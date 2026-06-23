"""
Agent: turn (level, topic) -> structured reading script.

Primary path : NVIDIA NIM (free hosted endpoints, OpenAI-compatible REST).
Fallback path: offline local content engine (content/fallback_bank.py).
"""
from __future__ import annotations
import json, os, re, time
from typing import Dict, Optional
import requests

from prompts.reading_prompts import SYSTEM, build_user_prompt
from content import fallback_bank
from app.utils import get_logger

log = get_logger()

def _extract_json(text: str) -> Optional[dict]:
    """Pull the first valid JSON object out of a model response."""
    text = text.strip()
    # strip ```json fences if present
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    # find the outermost {...}
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    chunk = text[start:end + 1]
    try:
        return json.loads(chunk)
    except Exception:
        return None


class ScriptGenerator:
    def __init__(self, cfg):
        self.cfg = cfg
        ai = cfg.get("ai", default={})
        self.provider = ai.get("provider", "nvidia_nim")
        self.base_url = ai.get("base_url", "https://integrate.api.nvidia.com/v1")
        self.model = ai.get("model", "meta/llama-3.1-70b-instruct")
        self.temperature = ai.get("temperature", 0.8)
        self.max_tokens = ai.get("max_tokens", 1200)
        self.timeout = ai.get("timeout_sec", 60)
        self.retries = ai.get("retries", 2)
        self.fallback = ai.get("fallback_to_local", True)
        self.api_key = os.getenv("NVIDIA_API_KEY", "").strip()

    # ------------------------------------------------------------------
    def generate(self, level_key: str, topic: str, seed: Optional[int] = None,
                 family: Optional[str] = None) -> Dict:
        level_spec = self.cfg.levels.get(level_key, {})
        use_nim = self.provider == "nvidia_nim" and bool(self.api_key)
        if use_nim:
            try:
                data = self._call_nim(level_key, level_spec, topic)
                data = self._normalize(data, level_key, topic, level_spec)
                data["source"] = "nvidia_nim"
                log.info("script via NVIDIA NIM (%s) | %d lines", self.model, len(data["lines"]))
                return data
            except Exception as e:
                log.warning("NIM failed (%s). Falling back to local engine.", e)
                if not self.fallback:
                    raise
        else:
            if self.provider == "nvidia_nim":
                log.warning("No NVIDIA_API_KEY set -> using offline local content engine.")
        data = fallback_bank.generate(level_key, level_spec, topic,
                                       n_lines=level_spec.get("target_lines", 18),
                                       seed=seed, family=family)
        return self._normalize(data, level_key, topic, level_spec)

    # ------------------------------------------------------------------
    def _call_nim(self, level_key, level_spec, topic) -> dict:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": build_user_prompt(level_key, level_spec, topic)},
            ],
        }
        last_err = None
        for attempt in range(1, self.retries + 2):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
                if r.status_code == 429:
                    raise RuntimeError("rate limited (429)")
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                data = _extract_json(content)
                if not data or "lines" not in data:
                    raise ValueError("model did not return valid JSON with 'lines'")
                return data
            except Exception as e:
                last_err = e
                if attempt <= self.retries:
                    time.sleep(1.5 * attempt)
        raise RuntimeError(f"NIM call failed after retries: {last_err}")

    # ------------------------------------------------------------------
    def _normalize(self, data: dict, level_key, topic, level_spec) -> dict:
        lines = [str(x).strip() for x in data.get("lines", []) if str(x).strip()]
        if not lines:
            raise ValueError("empty script")
        data["lines"] = lines
        data.setdefault("title", topic.capitalize() if isinstance(topic, str) else level_key)
        data.setdefault("hook", lines[0])
        data.setdefault("ending", lines[-1])
        data["level"] = level_key
        data["topic"] = topic
        data.setdefault("paragraph", " ".join(lines))
        return data
