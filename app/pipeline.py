"""Orchestrator: (level, topic) -> finished, upload-ready video package."""
from __future__ import annotations
import json, random
from pathlib import Path
from typing import Dict, Optional

from app.config_loader import Config
from app.utils import get_logger, slugify, timestamp, ensure_dir
from agents.script_generator import ScriptGenerator
from agents.segmenter import segment
from agents.timing import build_timing
from agents.background import BackgroundProvider
from agents.tts import TTS
from agents.metadata import build_metadata
from agents.uploader import TikTokUploader
from render.renderer import Renderer

log = get_logger()


class Pipeline:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.scriptgen = ScriptGenerator(cfg)
        self.bg = BackgroundProvider(cfg)
        self.tts = TTS(cfg)
        self.renderer = Renderer(cfg)
        self.uploader = TikTokUploader(cfg)

    # ------------------------------------------------------------------
    def choose_topic(self, account: Optional[Dict] = None, rng: Optional[random.Random] = None):
        rng = rng or random
        fams = self.cfg.topics.get("families", {})
        moods = self.cfg.topics.get("mood_queries", {})
        allowed = (account or {}).get("topic_families") or list(fams.keys())
        allowed = [f for f in allowed if f in fams] or list(fams.keys())
        family = rng.choice(allowed)
        topic = rng.choice(fams[family])
        queries = moods.get(family, [topic])
        return family, topic, queries

    # ------------------------------------------------------------------
    def generate_one(self, level: str, topic: Optional[str] = None,
                     account: Optional[Dict] = None, seed: Optional[int] = None,
                     with_audio: bool = True, auto_upload: bool = False,
                     title_override: str | None = None,
                     caption_override: str | None = None,
                     hashtags_override: str | None = None,
                     duration: Optional[int] = None,
                     text_color: Optional[str] = None,
                     tts_speed: Optional[float] = None) -> Dict:
        rng = random.Random(seed)
        level_spec = self.cfg.levels.get(level)
        if not level_spec:
            raise ValueError(f"unknown level '{level}' (have {list(self.cfg.levels)})")

        family, picked_topic, queries = self.choose_topic(account, rng)
        topic = topic or picked_topic
        log.info("=== generating %s | level=%s | topic=%s ===",
                 (account or {}).get("id", "adhoc"), level, topic)

        # 1) script (one coherent paragraph, level-appropriate words)
        script = self.scriptgen.generate(level, topic, seed=seed, family=family)
        # 2) clean whitespace but keep each sentence as one readable block;
        #    the renderer word-wraps each block to the safe width automatically.
        lines = segment(script["lines"], max_words=10_000)
        # 3) timing
        intro = self.cfg.get("intro_phrases", default=["Let's practice English", "Education is the key"])
        target = duration or self.cfg.get("video", "duration_sec", default=120)
        timing = build_timing(lines, level_spec.get("words_per_minute", 100), target)
        duration = float(min(max(timing["total"], target * 0.8), target * 1.2))

        # 4) background
        background = self.bg.get(queries, account=(account or {}).get("id", "default"))

        # 5) build output job folder
        meta = build_metadata(script, account,
                              title_override=title_override,
                              caption_override=caption_override,
                              hashtags_override=hashtags_override)
        job_dir = ensure_dir(self.cfg.abspath(self.cfg.get("paths", "jobs", default="outputs/jobs"))
                             / f"{timestamp()}_{meta['filename']}")

        # 6) audio (intro phrases, optional reading narration)
        audio_path = None
        if with_audio and self.cfg.get("audio", "intro_tts", default=True):
            wav = job_dir / "intro.wav"
            audio_path = self.tts.intro_track(intro, wav)
            audio_path = str(audio_path) if audio_path else None

        # 7) render
        strip_png = job_dir / "text_strip.png"
        scrim_png = job_dir / "scrim.png"
        _, _, strip_h = self.renderer.build_text_strip(intro, lines, strip_png, text_color=text_color)
        self.renderer.build_scrim(scrim_png)
        out_mp4 = job_dir / f"{meta['filename']}.mp4"
        self.renderer.compose(background, strip_png, strip_h, scrim_png,
                              duration, out_mp4, audio_path=audio_path)

        # 8) write sidecars
        (job_dir / "script.json").write_text(json.dumps(script, indent=2))
        (job_dir / "metadata.json").write_text(json.dumps(meta, indent=2))
        (job_dir / "caption.txt").write_text(
            str(meta.get("caption", "")) + "\n\n" + " ".join(meta.get("hashtags", [])))
        (job_dir / "timing.json").write_text(json.dumps(timing, indent=2))
        # full reading paragraph as plain text (easy to read / reuse)
        (job_dir / "paragraph.txt").write_text(script.get("paragraph") or "\n".join(lines))

        log.info("DONE -> %s", out_mp4)
        result = {"video": str(out_mp4), "job_dir": str(job_dir), "meta": meta,
                  "duration": duration, "background": background,
                  "script_source": script.get("source")}

        # 9) optional auto-upload to TikTok
        if auto_upload or self.cfg.get("upload", "enabled", default=False):
            try:
                up = self.uploader.upload(str(out_mp4),
                                          (job_dir / "caption.txt").read_text(),
                                          job_dir=str(job_dir))
                result["upload"] = up
                log.info("upload result: %s", up)
            except Exception as e:
                log.error("auto-upload failed: %s", e)
                result["upload"] = {"status": "failed", "error": str(e)}
        return result

    # ------------------------------------------------------------------
    def generate_batch(self, count: int, level: Optional[str] = None,
                       account: Optional[Dict] = None, with_audio: bool = True,
                       auto_upload: bool = False,
                       title_override: str | None = None,
                       caption_override: str | None = None,
                       hashtags_override: str | None = None,
                       duration: Optional[int] = None,
                       text_color: Optional[str] = None,
                       tts_speed: Optional[float] = None):
        results = []
        for i in range(count):
            lvl = level or (account or {}).get("level") or random.choice(list(self.cfg.levels))
            try:
                results.append(self.generate_one(
                    lvl,
                    account=account,
                    seed=None,
                    with_audio=with_audio,
                    auto_upload=auto_upload,
                    title_override=title_override,
                    caption_override=caption_override,
                    hashtags_override=hashtags_override,
                    duration=duration,
                    text_color=text_color,
                    tts_speed=tts_speed,
                ))
            except Exception as e:
                log.error("video %d/%d failed: %s", i + 1, count, e)
        return results
