"""
Content Scraper — كشط محتوى من مصادر لكل نيش.
المصادر المدعومة: Reddit (JSON)، RSS feeds، Douyin (إصدار لاحق).
"""
from __future__ import annotations
import json, random, time, re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import requests
from xml.etree import ElementTree

from app.utils import get_logger

log = get_logger()

# ── Reddit endpoints ────────────────────────────────────────────
REDDIT_BASE = "https://www.reddit.com"
REDDIT_HEADERS = {"User-Agent": "TikTokFactory/2026.1 (by /u/reading_reels)"}

# ── Cache ───────────────────────────────────────────────────────
_cache_dir: Optional[Path] = None
_content_cache: dict = {}  # source_key -> [{...}]


def _load_content_cache(db_path: Path) -> dict:
    if db_path.exists():
        try:
            return json.loads(db_path.read_text())
        except Exception:
            return {}
    return {}


def _save_content_cache(db_path: Path, data: dict):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text(json.dumps(data, indent=2))


class ContentScraper:
    """جلب محتوى خام من Reddit/RSS لكل نيش."""

    def __init__(self, cfg):
        self.cfg = cfg
        global _cache_dir
        _cache_dir = cfg.abspath("assets/factory_content")
        _cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_source(self, source_url: str, max_items: int = 20,
                     force_refresh: bool = False) -> List[Dict]:
        """جلب محتوى من مصدر معين (Reddit subreddit أو RSS)."""
        # Reddit
        if source_url.startswith("reddit:r/"):
            sub = source_url.replace("reddit:r/", "")
            return self._fetch_reddit(sub, max_items, force_refresh)

        # RSS
        if source_url.startswith("rss:"):
            url = source_url[4:]
            return self._fetch_rss(url, max_items, force_refresh)

        log.warning("Unknown source type: %s", source_url)
        return []

    def fetch_niche_sources(self, niche_key: str, max_items: int = 5) -> List[Dict]:
        """جلب محتوى من جميع مصادر نيش معين."""
        import yaml

        niches_path = self.cfg.abspath("config/niches.yaml")
        if not niches_path.exists():
            return []

        data = yaml.safe_load(niches_path.read_text(encoding="utf-8"))
        niche = data.get("niches", {}).get(niche_key, {})
        sources = niche.get("content_sources", [])
        if not sources:
            log.warning("No sources for niche '%s'", niche_key)
            return []

        all_items = []
        for src in sources[:3]:  # حد أقصى 3 مصادر لكل نيش
            try:
                items = self.fetch_source(src, max_items=7)
                all_items.extend(items)
            except Exception as e:
                log.warning("Failed to fetch %s: %s", src, e)

        return all_items[:max_items]

    def _fetch_reddit(self, subreddit: str, max_items: int,
                      force_refresh: bool) -> List[Dict]:
        """جلب أحدث المنشورات من subreddit عبر JSON API."""
        cache_key = f"reddit:{subreddit}"
        cache_db = _cache_dir / "reddit_cache.json"
        cache = _load_content_cache(cache_db)
        now = time.time()

        # Cache check (10 دقائق صلاحية)
        if not force_refresh and cache_key in cache:
            cached = cache[cache_key]
            if now - cached.get("ts", 0) < 600:
                return cached.get("items", [])[:max_items]

        url = f"{REDDIT_BASE}/r/{subreddit}/hot.json?limit={max_items + 5}&t=week"
        try:
            r = requests.get(url, headers=REDDIT_HEADERS, timeout=20)
            if r.status_code != 200:
                log.warning("Reddit %s: HTTP %d", subreddit, r.status_code)
                return []

            data = r.json()
            posts = data.get("data", {}).get("children", [])
            items = []
            for post in posts:
                p = post.get("data", {})
                title = p.get("title", "")
                selftext = p.get("selftext", "")
                ups = p.get("ups", 0)
                comments = p.get("num_comments", 0)

                # تخطي المنشورات الضعيفة
                if ups < 10:
                    continue

                items.append({
                    "title": title,
                    "text": selftext[:500] if selftext else title,
                    "ups": ups,
                    "comments": comments,
                    "url": f"https://reddit.com{p.get('permalink', '')}",
                    "source": f"r/{subreddit}",
                })

            # تحديث cache
            cache[cache_key] = {"ts": now, "items": items}
            _save_content_cache(cache_db, cache)

            return items[:max_items]

        except Exception as e:
            log.warning("Reddit fetch error for %s: %s", subreddit, e)
            return []

    def _fetch_rss(self, url: str, max_items: int,
                    force_refresh: bool) -> List[Dict]:
        """جلب محتوى من RSS feed."""
        cache_key = f"rss:{url}"
        cache_db = _cache_dir / "rss_cache.json"
        cache = _load_content_cache(cache_db)
        now = time.time()

        if not force_refresh and cache_key in cache:
            cached = cache[cache_key]
            if now - cached.get("ts", 0) < 1800:  # 30 دقيقة
                return cached.get("items", [])[:max_items]

        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                return []

            items = []
            root = ElementTree.fromstring(r.content)

            # Standard RSS
            for item_elem in root.iter("item"):
                title = ""
                desc = ""
                for child in item_elem:
                    if child.tag == "title":
                        title = child.text or ""
                    elif child.tag in ("description", "content:encoded"):
                        desc = child.text or ""

                # تنظيف النص من HTML
                clean_desc = re.sub(r"<[^>]+>", "", desc)[:300]

                items.append({
                    "title": title,
                    "text": clean_desc or title,
                    "source": url,
                })
                if len(items) >= max_items:
                    break

            # Atom
            if not items:
                for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                    title = ""
                    summary = ""
                    for child in entry:
                        if child.tag == "{http://www.w3.org/2005/Atom}title":
                            title = child.text or ""
                        elif child.tag == "{http://www.w3.org/2005/Atom}summary":
                            summary = child.text or ""
                    clean = re.sub(r"<[^>]+>", "", summary)[:300]
                    items.append({"title": title, "text": clean or title, "source": url})
                    if len(items) >= max_items:
                        break

            cache[cache_key] = {"ts": now, "items": items}
            _save_content_cache(cache_db, cache)

            return items[:max_items]

        except Exception as e:
            log.warning("RSS fetch error for %s: %s", url, e)
            return []

    def extract_trending_topics(self, niche_key: str, max_topics: int = 5) -> List[str]:
        """استخراج المواضيع الرائجة من محتوى النيش."""
        items = self.fetch_niche_sources(niche_key, max_items=15)
        topics = []
        seen = set()
        for item in items:
            title = item.get("title", "")
            words = title.split()
            # جلب أول 3-5 كلمات كموضوع
            if words:
                topic = " ".join(words[:5]).strip()
                if topic and len(topic) > 10 and topic.lower() not in seen:
                    topics.append(topic)
                    seen.add(topic.lower())
        return topics[:max_topics]

    def clear_cache(self):
        """مسح كل ملفات cache."""
        for f in _cache_dir.glob("*_cache.json"):
            f.unlink()
        log.info("Content cache cleared")
