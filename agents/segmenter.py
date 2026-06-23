"""Agent: clean + enforce max-words-per-line so each line reads in one glance."""
from __future__ import annotations
import re
from typing import List

def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s

def split_long_line(line: str, max_words: int) -> List[str]:
    words = line.split()
    if len(words) <= max_words:
        return [line]
    out, cur = [], []
    for word_ in words:
        cur.append(word_)
        # break preferentially after punctuation
        if len(cur) >= max_words or word_.endswith((",", ";", ":")):
            out.append(" ".join(cur)); cur = []
    if cur:
        out.append(" ".join(cur))
    return out

def segment(lines: List[str], max_words: int) -> List[str]:
    result: List[str] = []
    for ln in lines:
        ln = _clean(ln)
        if not ln:
            continue
        result.extend(split_long_line(ln, max_words))
    return result
