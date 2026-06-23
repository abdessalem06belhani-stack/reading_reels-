"""
Agent: free text-to-speech for the intro phrases (and optionally the reading).

Engine priority (configurable):
  gtts    -> online, natural voices, free (needs internet)
  pyttsx3 -> offline, robotic but zero-network
  none    -> produce silence (video still renders)

All outputs are converted to a normalized WAV via ffmpeg so the renderer can
concatenate / mix them deterministically.
"""
from __future__ import annotations
import os, tempfile
from pathlib import Path
from typing import List, Optional
from app.utils import get_logger, run_ffmpeg, ensure_dir

log = get_logger()

class TTS:
    def __init__(self, cfg):
        a = cfg.get("audio", default={})
        self.engine = a.get("tts_engine", "auto")
        self.lang = a.get("tts_lang", "en")
        self.tld = a.get("tts_tld", "com")
        self.loudnorm = a.get("loudnorm", True)

    def _gtts(self, text: str, out_mp3: Path) -> bool:
        try:
            from gtts import gTTS
            gTTS(text=text, lang=self.lang, tld=self.tld).save(str(out_mp3))
            return out_mp3.exists() and out_mp3.stat().st_size > 0
        except Exception as e:
            log.warning("gTTS failed: %s", e)
            return False

    def _pyttsx3(self, text: str, out_wav: Path) -> bool:
        try:
            import pyttsx3
            eng = pyttsx3.init()
            eng.save_to_file(text, str(out_wav))
            eng.runAndWait()
            return out_wav.exists() and out_wav.stat().st_size > 0
        except Exception as e:
            log.warning("pyttsx3 failed: %s", e)
            return False

    def synth(self, text: str, out_wav: Path) -> Optional[Path]:
        """Return a normalized wav path, or None if all engines fail."""
        ensure_dir(out_wav.parent)
        tmp = Path(tempfile.mkdtemp())
        raw = None
        order = (["gtts", "pyttsx3"] if self.engine in ("auto",)
                 else [self.engine])
        for eng in order:
            if eng == "gtts":
                cand = tmp / "g.mp3"
                if self._gtts(text, cand):
                    raw = cand; break
            elif eng == "pyttsx3":
                cand = tmp / "p.wav"
                if self._pyttsx3(text, cand):
                    raw = cand; break
        if raw is None:
            log.warning("no TTS engine available -> silent")
            return None
        # normalize to 48k stereo wav
        af = "loudnorm=I=-16:TP=-1.5:LRA=11" if self.loudnorm else "anull"
        run_ffmpeg(["-i", str(raw), "-af", af, "-ar", "48000", "-ac", "2", str(out_wav)],
                   desc="tts normalize")
        return out_wav

    def intro_track(self, phrases: List[str], out_wav: Path, gap_sec: float = 0.5) -> Optional[Path]:
        """Speak each intro phrase with a small gap, concatenated into one wav."""
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
        # concat with silence gap
        sil = tmp / "sil.wav"
        run_ffmpeg(["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", str(gap_sec), str(sil)],
                   desc="gap")
        inputs = []
        filt = []
        idx = 0
        for i, p in enumerate(parts):
            inputs += ["-i", str(p)]; filt.append(f"[{idx}:a]"); idx += 1
            if i < len(parts) - 1:
                inputs += ["-i", str(sil)]; filt.append(f"[{idx}:a]"); idx += 1
        n = idx
        run_ffmpeg([*inputs, "-filter_complex", f"{''.join(filt)}concat=n={n}:v=0:a=1[a]",
                    "-map", "[a]", str(out_wav)], desc="intro concat")
        return out_wav
