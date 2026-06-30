"""
TikTokFactory — المنسق الرئيسي لمصنع فيديوهات التيك توك الآلي.

يدير دورة حياة الفيديو الكاملة:
  1. اختيار النيش + السكريبت
  2. توليد الصوت (AI voiceover)
  3. جلب الخلفية البصرية
  4. تركيب الفيديو النهائي HD
  5. حفظ metadata + caption + hashtags
  6. إشعار عبر Telegram (اختياري)
"""
from __future__ import annotations
import json, os, random
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from app.utils import get_logger, timestamp, ensure_dir, slugify

from tiktok_factory.niche_scripts import NicheScriptGenerator
from tiktok_factory.voice_engine import VoiceEngine
from tiktok_factory.visual_engine import VisualEngine
from tiktok_factory.video_composer import VideoComposer

log = get_logger()

# النيشات المدعومة
SUPPORTED_NICHES = [
    "finance", "ai_tools", "real_estate",
    "health_biohacking", "productivity",
]


class TikTokFactory:
    """مصنع الفيديوهات الرئيسي — TikTok AI Factory."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.niche_gen = NicheScriptGenerator(cfg)
        self.voice = VoiceEngine(cfg)
        self.visual = VisualEngine(cfg)
        self.composer = VideoComposer(cfg)

        # Factory config
        fc = cfg.get("factory", default={})
        self.output_dir = ensure_dir(
            cfg.abspath(fc.get("output_dir", "outputs/factory"))
        )
        self.default_niche = fc.get("default_niche", "finance")
        self.intro_phrases = cfg.get("intro_phrases",
                                     default=["Let's practice English",
                                              "Education is the key"])

    def generate(self, niche_key: Optional[str] = None,
                 seed: Optional[int] = None,
                 with_audio: bool = True,
                 prefer_video_bg: bool = True) -> Dict:
        """Generate one complete TikTok video for the given niche."""
        niche = niche_key or self.default_niche
        rng = random.Random(seed)

        if niche not in SUPPORTED_NICHES:
            raise ValueError(f"Unsupported niche '{niche}'. "
                             f"Supported: {SUPPORTED_NICHES}")

        log.info("═══ TikTok Factory | niche=%s | seed=%s ═══", niche, seed)

        # 1. Generate script
        script = self.niche_gen.generate(niche, seed=seed)
        lines = script.get("lines", [])

        # 2. Build output directory
        meta = self._build_metadata(script, niche)
        job_dir = ensure_dir(
            self.output_dir / f"{timestamp()}_{meta['filename']}"
        )

        # 3. Audio (narrated text + optional intro)
        audio_path = None
        if with_audio:
            audio_path = self._build_audio(lines, script, job_dir)

        # 4. Background visuals
        background = self.visual.get_background(niche, prefer_video=prefer_video_bg)

        # 5. Render video
        out_mp4 = job_dir / f"{meta['filename']}.mp4"
        self.composer.render(
            niche, script, background, audio_path, out_mp4,
            duration_sec=self._get_target_duration(),
        )

        # 6. Write sidecar files
        self._write_sidecars(job_dir, script, meta, background)

        # 7. Speech intro phrases if enabled
        if with_audio and not audio_path:
            intro_path = self.voice.build_intro_track(
                self.intro_phrases, job_dir / "intro.wav"
            )

        log.info("DONE -> %s [%s]", out_mp4, niche)
        return {
            "video": str(out_mp4),
            "job_dir": str(job_dir),
            "niche": niche,
            "niche_name": meta.get("niche_name", niche),
            "meta": meta,
            "script_source": script.get("source", "fallback"),
            "duration": self._get_target_duration(),
            "background_type": background.get("type", "image"),
        }

    def generate_batch(self, count: int = 3,
                       niche: Optional[str] = None,
                       with_audio: bool = True,
                       prefer_video_bg: bool = True) -> List[Dict]:
        """Generate multiple videos (may mix niches if none specified)."""
        results = []
        niches_to_use = [niche] if niche else SUPPORTED_NICHES

        for i in range(count):
            chosen = random.choice(niches_to_use)
            try:
                res = self.generate(
                    niche_key=chosen,
                    seed=None,
                    with_audio=with_audio,
                    prefer_video_bg=prefer_video_bg,
                )
                results.append(res)
                log.info("Factory batch: [%d/%d] %s -> %s",
                         i + 1, count, chosen, res["video"])
            except Exception as e:
                log.error("Factory batch [%d/%d] failed: %s", i + 1, count, e)

        return results

    def generate_niche_batch(self, niche: str, count: int = 3,
                             with_audio: bool = True,
                             prefer_video_bg: bool = True) -> List[Dict]:
        """Generate multiple videos for ONE specific niche."""
        return self.generate_batch(
            count=count, niche=niche, with_audio=with_audio,
            prefer_video_bg=prefer_video_bg
        )

    # ── Internal ────────────────────────────────────────────────

    def _build_audio(self, lines: List[str], script: Dict,
                     job_dir: Path) -> Optional[str]:
        """Build full voice track."""
        audio_path = job_dir / "voiceover.wav"

        # Narrate all reading lines (main voice)
        voice_path = self.voice.build_voice_track(
            lines, job_dir / "narration.wav", gap_sec=0.3
        )

        # Add intro phrases before narration
        intro_path = self.voice.build_intro_track(
            self.intro_phrases, job_dir / "intro.wav", gap_sec=0.5
        )

        # Try to concat intro + narration
        if intro_path and voice_path:
            import tempfile
            tmp = Path(tempfile.mkdtemp())
            sil = tmp / "sil.wav"
            from app.utils import run_ffmpeg, ffmpeg_bin
            run_ffmpeg(
                ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                 "-t", "0.3", str(sil)], desc="silence"
            )
            run_ffmpeg(
                ["-i", str(intro_path), "-i", str(sil),
                 "-i", str(voice_path),
                 "-filter_complex",
                 "[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]",
                 "-map", "[a]", str(audio_path)],
                desc="voice full track"
            )
            return str(audio_path)
        elif voice_path:
            from app.utils import run_ffmpeg
            run_ffmpeg(
                ["-i", str(voice_path), str(audio_path)],
                desc="voice copy"
            )
            return str(audio_path)
        elif intro_path:
            return str(intro_path)

        return None

    def _build_metadata(self, script: Dict, niche: str) -> Dict:
        """Build upload-ready metadata."""
        title = script.get("title", f"TikTok {niche} Tips")
        caption = script.get("caption", "")
        niche_hashtags = script.get("hashtags", [])
        base_tags = ["#tiktok", "#fyp", "#viral", "#edutok"]
        level_tags = {
            "finance": "#moneytips",
            "ai_tools": "#aitips",
            "real_estate": "#realestate",
            "health_biohacking": "#healthtips",
            "productivity": "#productivity",
        }

        tags = list(dict.fromkeys(
            niche_hashtags + base_tags + [level_tags.get(niche, "")]
        ))
        tags = [t for t in tags if t]

        fname = f"{niche}_{slugify(title)}"
        niche_info = self.niche_gen.get_niche_names()

        return {
            "title": title,
            "niche": niche,
            "niche_name": niche_info.get(niche, niche),
            "caption": (caption or title)[:200],
            "hashtags": tags[:15],
            "filename": fname,
            "generated_at": timestamp(),
            "source": script.get("source", "unknown"),
        }

    def _get_target_duration(self) -> float:
        """Get target video duration from config."""
        v = self.cfg.get("factory", "video", default={}) or {}
        return float(v.get("target_duration_sec", 120))

    def _write_sidecars(self, job_dir: Path, script: Dict,
                        meta: Dict, background: Dict):
        """Write metadata files alongside the video."""
        (job_dir / "script.json").write_text(
            json.dumps(script, indent=2, ensure_ascii=False)
        )
        (job_dir / "metadata.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False)
        )
        (job_dir / "caption.txt").write_text(
            str(meta.get("caption", "")) + "\n\n" + " ".join(meta.get("hashtags", []))
        )
        (job_dir / "background.json").write_text(
            json.dumps(background, indent=2)
        )
        (job_dir / "paragraph.txt").write_text(
            script.get("paragraph") or "\n".join(script.get("lines", []))
        )

    def niche_report(self) -> str:
        """Generate a report of all available niches with stats."""
        lines = ["📊 **TikTok AI Factory — Niche Report**\n"]
        for niche in SUPPORTED_NICHES:
            try:
                s = self.niche_gen.generate(niche, seed=42)
                lines.append(f"• **{niche}**: {s.get('title', 'N/A')} "
                             f"({s.get('source', 'local')}) "
                             f"— {len(s.get('lines', []))} lines")
            except Exception as e:
                lines.append(f"• **{niche}**: ERROR - {e}")
        lines.append(f"\n✅ {len(SUPPORTED_NICHES)} niches configured")
        return "\n".join(lines)
