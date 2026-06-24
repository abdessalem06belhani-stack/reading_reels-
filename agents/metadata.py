"""Agent: produce the upload-ready caption + hashtags + filename for a video."""
from __future__ import annotations
from typing import Dict
from app.utils import slugify

_BASE_TAGS = ["#learnenglish", "#englishreading", "#readingpractice",
              "#studyenglish", "#englishpractice", "#fyp"]
_LEVEL_TAGS = {"A1": "#beginnerenglish", "A2": "#elementaryenglish",
               "B1": "#intermediateenglish", "B2": "#upperintermediate",
               "C1": "#advancedenglish"}

def build_metadata(script: Dict, account: Dict | None = None,
                   title_override: str | None = None,
                   caption_override: str | None = None,
                   hashtags_override: str | None = None) -> Dict:
    level = script.get("level", "B1")
    title = script.get("title", "English Reading")
    if title_override:
        title = str(title_override).strip() or title

    caption = caption_override if caption_override is not None else script.get("caption")
    if caption is None:
        caption = f"{title} — read along with me. {script['lines'][0]}"
    caption = str(caption).strip()

    user_tags = []
    if hashtags_override:
        if isinstance(hashtags_override, str):
            user_tags = [t.strip() for t in hashtags_override.split(",") if t.strip()]
        elif isinstance(hashtags_override, list):
            user_tags = [str(t).strip() for t in hashtags_override if str(t).strip()]

    script_tags = script.get("hashtags") or []
    if isinstance(script_tags, str):
        script_tags = [script_tags]
    tags = list(dict.fromkeys(user_tags + script_tags + _BASE_TAGS + [_LEVEL_TAGS.get(level, "")]))
    tags = [t for t in tags if t]
    fname = f"{level.lower()}_{slugify(title)}"
    return {
        "title": title,
        "level": level,
        "caption": caption[:200],
        "hashtags": tags[:12],
        "filename": fname,
        "account_id": (account or {}).get("id"),
    }
