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
    return Config(base, _y("levels.yaml"), _y("topics.yaml"), _y("accounts.yaml"))
