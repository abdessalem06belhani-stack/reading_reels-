"""Agent: produce the upload-ready caption + hashtags + filename for a video."""
from __future__ import annotations
from typing import Dict
from app.utils import slugify

_BASE_TAGS = ["#learnenglish", "#englishreading", "#readingpractice",
              "#studyenglish", "#englishpractice", "#fyp"]
_LEVEL_TAGS = {"A1": "#beginnerenglish", "A2": "#elementaryenglish",
               "B1": "#intermediateenglish", "B2": "#upperintermediate",
               "C1": "#advancedenglish"}

def build_metadata(script: Dict, account: Dict | None = None) -> Dict:
    level = script.get("level", "B1")
    title = script.get("title", "English Reading")
    caption = script.get("caption") or f"{title} — read along with me. {script['lines'][0]}"
    tags = list(dict.fromkeys((script.get("hashtags") or []) + _BASE_TAGS + [_LEVEL_TAGS.get(level, "")]))
    tags = [t for t in tags if t]
    fname = f"{level.lower()}_{slugify(title)}"
    return {
        "title": title,
        "level": level,
        "caption": caption.strip()[:200],
        "hashtags": tags[:12],
        "filename": fname,
        "account_id": (account or {}).get("id"),
    }
