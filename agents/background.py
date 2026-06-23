"""
Agent: fetch a fresh, mood-matched background per video.

Priority (configurable): pexels -> pixabay -> gradient (always-available offline).
Dedup: never reuse the same asset id for the same account.
Returns {"type": "image"|"video", "path": <local path>}.
"""
from __future__ import annotations
import os, random, hashlib
from pathlib import Path
from typing import Dict, List, Optional
import requests
import numpy as np
from PIL import Image, ImageFilter

from app.utils import get_logger, load_used, save_used, ensure_dir

log = get_logger()

# Calming palettes for the offline gradient fallback (top_rgb, bottom_rgb)
_PALETTES = [
    ((24, 33, 58), (86, 67, 110)),     # indigo dusk
    ((17, 46, 64), (16, 88, 96)),      # teal deep
    ((46, 26, 71), (120, 58, 95)),     # plum
    ((26, 42, 38), (74, 103, 73)),     # forest
    ((38, 24, 24), (110, 72, 58)),     # warm earth
    ((20, 30, 48), (52, 86, 139)),     # ocean blue
    ((40, 22, 44), (96, 52, 88)),      # berry
]

class BackgroundProvider:
    def __init__(self, cfg):
        self.cfg = cfg
        self.bg = cfg.get("background", default={})
        self.cache = ensure_dir(cfg.abspath(self.bg.get("cache_dir", "assets/cache")))
        self.db_path = cfg.abspath(cfg.get("paths", "used_assets_db", default="assets/used_assets.json"))
        self.used = load_used(self.db_path)
        self.W = cfg.get("video", "width", default=1080)
        self.H = cfg.get("video", "height", default=1920)
        self.pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
        self.pixabay_key = os.getenv("PIXABAY_API_KEY", "").strip()

    # ------------------------------------------------------------------
    def _seen(self, account: str, src: str, asset_id) -> bool:
        key = f"{src}:{asset_id}"
        return key in self.used.get(account, [])

    def _mark(self, account: str, src: str, asset_id):
        self.used.setdefault(account, []).append(f"{src}:{asset_id}")
        save_used(self.db_path, self.used)

    def _download(self, url: str, suffix: str) -> Path:
        h = hashlib.md5(url.encode()).hexdigest()[:16]
        out = self.cache / f"{h}{suffix}"
        if out.exists():
            return out
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return out

    # ------------------------------------------------------------------
    def get(self, queries: List[str], account: str = "default") -> Dict:
        order = self.bg.get("source_priority", ["pexels", "pixabay", "gradient"])
        for src in order:
            try:
                if src == "pexels" and self.pexels_key:
                    res = self._from_pexels(queries, account)
                    if res: return res
                elif src == "pixabay" and self.pixabay_key:
                    res = self._from_pixabay(queries, account)
                    if res: return res
                elif src == "gradient":
                    return self._gradient(account)
            except Exception as e:
                log.warning("background source %s failed: %s", src, e)
        return self._gradient(account)

    # ---- Pexels -------------------------------------------------------
    def _from_pexels(self, queries, account) -> Optional[Dict]:
        src_tag = "pexels"
        q = random.choice(queries)
        headers = {"Authorization": self.pexels_key}
        want_video = self.bg.get("media_type", "auto") in ("auto", "video")
        if want_video:
            r = requests.get("https://api.pexels.com/videos/search",
                             headers=headers, timeout=30,
                             params={"query": q, "orientation": "portrait", "per_page": 15})
            if r.ok:
                for v in r.json().get("videos", []):
                    if self._seen(account, "pexels_v", v["id"]):
                        continue
                    files = sorted([f for f in v["video_files"] if f.get("height")],
                                   key=lambda f: abs((f.get("height") or 0) - self.H))
                    if not files:
                        continue
                    path = self._download(files[0]["link"], ".mp4")
                    self._mark(account, "pexels_v", v["id"])
                    log.info("background: pexels video #%s (%s)", v["id"], q)
                    return {"type": "video", "path": str(path), "source": src_tag}
        # photos
        r = requests.get("https://api.pexels.com/v1/search", headers=headers, timeout=30,
                         params={"query": q, "orientation": "portrait", "per_page": 15})
        if r.ok:
            for p in r.json().get("photos", []):
                if self._seen(account, "pexels_p", p["id"]):
                    continue
                url = p["src"].get("portrait") or p["src"].get("large2x") or p["src"]["original"]
                path = self._download(url, ".jpg")
                self._mark(account, "pexels_p", p["id"])
                log.info("background: pexels photo #%s (%s)", p["id"], q)
                return {"type": "image", "path": str(self._fit_image(path)), "source": src_tag}
        return None

    # ---- Pixabay ------------------------------------------------------
    def _from_pixabay(self, queries, account) -> Optional[Dict]:
        src_tag = "pixabay"
        q = random.choice(queries)
        if self.bg.get("media_type", "auto") in ("auto", "video"):
            r = requests.get("https://pixabay.com/api/videos/", timeout=30,
                             params={"key": self.pixabay_key, "q": q, "per_page": 20})
            if r.ok:
                for h in r.json().get("hits", []):
                    if self._seen(account, "pixabay_v", h["id"]):
                        continue
                    vids = h.get("videos", {})
                    url = (vids.get("large") or vids.get("medium") or {}).get("url")
                    if not url:
                        continue
                    path = self._download(url, ".mp4")
                    self._mark(account, "pixabay_v", h["id"])
                    log.info("background: pixabay video #%s (%s)", h["id"], q)
                    return {"type": "video", "path": str(path), "source": src_tag}
        r = requests.get("https://pixabay.com/api/", timeout=30,
                         params={"key": self.pixabay_key, "q": q, "image_type": "photo",
                                 "orientation": "vertical", "per_page": 20})
        if r.ok:
            for h in r.json().get("hits", []):
                if self._seen(account, "pixabay_p", h["id"]):
                    continue
                path = self._download(h["largeImageURL"], ".jpg")
                self._mark(account, "pixabay_p", h["id"])
                log.info("background: pixabay photo #%s (%s)", h["id"], q)
                return {"type": "image", "path": str(self._fit_image(path)), "source": src_tag}
        return None

    # ---- helpers ------------------------------------------------------
    def _fit_image(self, path: Path) -> Path:
        """Center-crop/scale any image to exactly WxH so ffmpeg has clean input."""
        img = Image.open(path).convert("RGB")
        tw, th = self.W, self.H
        sw, sh = img.size
        scale = max(tw / sw, th / sh)
        img = img.resize((int(sw * scale), int(sh * scale)), Image.LANCZOS)
        nw, nh = img.size
        left, top = (nw - tw) // 2, (nh - th) // 2
        img = img.crop((left, top, left + tw, top + th))
        out = path.with_suffix(".fit.jpg")
        img.save(out, quality=90)
        return out

    def _gradient(self, account) -> Dict:
        top, bottom = random.choice(_PALETTES)
        W, H = self.W, self.H
        ty = np.linspace(0, 1, H)[:, None]
        grad = np.zeros((H, W, 3), dtype=np.float32)
        for c in range(3):
            grad[..., c] = top[c] * (1 - ty) + bottom[c] * ty
        # subtle diagonal light + film grain for a premium feel
        xx = np.linspace(-1, 1, W)[None, :]
        yy = np.linspace(-1, 1, H)[:, None]
        glow = np.clip(1 - (xx**2 + (yy + 0.3)**2) * 0.5, 0, 1)[..., None]
        grad = grad + glow * 22
        grad += (np.random.randn(H, W, 1) * 4.0)
        grad = np.clip(grad, 0, 255).astype(np.uint8)
        img = Image.fromarray(grad, "RGB").filter(ImageFilter.GaussianBlur(1.2))
        h = hashlib.md5(f"{top}{bottom}{random.random()}".encode()).hexdigest()[:12]
        out = self.cache / f"gradient_{h}.jpg"
        img.save(out, quality=92)
        log.info("background: generated gradient (offline)")
        return {"type": "image", "path": str(out), "source": "gradient"}
