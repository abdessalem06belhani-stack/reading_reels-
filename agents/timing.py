"""Agent: build a timing map so the passage fills ~target duration and the
scroll speed is calm and readable. Returns per-line (start,end) + total."""
from __future__ import annotations
from typing import List, Dict

def build_timing(lines: List[str], words_per_minute: int, target_sec: int,
                 lead_in: float = 2.5, lead_out: float = 3.0,
                 min_line_sec: float = 1.6) -> Dict:
    wps = max(0.8, words_per_minute / 60.0)
    durations = []
    for ln in lines:
        n = max(1, len(ln.split()))
        durations.append(max(min_line_sec, n / wps))
    reading = sum(durations)
    # scale BOTH ways toward the target, but stay within readable bounds:
    #   never faster than 0.65x (too rushed) or slower than 1.7x (too sleepy)
    desired = max(1.0, target_sec - lead_in - lead_out)
    scale = desired / max(0.1, reading)
    scale = max(0.65, min(scale, 1.7))
    durations = [d * scale for d in durations]
    t = lead_in
    spans = []
    for ln, d in zip(lines, durations):
        spans.append({"text": ln, "start": round(t, 2), "end": round(t + d, 2)})
        t += d
    total = round(t + lead_out, 2)
    return {"spans": spans, "total": total, "lead_in": lead_in, "lead_out": lead_out}
