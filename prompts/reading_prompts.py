"""
Prompt templates for NVIDIA NIM (OpenAI-compatible chat completions).
The model is asked to return STRICT JSON so we can parse it deterministically.
"""
from __future__ import annotations
from typing import Dict
import json

JSON_SCHEMA = {
    "title": "short 2-4 word title",
    "hook": "the first reading line (must be easy and inviting)",
    "lines": ["reading line 1", "reading line 2", "...stacked sentences..."],
    "ending": "the final, satisfying / loop-friendly line",
    "caption": "a TikTok caption (<= 150 chars)",
    "hashtags": ["#learnenglish", "#englishreading"],
}

SYSTEM = (
    "You are an expert English-as-a-foreign-language curriculum writer who "
    "creates calm, high-retention reading-practice scripts for short vertical "
    "videos. You write clean, natural, grammatically correct English and you "
    "respect the requested CEFR level exactly.\n\n"
    "HOOK OBSESSION: The first line MUST grab attention instantly. It should\n"
    "feel personal, curious, or slightly surprising — never generic.\n\n"
    "MICRO-ARC: The script must build a tiny emotional journey: curiosity ->\n"
    "engagement -> satisfaction. Each line must make the viewer NEED the next.\n\n"
    "You ALWAYS reply with a single valid JSON object and nothing else."
)

def build_user_prompt(level_key: str, level_spec: Dict, topic: str) -> str:
    n = level_spec.get("target_lines", 18)
    hook = level_spec.get("hook", "a curious observation about the topic")
    ending = level_spec.get("ending", "a satisfying, warm reflection")
    return f"""Write ONE compelling {level_key} ({level_spec.get('name','')}) English reading script.

TOPIC: {topic}

STRUCTURE (1 connected paragraph, NOT random sentences):
- Lines 1-2: STRONG HOOK that makes the viewer stop scrolling.
  ({hook})
- Lines 3-{n-2}: Build the idea naturally — keep it flowing, keep it curious.
  Every line should feel like a tiny reveal or a step forward.
- Lines {n-1}-{n}: Warm, satisfying ending. ({ending})
  The last line must feel complete yet make the viewer want to re-watch.

LEVEL RULES (follow strictly):
- Vocabulary: {level_spec.get('vocabulary','')}
- Sentence style: {level_spec.get('sentence_style','')}
- Max words per line: {level_spec.get('max_words_per_line', 9)}
- Split into exactly {n} lines; each line is the next part of one flowing paragraph.

RETENTION PSYCHOLOGY:
- Line 1: A micro-curiosity gap. Example: "Why do some people change their lives in a single moment?" not "Reading is important."
- Every 3-4 lines: a mini-reward (a satisfying image, a gentle insight).
- Final line: A quiet, feel-good close that invites replay.
- Never lecture. Make the reader feel smart for reading.
- No emojis inside reading lines.

Return ONE JSON object with EXACTLY these keys:
{json.dumps(list(JSON_SCHEMA.keys()))}
Where "lines" is an array of exactly {n} strings forming ONE flowing paragraph.
"""
