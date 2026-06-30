"""
VideoComposer — تركيب الفيديو النهائي بتقنية HD.
يستخدم ffmpeg/Pillow لدمج: خلفية (فيديو/صورة) + سكريبت + صوت + تأثيرات.
"""
from __future__ import annotations
import json, random
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

from app.utils import get_logger, run_ffmpeg, ensure_dir, timestamp

log = get_logger()

_DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJAVU_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _hex(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))


def _load_font(cfg, bold: bool, size: int):
    rel = cfg.get("factory", "text", "font_bold" if bold else "font_regular", default=None)
    if rel is None:
        rel = cfg.get("text", "font_bold" if bold else "font_regular", default=None)
    candidates = []
    if rel:
        candidates.append(str(cfg.abspath(rel)))
    candidates.append(_DEJAVU_BOLD if bold else _DEJAVU_REG)
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(draw, text: str, font, max_w: int) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for wd in words:
        test = (cur + " " + wd).strip()
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


class VideoComposer:
    """Video composer producing HD 1080×1920 TikTok videos."""

    def __init__(self, cfg):
        self.cfg = cfg
        v = cfg.get("factory", "video", default={}) or cfg.get("video", default={})
        self.W = v.get("width", 1080)
        self.H = v.get("height", 1920)
        self.fps = v.get("fps", 30)
        self.crf = v.get("crf", 17)
        self.preset = v.get("preset", "slow")
        self.pix_fmt = v.get("pix_fmt", "yuv420p")
        self.bitrate = v.get("bitrate", "10000k")
        self.max_bitrate = v.get("max_bitrate", "15000k")
        self.audio_bitrate = v.get("audio_bitrate", "192k")
        self.profile = v.get("profile", "high")
        self.level = v.get("level", "4.1")
        self.tune = v.get("tune", "stillimage")

    def render(self, niche_key: str, script: Dict, background: Dict,
               audio_path: Optional[str], output_path: Path,
               duration_sec: Optional[float] = None) -> Path:
        """Full video render pipeline: text strip → scrim → compose."""

        lines = script.get("lines", [])
        title = script.get("title", "TikTok Video")
        color_palette = script.get("color_palette", {})

        # Build text strip
        strip_png = output_path.parent / "text_strip.png"
        strip_h = self._build_text_strip(lines, strip_png, color_palette)

        # Build scrim
        scrim_png = output_path.parent / "scrim.png"
        self._build_scrim(scrim_png)

        # Determine duration
        target_sec = duration_sec or 120.0
        dur = max(min(target_sec, 130.0), 110.0)

        # FFmpeg composition
        out = self._compose(background, strip_png, strip_h, scrim_png,
                            dur, output_path, audio_path)

        # Write timing metadata
        timing = {"total": dur, "lines": len(lines)}
        (output_path.parent / "timing.json").write_text(json.dumps(timing, indent=2))

        log.info("Video rendered: %s (%.1fs, %s)", output_path, dur, niche_key)
        return out

    def _build_text_strip(self, lines: List[str], out_png: Path,
                          color_palette: dict) -> int:
        """Build transparent text strip with all reading lines."""
        W = self.W
        margin = 72
        max_w = W - 2 * margin
        body_font = _load_font(self.cfg, bold=False, size=54)

        lvl_accent = _hex(color_palette.get("accent", "#FFD700"))
        lvl_fill = _hex(color_palette.get("text", "#FFFFFF"))
        lvl_highlight = _hex(color_palette.get("highlight", "#FFD700"))
        lvl_stroke = _hex(color_palette.get("stroke", "#000000"))

        spacing_mult = 1.35
        block_gap = 48
        top_pad = bottom_pad = 60

        scratch = ImageDraw.Draw(Image.new("RGBA", (W, 10)))
        font = body_font
        asc, desc = font.getmetrics()
        line_h = int((asc + desc) * spacing_mult)

        total_h = top_pad
        wrapped = []
        for ln in lines:
            wl = _wrap(scratch, ln, font, max_w)
            wrapped.append(wl)
            total_h += len(wl) * line_h + block_gap
        total_h += bottom_pad

        img = Image.new("RGBA", (W, max(total_h, 100)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        sw = 5
        shadow = True
        soff = 3
        shadow_clr = _hex("#1A0F05")
        glow = True
        glow_rad = 4

        y = top_pad
        for bi, wl in enumerate(wrapped):
            for si, sub in enumerate(wl):
                tw = draw.textlength(sub, font=font)
                x = (W - tw) / 2

                # Highlight first word of each line
                words = sub.split(" ", 1)
                if len(words) > 1 and si == 0:
                    first_word = words[0] + " "
                    rest = words[1]
                    fw = draw.textlength(first_word, font=font)

                    # First word in highlight color
                    if glow:
                        self._draw_glow(draw, x, y, first_word, font, lvl_highlight, 6)
                    if shadow:
                        draw.text((x + soff, y + soff), first_word, font=font,
                                  fill=shadow_clr + (180,), stroke_width=0)
                    draw.text((x, y), first_word, font=font,
                              fill=lvl_highlight + (255,),
                              stroke_width=sw, stroke_fill=lvl_stroke + (255,))

                    # Rest in normal color
                    x2 = x + fw
                    if glow:
                        self._draw_glow(draw, x2, y, rest, font, lvl_highlight, glow_rad)
                    if shadow:
                        draw.text((x2 + soff, y + soff), rest, font=font,
                                  fill=shadow_clr + (180,), stroke_width=0)
                    draw.text((x2, y), rest, font=font,
                              fill=lvl_fill + (255,),
                              stroke_width=sw, stroke_fill=lvl_stroke + (255,))
                else:
                    if glow:
                        self._draw_glow(draw, x, y, sub, font, lvl_highlight, glow_rad)
                    if shadow:
                        draw.text((x + soff, y + soff), sub, font=font,
                                  fill=shadow_clr + (180,), stroke_width=0)
                    draw.text((x, y), sub, font=font,
                              fill=lvl_fill + (255,),
                              stroke_width=sw, stroke_fill=lvl_stroke + (255,))
                y += line_h
            y += block_gap

        ensure_dir(out_png.parent)
        img.save(out_png)
        return total_h

    def _draw_glow(self, draw, x, y, text, font, color, radius):
        gc = color[:3]
        for r in range(radius, 0, -1):
            alpha = max(30, 120 - r * 15)
            for ox, oy in [(r, 0), (-r, 0), (0, r), (0, -r),
                            (r, r), (-r, -r), (r, -r), (-r, r)]:
                draw.text((x + ox, y + oy), text, font=font, fill=gc + (alpha,))

    def _build_scrim(self, out_png: Path):
        """Build dark overlay + vignette for text contrast."""
        W, H = self.W, self.H
        import numpy as np
        opacity = 0.35
        base = np.full((H, W), int(255 * opacity), dtype=np.float32)
        # Vignette
        vs = 0.25
        yy = np.linspace(-1, 1, H)[:, None]
        edge = np.clip(yy ** 2, 0, 1)
        base = base + edge * (255 * vs)
        alpha = np.clip(base, 0, 255).astype(np.uint8)
        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        rgba[..., 3] = alpha
        img = Image.fromarray(rgba, "RGBA").filter(
            ImageFilter.GaussianBlur(2))
        img.save(out_png)
        return out_png

    def _compose(self, background: Dict, strip_png: Path, strip_h: int,
                 scrim_png: Path, duration: float, out_mp4: Path,
                 audio_path: Optional[str] = None) -> Path:
        """FFmpeg composition: bg + scrim + scrolling text + audio."""
        W, H, fps = self.W, self.H, self.fps

        # Handle slideshow
        if background.get("type") == "slideshow":
            return self._compose_slideshow(background, strip_png, strip_h,
                                           scrim_png, duration, out_mp4, audio_path)

        is_video = background.get("type") == "video"

        inputs = []
        if is_video:
            inputs += ["-stream_loop", "-1", "-i", background["path"]]
        else:
            inputs += ["-loop", "1", "-t", str(duration), "-i", background["path"]]
        inputs += ["-loop", "1", "-t", str(duration), "-i", str(scrim_png)]
        inputs += ["-loop", "1", "-t", str(duration), "-i", str(strip_png)]

        # Background filter
        if is_video:
            bg_f = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                    f"crop={W}:{H},fps={fps},setsar=1,format=rgba[bg]")
        else:
            ov = 1.08
            sw, sh = int(W * ov), int(H * ov)
            bg_f = (f"[0:v]scale={sw}:{sh},"
                    f"crop={W}:{H}:x='(in_w-{W})*(t/{duration})':y='(in_h-{H})*(t/{duration})',"
                    f"fps={fps},setsar=1,format=rgba[bg]")

        # Scroll expression
        start_frac = 0.10
        end_frac = 0.82
        y0 = H * start_frac
        if strip_h <= H * (end_frac - start_frac):
            y_static = (H - strip_h) / 2
            yexpr = f"{y_static:.1f}"
        else:
            travel = strip_h - H * (end_frac - start_frac)
            speed = travel / max(1.0, duration)
            yexpr = f"{y0:.1f}-{speed:.4f}*t"

        vfilters = [
            bg_f,
            "[bg][1:v]overlay=0:0:format=auto[bgs]",
            f"[bgs][2:v]overlay=x=0:y='{yexpr}':eval=frame:format=auto[outv]",
        ]

        extra, afilters, alabel = self._audio_args(audio_path, duration)

        filter_complex = ";".join(vfilters + afilters)
        args = [
            *inputs, *extra,
            "-filter_threads", "1", "-threads", "1",
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", alabel,
            "-c:v", "libx264", "-preset", self.preset, "-crf", str(self.crf),
            "-b:v", self.bitrate, "-maxrate", self.max_bitrate,
            "-bufsize", f"{int(int(self.max_bitrate.rstrip('k')) * 2)}k",
            "-profile:v", self.profile, "-level", self.level,
            "-tune", self.tune,
            "-pix_fmt", self.pix_fmt, "-r", str(fps),
            "-c:a", "aac", "-b:a", self.audio_bitrate,
            "-t", str(duration), "-movflags", "+faststart",
            str(out_mp4),
        ]
        ensure_dir(out_mp4.parent)
        run_ffmpeg(args, desc=f"render factory {out_mp4.name}")
        return out_mp4

    def _compose_slideshow(self, background, strip_png, strip_h,
                           scrim_png, duration, out_mp4, audio_path):
        """Slideshow mode: multiple images transitioning."""
        W, H, fps = self.W, self.H, self.fps
        images = background.get("images", [])

        if not images:
            return self._compose(
                {"type": "image", "path": images[0]} if images else
                {"type": "image", "path": ""},
                strip_png, strip_h, scrim_png, duration, out_mp4, audio_path
            )

        img_dur = max(5.0, duration / len(images))
        inputs = []
        concat_parts = []

        for i, img_path in enumerate(images):
            idx = i * 3
            inputs += ["-loop", "1", "-t", str(img_dur + 0.5), "-i", img_path]
            inputs += ["-loop", "1", "-t", str(img_dur + 0.5), "-i", str(scrim_png)]
            inputs += ["-loop", "1", "-t", str(img_dur + 0.5), "-i", str(strip_png)]

            start_frac = 0.10
            end_frac = 0.82
            y0 = H * start_frac
            if strip_h <= H * (end_frac - start_frac):
                y_static = (H - strip_h) / 2
                yexpr = f"{y_static:.1f}"
            else:
                travel = strip_h - H * (end_frac - start_frac)
                speed = travel / max(1.0, img_dur + 0.5)
                yexpr = f"{y0:.1f}-{speed:.4f}*t"

            concat_parts.append(f"[{idx}]scale={W}:{H},fps={fps},setsar=1,format=rgba[bg{i}];")
            concat_parts.append(f"[bg{i}][{idx+1}]overlay=0:0:format=auto[bgs{i}];")
            concat_parts.append(
                f"[bgs{i}][{idx+2}]overlay=x=0:y='{yexpr}':eval=frame:format=auto[v{i}];"
            )

        concat_expr = "".join(concat_parts)
        for i in range(len(images)):
            concat_expr += f"[v{i}]"
        concat_expr += f"concat=n={len(images)}:v=1[outv]"

        extra, afilters, alabel = self._audio_args(audio_path, duration,
                                                     start_idx=len(images) * 3)
        filter_complex = concat_expr + ";" + ";".join(afilters)

        args = [
            *inputs, *extra,
            "-filter_threads", "1", "-threads", "1",
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", alabel,
            "-c:v", "libx264", "-preset", self.preset, "-crf", str(self.crf),
            "-b:v", self.bitrate, "-maxrate", self.max_bitrate,
            "-bufsize", f"{int(int(self.max_bitrate.rstrip('k')) * 2)}k",
            "-profile:v", self.profile, "-level", self.level,
            "-tune", self.tune,
            "-pix_fmt", self.pix_fmt, "-r", str(fps),
            "-c:a", "aac", "-b:a", self.audio_bitrate,
            "-movflags", "+faststart",
            str(out_mp4),
        ]
        ensure_dir(out_mp4.parent)
        log.info("slideshow: %d images, ~%ds each", len(images), int(img_dur))
        run_ffmpeg(args, desc=f"render slideshow {out_mp4.name}")
        return out_mp4

    def _audio_args(self, audio_path: Optional[str], duration: float,
                    start_idx: int = 3):
        """Build audio filter chain. Always produces audio (silent if needed)."""
        extra, filt = [], []
        idx = start_idx
        out = None
        if audio_path:
            extra += ["-i", audio_path]
            filt.append(f"[{idx}:a]volume=0dB,apad,atrim=0:{duration}[v]")
            out = "[v]"
            idx += 1

        if out is None:
            extra += ["-f", "lavfi", "-t", str(duration), "-i",
                       "anullsrc=r=48000:cl=stereo"]
            out = f"{idx}:a"

        return extra, filt, out
