"""
Send generated videos to Telegram via Bot API.
Auto-compresses videos exceeding 48MB to stay under Telegram's 50MB limit.

Usage:
  python -m telegram_sender --file path/to/video.mp4 --caption "text"
  python -m telegram_sender --dir path/to/job_folder
"""
from __future__ import annotations
import json, os, sys, argparse, subprocess
from pathlib import Path
from typing import Optional
import requests

from app.utils import get_logger, ffmpeg_bin

log = get_logger()

BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
TELEGRAM_LIMIT = 48 * 1024 * 1024  # 48MB (give headroom from 50MB limit)


def _compress(file_path: str) -> str:
    """Re-encode video to 720p CRF 28 to fit under Telegram's 50MB limit."""
    inp = Path(file_path)
    out = inp.with_suffix(".compressed.mp4")
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error",
           "-i", file_path,
           "-c:v", "libx264", "-preset", "fast", "-crf", "28",
           "-vf", "scale=-2:720",
           "-c:a", "aac", "-b:a", "64k",
           "-movflags", "+faststart",
           str(out)]
    log.info("compressing video (target < 48MB) ...")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not out.exists():
        log.warning("compression failed (exit %s), sending original", proc.returncode)
        if out.exists():
            out.unlink()
        return file_path
    log.info("compressed %s (%.1fMB -> %.1fMB)", file_path,
             os.path.getsize(file_path) / 1e6, os.path.getsize(str(out)) / 1e6)
    return str(out)


def send_video(file_path: str, caption: str = "",
               bot_token: Optional[str] = None,
               chat_id: Optional[str] = None) -> bool:
    bot_token = bot_token or os.getenv(BOT_TOKEN_ENV, "").strip()
    chat_id = chat_id or os.getenv(CHAT_ID_ENV, "").strip()
    if not bot_token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return False

    # Auto-compress if too large for Telegram
    size = os.path.getsize(file_path)
    path = _compress(file_path) if size > TELEGRAM_LIMIT else file_path

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    cap = caption[:1024] if caption else ""
    with open(path, "rb") as f:
        r = requests.post(url, data={"chat_id": chat_id, "caption": cap},
                          files={"video": f}, timeout=300)
    # Clean up temp compressed file
    if path != file_path and os.path.exists(path):
        os.unlink(path)
    if r.ok:
        log.info("sent %s to Telegram", file_path)
        return True
    log.error("Telegram send failed: %s", r.text[-500:])
    return False


def send_job_dir(job_dir: str):
    p = Path(job_dir)
    mp4s = list(p.glob("*.mp4"))
    caption_txt = p / "caption.txt"
    caption = caption_txt.read_text(encoding="utf-8")[:1024] if caption_txt.exists() else ""
    meta_json = p / "metadata.json"
    meta = json.loads(meta_json.read_text()) if meta_json.exists() else {}
    title = meta.get("title", "Reading video")
    level = meta.get("level", "B1")
    cap = f"{title} | Level: {level}\n\n{caption}"
    for mp4 in mp4s:
        send_video(str(mp4), caption=cap)


def cmd_send(args):
    if args.dir:
        send_job_dir(args.dir)
    elif args.file:
        send_video(args.file, args.caption or "")

if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="telegram_sender")
    p.add_argument("--file", help="path to mp4")
    p.add_argument("--dir", help="path to job directory")
    p.add_argument("--caption", default="")
    p.add_argument("--bot-token", default=None)
    p.add_argument("--chat-id", default=None)
    args = p.parse_args()
    cmd_send(args)
