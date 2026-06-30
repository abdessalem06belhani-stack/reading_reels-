"""
BackgroundPool: Manages a local pool of background video clips downloaded from YouTube.

Uses yt-dlp to search and download gameplay clips (Minecraft parkour, Subway Surfers, GTA 5, etc.),
applies transformative modifications for copyright safety, and provides a deduplicated pool per account.
"""
from __future__ import annotations
import os
import json
import random
import hashlib
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import threading

from app.utils import get_logger, ensure_dir

log = get_logger()

# Default search queries for popular gameplay content
DEFAULT_QUERIES = [
    "Minecraft parkour no copyright gameplay",
    "Subway Surfers gameplay no copyright",
    "GTA 5 driving gameplay no copyright",
    "oddly satisfying compilation no copyright",
    "Minecraft building timelapse no copyright",
    "Subway Surfers high score gameplay",
    "GTA 5 cinematic driving no copyright",
    "satisfying video compilation no copyright",
    "Minecraft redstone contraption no copyright",
    "Subway Surfers world record gameplay",
]

# Target video specs
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30


@dataclass
class ClipInfo:
    """Metadata for a cached background clip."""
    path: str
    source: str  # "youtube", "youtube_modified"
    query: str
    duration: float
    width: int
    height: int
    downloaded_at: str = field(default_factory=lambda: datetime.now().isoformat())
    used_accounts: List[str] = field(default_factory=list)
    transform_params: Dict[str, Any] = field(default_factory=dict)
    file_hash: str = ""


class BackgroundPool:
    """
    Manages a local pool of background video clips downloaded from YouTube.
    
    Features:
    - Downloads clips using yt-dlp with search queries
    - Maintains a persistent pool with metadata (JSON index)
    - Deduplication per account (don't reuse same clip for same account)
    - Transformative modifications for copyright safety (speed, crop, metadata strip)
    - Ken Burns effect helper for slow pan/zoom
    """
    
    def __init__(
        self,
        pool_dir: Path,
        min_clips: int = 20,
        target_width: int = TARGET_WIDTH,
        target_height: int = TARGET_HEIGHT,
        target_fps: int = TARGET_FPS,
        queries: Optional[List[str]] = None,
    ):
        self.pool_dir = Path(pool_dir)
        self.min_clips = min_clips
        self.target_width = target_width
        self.target_height = target_height
        self.target_fps = target_fps
        self.queries = queries or DEFAULT_QUERIES
        
        # Pool subdirectories
        self.raw_dir = self.pool_dir / "raw"
        self.processed_dir = self.pool_dir / "processed"
        self.index_path = self.pool_dir / "pool_index.json"
        
        ensure_dir(self.raw_dir)
        ensure_dir(self.processed_dir)
        
        # Thread safety for index operations
        self._lock = threading.Lock()
        
        # Load or create index
        self._index: Dict[str, ClipInfo] = {}
        self._load_index()
        
        # Check for ffmpeg and yt-dlp availability
        self._ffmpeg_path = self._find_ffmpeg()
        self._yt_dlp_path = self._find_yt_dlp()
        
        if not self._ffmpeg_path:
            log.warning("ffmpeg not found - video processing will be limited")
        if not self._yt_dlp_path:
            log.warning("yt-dlp not found - YouTube downloads will not work")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find ffmpeg executable."""
        for name in ["ffmpeg", "ffmpeg.exe"]:
            path = shutil.which(name)
            if path:
                return path
        # Check imageio-ffmpeg fallback
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return None
    
    def _find_yt_dlp(self) -> Optional[str]:
        """Find yt-dlp executable."""
        for name in ["yt-dlp", "yt-dlp.exe"]:
            path = shutil.which(name)
            if path:
                return path
        # Try python -m yt_dlp
        try:
            subprocess.run(["python", "-m", "yt_dlp", "--version"], 
                          capture_output=True, check=True)
            return "python -m yt_dlp"
        except Exception:
            return None
    
    def _load_index(self) -> None:
        """Load the pool index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._index = {k: ClipInfo(**v) for k, v in data.items()}
                log.info("Loaded background pool index: %d clips", len(self._index))
            except Exception as e:
                log.warning("Failed to load pool index: %s", e)
                self._index = {}
        else:
            self._index = {}
    
    def _save_index(self) -> None:
        """Save the pool index to disk."""
        with self._lock:
            data = {k: asdict(v) for k, v in self._index.items()}
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
    
    def _compute_file_hash(self, path: Path) -> str:
        """Compute SHA256 hash of file for deduplication."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    
    def _run_ffmpeg(self, args: List[str], desc: str = "ffmpeg") -> bool:
        """Run ffmpeg command."""
        if not self._ffmpeg_path:
            log.error("ffmpeg not available")
            return False
        
        cmd = [self._ffmpeg_path] + args
        try:
            log.debug("Running %s: %s", desc, " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                log.error("%s failed: %s", desc, result.stderr)
                return False
            return True
        except subprocess.TimeoutExpired:
            log.error("%s timed out", desc)
            return False
        except Exception as e:
            log.error("%s error: %s", desc, e)
            return False
    
    def _run_yt_dlp(self, args: List[str], desc: str = "yt-dlp") -> bool:
        """Run yt-dlp command."""
        if not self._yt_dlp_path:
            log.error("yt-dlp not available")
            return False
        
        if self._yt_dlp_path.startswith("python"):
            cmd = self._yt_dlp_path.split() + args
        else:
            cmd = [self._yt_dlp_path] + args
        
        try:
            log.debug("Running %s: %s", desc, " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                log.error("%s failed: %s", desc, result.stderr)
                return False
            return True
        except subprocess.TimeoutExpired:
            log.error("%s timed out", desc)
            return False
        except Exception as e:
            log.error("%s error: %s", desc, e)
            return False
    
    def _get_video_info(self, path: Path) -> Optional[Dict]:
        """Get video duration, width, height using ffprobe."""
        if not self._ffmpeg_path:
            return None
        
        ffprobe = self._ffmpeg_path.replace("ffmpeg", "ffprobe")
        if not Path(ffprobe).exists():
            # Try to find ffprobe
            ffprobe = shutil.which("ffprobe") or ffprobe
        
        cmd = [
            ffprobe, "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration",
            "-of", "json",
            str(path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                stream = data.get("streams", [{}])[0]
                return {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0),
                    "duration": float(stream.get("duration", 0)),
                }
        except Exception as e:
            log.warning("ffprobe failed for %s: %s", path, e)
        return None
    
    def download_clip(self, query: str, output_dir: Path) -> Optional[Path]:
        """
        Search YouTube for query and download highest quality vertical/croppable version.
        
        Args:
            query: Search query like "Minecraft parkour no copyright gameplay"
            output_dir: Directory to save the downloaded clip
            
        Returns:
            Path to downloaded clip, or None if failed
        """
        if not self._yt_dlp_path:
            log.error("yt-dlp not available for download")
            return None
        
        ensure_dir(output_dir)
        
        # Generate unique filename based on query hash
        query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_template = str(output_dir / f"{query_hash}_{timestamp}.%(ext)s")
        
        # yt-dlp args: search, prefer vertical, best quality, no playlists
        args = [
            f"ytsearch5:{query}",  # Search and get top 5 results
            "--format", "bestvideo[height>=1080][width<=1920]+bestaudio/best[height>=1080]",
            "--merge-output-format", "mp4",
            "-o", out_template,
            "--no-playlist",
            "--no-warnings",
            "--quiet",
            "--no-check-certificates",
        ]
        
        if not self._run_yt_dlp(args, f"download {query}"):
            return None
        
        # Find the downloaded file
        downloaded_files = list(output_dir.glob(f"{query_hash}_{timestamp}.*"))
        if not downloaded_files:
            log.warning("No file downloaded for query: %s", query)
            return None
        
        downloaded = downloaded_files[0]
        log.info("Downloaded clip: %s", downloaded.name)
        return downloaded
    
    def strip_metadata(self, path: Path) -> Path:
        """
        Strip ALL metadata from video using ffmpeg.
        
        Uses -map_metadata -1 -fflags +bitexact to remove:
        - creation_time
        - encoder tags
        - software tags
        - All other metadata
        
        Args:
            path: Input video path
            
        Returns:
            Path to metadata-stripped video
        """
        out_path = self.processed_dir / f"{path.stem}_nometa{path.suffix}"
        
        args = [
            "-i", str(path),
            "-map_metadata", "-1",
            "-fflags", "+bitexact",
            "-c", "copy",
            "-y", str(out_path)
        ]
        
        if self._run_ffmpeg(args, f"strip_metadata {path.name}"):
            log.debug("Stripped metadata: %s -> %s", path.name, out_path.name)
            return out_path
        return path
    
    def transform(self, path: Path) -> Path:
        """
        Apply subtle transformative changes for copyright safety:
        - Speed: random 0.95-1.05x
        - Crop: slight random offset (0-5% shift)
        - No scale change (keep 1080x1920 target)
        
        Args:
            path: Input video path
            
        Returns:
            Path to transformed video
        """
        # Generate transform parameters
        speed = random.uniform(0.95, 1.05)
        # Random crop offset up to 5%
        max_offset_x = int(self.target_width * 0.05)
        max_offset_y = int(self.target_height * 0.05)
        crop_x = random.randint(0, max_offset_x)
        crop_y = random.randint(0, max_offset_y)
        
        out_path = self.processed_dir / f"{path.stem}_transformed{path.suffix}"
        
        # Build filter chain
        filters = []
        
        # Speed change (affects both video and audio)
        if abs(speed - 1.0) > 0.001:
            filters.append(f"setpts={1/speed}*PTS")
            # Also adjust audio tempo if present
            filters.append(f"atempo={speed}")
        
        # Crop with slight offset
        crop_w = self.target_width - crop_x
        crop_h = self.target_height - crop_y
        if crop_x > 0 or crop_y > 0:
            filters.append(f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}")
        
        # Scale to target if needed (should already be close)
        filters.append(f"scale={self.target_width}:{self.target_height}:force_original_aspect_ratio=decrease")
        filters.append(f"pad={self.target_width}:{self.target_height}:(ow-iw)/2:(oh-ih)/2")
        filters.append(f"fps={self.target_fps}")
        
        filter_str = ",".join(filters)
        
        args = [
            "-i", str(path),
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y", str(out_path)
        ]
        
        if self._run_ffmpeg(args, f"transform {path.name}"):
            log.info("Transformed clip: %s (speed=%.2f, crop=%dx%d)", 
                     path.name, speed, crop_x, crop_y)
            # Store transform params for reference
            return out_path
        return path
    
    def kenburns_filter(self, clip_path: str, duration: float, zoom: float = 1.05) -> str:
        """
        Returns ffmpeg filter string for slow Ken Burns pan/zoom effect.
        
        Args:
            clip_path: Path to video clip (for reference)
            duration: Duration of the effect in seconds
            zoom: Maximum zoom factor (default 1.05 = 5% zoom)
            
        Returns:
            FFmpeg filter string for zoompan effect
        """
        # Scale up by zoom factor, then crop a sliding window
        sw = int(self.target_width * zoom)
        sh = int(self.target_height * zoom)
        
        # Slow diagonal pan across the duration
        # x goes from 0 to (sw - target_width) over duration
        # y goes from 0 to (sh - target_height) over duration
        max_x = sw - self.target_width
        max_y = sh - self.target_height
        
        filter_str = (
            f"zoompan=z='min({zoom},1+({zoom}-1)*t/{duration})':"
            f"x='{max_x}*(t/{duration})':"
            f"y='{max_y}*(t/{duration})':"
            f"d={int(duration * self.target_fps)}:"
            f"s={self.target_width}x{self.target_height}:"
            f"fps={self.target_fps}"
        )
        return filter_str
    
    def ensure_pool(self, min_clips: Optional[int] = None) -> int:
        """
        Auto-download popular clips if pool is low.
        
        Args:
            min_clips: Minimum clips to maintain (default: self.min_clips)
            
        Returns:
            Number of clips in pool after ensuring
        """
        min_clips = min_clips or self.min_clips
        current_count = len(self._index)
        
        if current_count >= min_clips:
            log.info("Pool has %d clips (min: %d), no download needed", current_count, min_clips)
            return current_count
        
        needed = min_clips - current_count
        log.info("Pool has %d clips, need %d more. Starting downloads...", current_count, needed)
        
        downloaded = 0
        for query in self.queries:
            if downloaded >= needed:
                break
            
            log.info("Downloading for query: %s", query)
            clip_path = self.download_clip(query, self.raw_dir)
            
            if clip_path and clip_path.exists():
                # Process the clip
                processed = self._process_new_clip(clip_path, query)
                if processed:
                    downloaded += 1
                    log.info("Added clip to pool (%d/%d)", downloaded, needed)
        
        log.info("Pool ensure complete: %d clips total", len(self._index))
        return len(self._index)
    
    def _process_new_clip(self, raw_path: Path, query: str) -> Optional[ClipInfo]:
        """Process a newly downloaded clip: strip metadata, transform, index."""
        # Get video info
        info = self._get_video_info(raw_path)
        if not info or info["duration"] < 5:
            log.warning("Clip too short or invalid: %s", raw_path)
            raw_path.unlink(missing_ok=True)
            return None
        
        # Strip metadata
        no_meta_path = self.strip_metadata(raw_path)
        
        # Transform for copyright safety
        transformed_path = self.transform(no_meta_path)
        
        # Compute hash for deduplication
        file_hash = self._compute_file_hash(transformed_path)
        
        # Check if already in pool (by hash)
        for clip_id, clip_info in self._index.items():
            if clip_info.file_hash == file_hash:
                log.info("Duplicate clip detected, skipping: %s", transformed_path.name)
                transformed_path.unlink(missing_ok=True)
                return None
        
        # Create clip info
        clip_id = file_hash
        clip_info = ClipInfo(
            path=str(transformed_path),
            source="youtube_modified",
            query=query,
            duration=info["duration"],
            width=info["width"],
            height=info["height"],
            file_hash=file_hash,
            transform_params={
                "speed": "random_0.95_1.05",
                "crop_offset": "random_0_5_percent",
            }
        )
        
        # Add to index
        with self._lock:
            self._index[clip_id] = clip_info
            self._save_index()
        
        # Clean up intermediate files
        if no_meta_path != transformed_path:
            no_meta_path.unlink(missing_ok=True)
        raw_path.unlink(missing_ok=True)
        
        return clip_info
    
    def get_random_clip(self, account: str = "default") -> Optional[Dict]:
        """
        Pick random clip from pool with dedup (don't repeat same clip for same account).
        
        Args:
            account: Account identifier for deduplication
            
        Returns:
            Dict with {type: "video", path: str, source: "youtube"} or None
        """
        if not self._index:
            log.warning("Pool is empty, call ensure_pool() first")
            return None
        
        # Filter clips not used by this account
        available = [
            (cid, info) for cid, info in self._index.items()
            if account not in info.used_accounts
        ]
        
        if not available:
            # All clips used, reset for this account (or pick least recently used)
            log.info("All clips used for account %s, resetting dedup", account)
            available = list(self._index.items())
        
        clip_id, clip_info = random.choice(available)
        
        # Mark as used for this account
        clip_info.used_accounts.append(account)
        with self._lock:
            self._save_index()
        
        return {
            "type": "video",
            "path": clip_info.path,
            "source": clip_info.source,
            "duration": clip_info.duration,
            "width": clip_info.width,
            "height": clip_info.height,
        }
    
    def get(self, query: str, account: str = "default") -> Optional[Dict]:
        """
        Full pipeline: get clip → strip_metadata → transform.
        
        Args:
            query: Search query
            account: Account identifier for deduplication
            
        Returns:
            Dict with {type: "video", path: str, source: "youtube_modified"} or None
        """
        # First try to get from pool
        clip = self.get_random_clip(account)
        if clip:
            return clip
        
        # Pool empty or all used, download new
        log.info("Downloading new clip for query: %s", query)
        raw_path = self.download_clip(query, self.raw_dir)
        if not raw_path:
            return None
        
        processed = self._process_new_clip(raw_path, query)
        if not processed:
            return None
        
        # Mark as used for this account
        processed.used_accounts.append(account)
        with self._lock:
            self._save_index()
        
        return {
            "type": "video",
            "path": processed.path,
            "source": "youtube_modified",
            "duration": processed.duration,
            "width": processed.width,
            "height": processed.height,
        }
    
    def get_pool_stats(self) -> Dict:
        """Get statistics about the current pool."""
        total_duration = sum(c.duration for c in self._index.values())
        sources = {}
        for c in self._index.values():
            sources[c.source] = sources.get(c.source, 0) + 1
        
        return {
            "total_clips": len(self._index),
            "total_duration_sec": round(total_duration, 1),
            "total_duration_min": round(total_duration / 60, 1),
            "by_source": sources,
            "pool_dir": str(self.pool_dir),
        }
    
    def cleanup_old_clips(self, max_age_days: int = 30, max_clips: int = 100) -> int:
        """
        Remove old/unused clips to manage disk space.
        
        Args:
            max_age_days: Remove clips older than this many days
            max_clips: Maximum clips to keep (removes oldest first)
            
        Returns:
            Number of clips removed
        """
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(days=max_age_days)
        removed = 0
        
        # Sort by download date (oldest first)
        sorted_clips = sorted(
            self._index.items(),
            key=lambda x: x[1].downloaded_at
        )
        
        for clip_id, clip_info in sorted_clips:
            should_remove = False
            
            # Check age
            try:
                downloaded = datetime.fromisoformat(clip_info.downloaded_at)
                if downloaded < cutoff:
                    should_remove = True
            except Exception:
                pass
            
            # Check max clips
            if len(self._index) - removed > max_clips:
                should_remove = True
            
            if should_remove:
                Path(clip_info.path).unlink(missing_ok=True)
                del self._index[clip_id]
                removed += 1
                log.info("Removed old clip: %s", clip_id)
        
        if removed:
            self._save_index()
        
        return removed


# Convenience function for quick pool creation
def create_background_pool(
    base_dir: Path,
    min_clips: int = 20,
    queries: Optional[List[str]] = None,
) -> BackgroundPool:
    """Create and initialize a BackgroundPool."""
    pool = BackgroundPool(
        pool_dir=base_dir / "background_pool",
        min_clips=min_clips,
        queries=queries,
    )
    pool.ensure_pool()
    return pool