"""
VoiceEngine — محرك صوت متطور متعدد المصادر.
Edge-TTS (أفضل جودة) → gTTS → pyttsx3 → silent fallback.
يدعم قراءة النص كاملاً (narrate_text) لزيادة مدة المشاهدة.
"""
from __future__ import annotations
import os, tempfile, asyncio
from pathlib import Path
from typing import List, Optional

from app.utils import get_logger, run_ffmpeg, ensure_dir

log = get_logger()


class VoiceEngine:
    """Multi-engine TTS with Edge-TTS priority."""

    def __init__(self, cfg):
        a = cfg.get("factory", "audio", default={}) or cfg.get("audio", default={})
        self.engine = a.get("tts_engine", "auto")
        self.lang = a.get("tts_lang", "en")
        self.tld = a.get("tts_tld", "com")
        self.loudnorm = a.get("loudnorm", True)
        self.edge_voice = a.get("edge_tts_voice", "en-US-JennyNeural")
        self.edge_rate = a.get("edge_tts_rate", "+0%")
        self.edge_pitch = a.get("edge_tts_pitch", "+0Hz")
        self.narrate_text = a.get("narrate_text", True)
        self.narrate_speed = a.get("narrate_speed", 0.95)

    def synth(self, text: str, out_wav: Path) -> Optional[Path]:
        """Generate speech for text, saving to out_wav. Returns path or None."""
        ensure_dir(out_wav.parent)
        tmp = Path(tempfile.mkdtemp())

        order = ["edge_tts", "gtts", "pyttsx3"]
        if self.engine == "gtts":
            order = ["gtts", "pyttsx3"]
        elif self.engine == "pyttsx3":
            order = ["pyttsx3"]
        elif self.engine == "silent":
            return None

        raw = None
        for eng in order:
            try:
                if eng == "edge_tts":
                    raw = self._edge_tts(text, tmp / "e.mp3")
                elif eng == "gtts":
                    raw = self._gtts(text, tmp / "g.mp3")
                elif eng == "pyttsx3":
                    raw = self._pyttsx3(text, tmp / "p.wav")
                if raw and Path(raw).exists() and Path(raw).stat().st_size > 0:
                    break
            except Exception as e:
                log.warning("%s failed: %s", eng, e)
                raw = None

        if raw is None:
            log.warning("All TTS engines failed -> silent")
            return None

        # Normalize to 48k stereo WAV
        af = "loudnorm=I=-16:TP=-1.5:LRA=11" if self.loudnorm else "anull"
        run_ffmpeg(["-i", str(raw), "-af", af, "-ar", "48000", "-ac", "2", str(out_wav)],
                   desc="voice normalize")
        return out_wav

    def _edge_tts(self, text: str, out_mp3: Path) -> Optional[Path]:
        """Use Edge-TTS (Microsoft) — best quality free TTS."""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                text,
                self.edge_voice,
                rate=self.edge_rate,
                pitch=self.edge_pitch,
            )
            asyncio.run(communicate.save(str(out_mp3)))
            if out_mp3.exists() and out_mp3.stat().st_size > 100:
                return out_mp3
        except ImportError:
            log.debug("edge_tts not installed, skipping")
        except Exception as e:
            log.warning("edge_tts error: %s", e)
        return None

    def _gtts(self, text: str, out_mp3: Path) -> Optional[Path]:
        """Use gTTS (Google) — good quality, needs internet."""
        try:
            from gtts import gTTS
            gTTS(text=text, lang=self.lang, tld=self.tld).save(str(out_mp3))
            if out_mp3.exists() and out_mp3.stat().st_size > 0:
                return out_mp3
        except Exception as e:
            log.warning("gTTS failed: %s", e)
        return None

    def _pyttsx3(self, text: str, out_wav: Path) -> Optional[Path]:
        """Use pyttsx3 (offline, robotic)."""
        try:
            import pyttsx3
            eng = pyttsx3.init()
            # Slow down speech for clarity
            rate = eng.getProperty("rate")
            eng.setProperty("rate", int(rate * self.narrate_speed))
            eng.save_to_file(text, str(out_wav))
            eng.runAndWait()
            if out_wav.exists() and out_wav.stat().st_size > 0:
                return out_wav
        except Exception as e:
            log.warning("pyttsx3 failed: %s", e)
        return None

    def build_voice_track(self, lines: List[str], out_wav: Path,
                          gap_sec: float = 0.3) -> Optional[Path]:
        """Generate voiceover for all lines, concatenated with gaps."""
        if not self.narrate_text:
            return None

        tmp = Path(tempfile.mkdtemp())
        parts = []

        for i, line in enumerate(lines):
            p = self.synth(line, tmp / f"line_{i:03d}.wav")
            if p:
                parts.append(p)

        if not parts:
            log.warning("No voice parts generated")
            return None

        if len(parts) == 1:
            run_ffmpeg(["-i", str(parts[0]), str(out_wav)], desc="voice copy")
            return out_wav

        # Concatenate with silence gaps
        sil = tmp / "sil.wav"
        run_ffmpeg(["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
                    "-t", str(gap_sec), str(sil)], desc="gap")

        inputs = []
        filt = []
        idx = 0
        for i, p in enumerate(parts):
            inputs += ["-i", str(p)]
            filt.append(f"[{idx}:a]")
            idx += 1
            if i < len(parts) - 1:
                inputs += ["-i", str(sil)]
                filt.append(f"[{idx}:a]")
                idx += 1

        n = idx
        run_ffmpeg([*inputs, "-filter_complex",
                     f"{''.join(filt)}concat=n={n}:v=0:a=1[a]",
                     "-map", "[a]", str(out_wav)], desc="voice concat")
        return out_wav

    def build_intro_track(self, phrases: List[str], out_wav: Path,
                          gap_sec: float = 0.5) -> Optional[Path]:
        """Speak intro phrases with gaps (same as original TTS.intro_track)."""
        tmp = Path(tempfile.mkdtemp())
        parts = []
        for i, ph in enumerate(phrases):
            p = self.synth(ph, tmp / f"intro_{i}.wav")
            if p:
                parts.append(p)
        if not parts:
            return None
        if len(parts) == 1:
            run_ffmpeg(["-i", str(parts[0]), str(out_wav)], desc="intro copy")
            return out_wav

        sil = tmp / "sil.wav"
        run_ffmpeg(["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
                    "-t", str(gap_sec), str(sil)], desc="gap")
        inputs = []
        filt = []
        idx = 0
        for i, p in enumerate(parts):
            inputs += ["-i", str(p)]
            filt.append(f"[{idx}:a]")
            idx += 1
            if i < len(parts) - 1:
                inputs += ["-i", str(sil)]
                filt.append(f"[{idx}:a]")
                idx += 1
        n = idx
        run_ffmpeg([*inputs, "-filter_complex",
                     f"{''.join(filt)}concat=n={n}:v=0:a=1[a]",
                     "-map", "[a]", str(out_wav)], desc="intro concat")
        return out_wav
