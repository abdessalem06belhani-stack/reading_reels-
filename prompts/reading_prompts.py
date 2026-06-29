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
    "respect the requested CEFR level exactly. You ALWAYS reply with a single "
    "valid JSON object and nothing else."
)

def build_user_prompt(level_key: str, level_spec: Dict, topic: str) -> str:
    n = level_spec.get("target_lines", 18)
    return f"""Write ONE coherent {level_key} ({level_spec.get('name','')}) English reading paragraph.

TOPIC: {topic}

It must read as a SINGLE connected paragraph (one short story or reflection on the
topic), NOT a list of unrelated sentences. Keep the same subject and storyline from the
first line to the last so the reader follows one continuous idea.

LEVEL RULES (follow strictly):
- Vocabulary: {level_spec.get('vocabulary','')}
- Sentence style: {level_spec.get('sentence_style','')}
- Max words per line: {level_spec.get('max_words_per_line', 9)}
- Split the paragraph into exactly {n} short reading lines (each line is the next part
  of the SAME paragraph; one clear idea per line).
- Hook idea: {level_spec.get('hook','')}
- Ending idea: {level_spec.get('ending','')}

RETENTION RULES:
- Line 1-2 must be the easiest, to pull the viewer in.
- Build a gentle micro-arc so the viewer wants to reach the last line.
- The final line must feel complete yet quietly invite a re-watch.
- Do NOT include the intro phrases; those are added separately.
- No emojis inside the reading lines.

Return ONE JSON object with EXACTLY these keys:
{json.dumps(list(JSON_SCHEMA.keys()))}
Where "lines" is an array of exactly {n} strings that together form ONE flowing paragraph.
"""
