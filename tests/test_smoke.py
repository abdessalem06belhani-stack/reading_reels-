"""Smoke tests that need no API keys and no rendering."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config_loader import load_config
from agents.segmenter import segment
from agents.timing import build_timing
from content import fallback_bank


def test_config_loads():
    cfg = load_config()
    assert "video" in cfg.base
    assert set(cfg.levels) >= {"A1", "A2", "B1", "B2", "C1"}


def test_offline_content_engine():
    cfg = load_config()
    spec = cfg.levels["B1"]
    data = fallback_bank.generate("B1", spec, "a quiet morning routine",
                                  n_lines=spec["target_lines"], seed=1)
    assert data["lines"] and isinstance(data["lines"], list)
    assert data["hook"] and data["ending"]


def test_segment_and_timing():
    lines = ["This is a test sentence that is fairly long and should wrap nicely."]
    segs = segment(lines, max_words=10000)
    t = build_timing(segs, words_per_minute=100, target_sec=120)
    assert t["total"] > 0 and t["spans"]


if __name__ == "__main__":
    test_config_loads(); test_offline_content_engine(); test_segment_and_timing()
    print("smoke tests passed")
