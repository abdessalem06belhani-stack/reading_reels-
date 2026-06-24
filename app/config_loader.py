"""Load YAML config + .env into a single Config object."""
from __future__ import annotations
import os, yaml
from pathlib import Path
from typing import Any, Dict

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[1]   # project root (reading_reels/)

class Config:
    def __init__(self, base: Dict[str, Any], levels: Dict, topics: Dict, accounts: Dict):
        self.base = base
        self.levels = levels
        self.topics = topics
        self.accounts = accounts
        self.root = ROOT

    # convenience getters -------------------------------------------------
    def get(self, *keys, default=None):
        node = self.base
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    def abspath(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (self.root / p)

    @property
    def env(self) -> Dict[str, str]:
        return dict(os.environ)


def load_config(config_dir: str | None = None) -> Config:
    if load_dotenv:
        load_dotenv(ROOT / ".env")
    cdir = Path(config_dir) if config_dir else (ROOT / "config")
    def _y(name):
        f = cdir / name
        return yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else {}
    base = _y("config.yaml")
    # env overrides
    if os.getenv("NIM_MODEL"):
        base.setdefault("ai", {})["model"] = os.environ["NIM_MODEL"]
    
    # GitHub Actions workflow input overrides (GH_* variables)
    _apply_github_overrides(base)
    
    return Config(base, _y("levels.yaml"), _y("topics.yaml"), _y("accounts.yaml"))


def _apply_github_overrides(config: Dict[str, Any]) -> None:
    """Apply GitHub Actions workflow input overrides from GH_* environment variables."""
    
    # Video/rendering overrides
    if duration := os.getenv("GH_DURATION"):
        config.setdefault("video", {})["duration_target"] = int(duration)
    
    if text_font := os.getenv("GH_TEXT_FONT"):
        config.setdefault("text", {})["font"] = text_font
    if text_size_intro := os.getenv("GH_TEXT_SIZE_INTRO"):
        config.setdefault("text", {})["size_intro"] = int(text_size_intro)
    if text_size_body := os.getenv("GH_TEXT_SIZE_BODY"):
        config.setdefault("text", {})["size_body"] = int(text_size_body)
    if text_color := os.getenv("GH_TEXT_COLOR"):
        config.setdefault("text", {})["color"] = text_color
    if text_stroke_width := os.getenv("GH_TEXT_STROKE_WIDTH"):
        config.setdefault("text", {})["stroke_width"] = int(text_stroke_width)
    if text_scroll_speed := os.getenv("GH_TEXT_SCROLL_SPEED"):
        config.setdefault("text", {})["scroll_speed"] = float(text_scroll_speed)
    
    # Background overrides
    if bg_source := os.getenv("GH_BACKGROUND_SOURCE"):
        if bg_source != "auto":
            config.setdefault("background", {})["source_priority"] = [bg_source]
    if mood_override := os.getenv("GH_MOOD_OVERRIDE"):
        # Store mood override for background agent to use
        config.setdefault("_overrides", {})["mood_query"] = mood_override
    if use_slideshow := os.getenv("GH_USE_SLIDESHOW"):
        config.setdefault("_overrides", {})["use_slideshow"] = use_slideshow.lower() == "true"
    
    # Audio/TTS overrides
    if enable_narration := os.getenv("GH_ENABLE_NARRATION"):
        config.setdefault("audio", {})["enable_narration"] = enable_narration.lower() == "true"
    if tts_speed := os.getenv("GH_TTS_SPEED"):
        config.setdefault("audio", {})["tts_speed"] = float(tts_speed)
    if bg_music := os.getenv("GH_BACKGROUND_MUSIC"):
        config.setdefault("audio", {})["background_music_enabled"] = bg_music.lower() == "true"
    if music_gain := os.getenv("GH_MUSIC_GAIN"):
        config.setdefault("audio", {})["music_gain_db"] = float(music_gain)
    
    # Metadata overrides
    if title_override := os.getenv("GH_TITLE_OVERRIDE"):
        config.setdefault("_overrides", {})["title"] = title_override
    if caption_override := os.getenv("GH_CAPTION_OVERRIDE"):
        config.setdefault("_overrides", {})["caption"] = caption_override
    if hashtags_override := os.getenv("GH_HASHTAGS_OVERRIDE"):
        config.setdefault("_overrides", {})["hashtags"] = hashtags_override
