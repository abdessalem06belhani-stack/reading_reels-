"""Shared helpers: logging, ffmpeg discovery, filesystem, dedup db."""
from __future__ import annotations
import json, logging, os, re, shutil, subprocess, sys
from pathlib import Path
from datetime import datetime

def get_logger(name="reading_reels"):
    log = logging.getLogger(name)
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
    return log

log = get_logger()

def ffmpeg_bin() -> str:
    """Return a usable ffmpeg path. Prefers system ffmpeg, falls back to the
    static binary shipped with imageio-ffmpeg (no system install needed)."""
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        return sys_ff
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:
        raise RuntimeError(
            "ffmpeg not found. Install it (apt-get install ffmpeg / brew install ffmpeg) "
            "or `pip install imageio-ffmpeg`."
        ) from e

def run_ffmpeg(args: list[str], desc: str = "ffmpeg"):
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", *args]
    log.info("%s ...", desc)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        log.error("ffmpeg failed:\n%s", proc.stderr[-4000:])
        raise RuntimeError(f"{desc} failed (exit {proc.returncode})")
    return proc

def slugify(text: str, maxlen: int = 48) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (s[:maxlen] or "video").strip("-")

def timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")

def ensure_dir(p) -> Path:
    p = Path(p); p.mkdir(parents=True, exist_ok=True); return p

# ---- dedup db for backgrounds --------------------------------------------
def load_used(db_path: Path) -> dict:
    if Path(db_path).exists():
        try:
            return json.loads(Path(db_path).read_text())
        except Exception:
            return {}
    return {}

def save_used(db_path: Path, data: dict):
    ensure_dir(Path(db_path).parent)
    Path(db_path).write_text(json.dumps(data, indent=2))
