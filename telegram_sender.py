"""
Send generated videos to Telegram via Bot API.

Usage:
  python -m telegram_sender --file path/to/video.mp4 --caption "text"
  python -m telegram_sender --dir path/to/job_folder
"""
from __future__ import annotations
import json, os, sys, argparse
from pathlib import Path
from typing import Optional
import requests

from app.utils import get_logger

log = get_logger()

BOT_TOKEN_ENV = "8759505095:AAH7d1BSTITsc5uqFH9cNZHWY-G_RxnRqzA"
CHAT_ID_ENV = "-1002141621308"


def send_video(file_path: str, caption: str = "",
               bot_token: Optional[str] = None,
               chat_id: Optional[str] = None) -> bool:
    bot_token = bot_token or os.getenv(BOT_TOKEN_ENV, "").strip()
    chat_id = chat_id or os.getenv(CHAT_ID_ENV, "").strip()
    if not bot_token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    cap = caption[:1024] if caption else ""
    with open(file_path, "rb") as f:
        r = requests.post(url, data={"chat_id": chat_id, "caption": cap},
                          files={"video": f}, timeout=300)
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
