"""
VisualEngine — محرك بصري لجلب وتنسيق الخلفيات لكل نيش.
يدعم: فيديو من Pexels/Pixabay، صور عالية الجودة، Gradient احتياطي.
"""
from __future__ import annotations
import os, random, hashlib
from pathlib import Path
from typing import Dict, List, Optional
import requests
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

from app.utils import get_logger, load_used, save_used, ensure_dir

log = get_logger()

_PALETTES = [
    ((24, 33, 58), (86, 67, 110)),
    ((17, 46, 64), (16, 88, 96)),
    ((46, 26, 71), (120, 58, 95)),
    ((26, 42, 38), (74, 103, 73)),
    ((38, 24, 24), (110, 72, 58)),
    ((20, 30, 48), (52, 86, 139)),
    ((40, 22, 44), (96, 52, 88)),
    ((10, 10, 30), (30, 40, 80)),
    ((60, 40, 20), (100, 70, 50)),
    ((15, 50, 60), (30, 90, 100)),
]

# خلفيات SVG/موجات مدمجة لتأثيرات بصرية إضافية
_WAVE_OVERLAYS = []  # مستقبلاً: مسارات لصور تراكب


class VisualEngine:
    """جلب وتنسيق الخلفيات البصرية لكل فيديو."""

    def __init__(self, cfg):
        self.cfg = cfg
        fc = cfg.get("factory", "background", default={}) or cfg.get("background", default={})
        self.cache = ensure_dir(cfg.abspath(fc.get("cache_dir", "assets/factory_cache")))
        self.db_path = cfg.abspath(cfg.get("paths", "used_assets_db", default="assets/used_assets.json"))
        self.used = load_used(self.db_path)
        self.W = cfg.get("factory", "video", "width", default=1080) or cfg.get("video", "width", default=1080)
        self.H = cfg.get("factory", "video", "height", default=1920) or cfg.get("video", "height", default=1920)
        self.pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
        self.pixabay_key = os.getenv("PIXABAY_API_KEY", "").strip()

    def get_background(self, niche_key: str, account: str = "factory",
                       prefer_video: bool = True) -> Dict:
        """Get background for the given niche. Returns {type, path, source}."""
        # Get niche-specific keywords
        from tiktok_factory.niche_scripts import NicheScriptGenerator
        nsg = NicheScriptGenerator(self.cfg)
        keywords = nsg.get_visual_keywords(niche_key)

        # Try video first (higher retention)
        if prefer_video:
            for src in ["pexels", "pixabay"]:
                try:
                    if src == "pexels" and self.pexels_key:
                        res = self._pexels_video(keywords, account)
                        if res:
                            return res
                    elif src == "pixabay" and self.pixabay_key:
                        res = self._pixabay_video(keywords, account)
                        if res:
                            return res
                except Exception as e:
                    log.warning("video source %s failed: %s", src, e)

        # Try images
        for src in ["pexels", "pixabay", "gradient"]:
            try:
                if src == "pexels" and self.pexels_key:
                    res = self._pexels_image(keywords, account)
                    if res:
                        return res
                elif src == "pixabay" and self.pixabay_key:
                    res = self._pixabay_image(keywords, account)
                    if res:
                        return res
                elif src == "gradient":
                    return self._gradient(account)
            except Exception as e:
                log.warning("source %s failed: %s", src, e)

        return self._gradient(account)

    def get_slideshow(self, niche_key: str, num_images: int = 8,
                      account: str = "factory") -> Dict:
        """Get multiple images for slideshow mode."""
        from tiktok_factory.niche_scripts import NicheScriptGenerator
        nsg = NicheScriptGenerator(self.cfg)
        keywords = nsg.get_visual_keywords(niche_key)

        images = []
        for _ in range(num_images):
            for src in ["pexels", "pixabay", "gradient"]:
                try:
                    if src == "pexels" and self.pexels_key:
                        res = self._pexels_image_single(keywords, account)
                        if res:
                            images.append(res)
                            break
                    elif src == "pixabay" and self.pixabay_key:
                        res = self._pixabay_image_single(keywords, account)
                        if res:
                            images.append(res)
                            break
                    elif src == "gradient":
                        g = self._gradient(account)
                        images.append(g["path"])
                        break
                except Exception:
                    continue
            if len(images) <= _:
                g = self._gradient(account)
                images.append(g["path"])

        return {"type": "slideshow", "images": images[:num_images], "source": "mixed"}

    # ── Pexels Video ────────────────────────────────────────────
    def _pexels_video(self, queries: list, account: str) -> Optional[Dict]:
        q = random.choice(queries)
        headers = {"Authorization": self.pexels_key}
        r = requests.get("https://api.pexels.com/videos/search",
                         headers=headers, timeout=30,
                         params={"query": q, "orientation": "portrait", "per_page": 15,
                                 "min_duration": 5, "max_duration": 30})
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
                log.info("visual: pexels video #%s (%s)", v["id"], q)
                return {"type": "video", "path": str(path), "source": "pexels"}
        return None

    # ── Pixabay Video ───────────────────────────────────────────
    def _pixabay_video(self, queries: list, account: str) -> Optional[Dict]:
        q = random.choice(queries)
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
                log.info("visual: pixabay video #%s (%s)", h["id"], q)
                return {"type": "video", "path": str(path), "source": "pixabay"}
        return None

    # ── Pexels Image ────────────────────────────────────────────
    def _pexels_image(self, queries: list, account: str) -> Optional[Dict]:
        q = random.choice(queries)
        headers = {"Authorization": self.pexels_key}
        r = requests.get("https://api.pexels.com/v1/search", headers=headers, timeout=30,
                         params={"query": q, "orientation": "portrait", "per_page": 15})
        if r.ok:
            for p in r.json().get("photos", []):
                if self._seen(account, "pexels_p", p["id"]):
                    continue
                url = p["src"].get("original") or p["src"].get("large2x") or p["src"]["portrait"]
                path = self._download(url, ".jpg")
                self._mark(account, "pexels_p", p["id"])
                log.info("visual: pexels photo #%s (%s)", p["id"], q)
                return {"type": "image", "path": str(self._fit_image(path)), "source": "pexels"}
        return None

    def _pexels_image_single(self, queries: list, account: str) -> Optional[str]:
        res = self._pexels_image(queries, account)
        return res["path"] if res else None

    # ── Pixabay Image ───────────────────────────────────────────
    def _pixabay_image(self, queries: list, account: str) -> Optional[Dict]:
        q = random.choice(queries)
        r = requests.get("https://pixabay.com/api/", timeout=30,
                         params={"key": self.pixabay_key, "q": q,
                                 "image_type": "photo", "orientation": "vertical",
                                 "per_page": 20, "min_width": self.W})
        if r.ok:
            for h in r.json().get("hits", []):
                if self._seen(account, "pixabay_p", h["id"]):
                    continue
                path = self._download(h["largeImageURL"], ".jpg")
                self._mark(account, "pixabay_p", h["id"])
                log.info("visual: pixabay photo #%s (%s)", h["id"], q)
                return {"type": "image", "path": str(self._fit_image(path)), "source": "pixabay"}
        return None

    def _pixabay_image_single(self, queries: list, account: str) -> Optional[str]:
        res = self._pixabay_image(queries, account)
        return res["path"] if res else None

    # ── Helpers ─────────────────────────────────────────────────
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
        r = requests.get(url, timeout=120, stream=True)
        if not r.ok:
            raise RuntimeError(f"download failed ({r.status_code})")
        with open(out, "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
        return out

    def _enhance_image(self, img: Image.Image) -> Image.Image:
        bg_cfg = self.cfg.get("factory", "background", default={}) or {}
        if not bg_cfg.get("enhance_image", True):
            return img
        sharpen = float(bg_cfg.get("sharpen_amount", 0.3))
        if sharpen > 0:
            img = ImageEnhance.Sharpness(img).enhance(1.0 + sharpen)
        contrast = float(bg_cfg.get("contrast_boost", 1.05))
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        saturation = float(bg_cfg.get("saturation_boost", 1.10))
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        return img

    def _fit_image(self, path: Path) -> Path:
        """Center-crop/scale image to exact WxH."""
        img = Image.open(path).convert("RGB")
        img = self._enhance_image(img)
        tw, th = self.W, self.H
        sw, sh = img.size
        scale = max(tw / sw, th / sh)
        img = img.resize((int(sw * scale), int(sh * scale)), Image.LANCZOS)
        nw, nh = img.size
        left, top = (nw - tw) // 2, (nh - th) // 2
        img = img.crop((left, top, left + tw, top + th))
        out = path.with_suffix(".fit.jpg")
        img.save(out, quality=97)
        return out

    def _gradient(self, account) -> Dict:
        """Generate HD gradient background."""
        top, bottom = random.choice(_PALETTES)
        W, H = self.W, self.H
        ty = np.linspace(0, 1, H)[:, None]
        grad = np.zeros((H, W, 3), dtype=np.float32)
        for c in range(3):
            grad[..., c] = top[c] * (1 - ty) + bottom[c] * ty
        # Premium glow effect
        xx = np.linspace(-1, 1, W)[None, :]
        yy = np.linspace(-1, 1, H)[:, None]
        glow = np.clip(1 - (xx**2 + (yy + 0.3)**2) * 0.5, 0, 1)[..., None]
        grad = grad + glow * 22
        grad += (np.random.randn(H, W, 1) * 4.0)
        grad = np.clip(grad, 0, 255).astype(np.uint8)
        img = Image.fromarray(grad, "RGB").filter(ImageFilter.GaussianBlur(1.2))
        h = hashlib.md5(f"{top}{bottom}{random.random()}".encode()).hexdigest()[:12]
        out = self.cache / f"gradient_{h}.jpg"
        img.save(out, quality=95)
        log.info("visual: generated HD gradient")
        return {"type": "image", "path": str(out), "source": "gradient"}
