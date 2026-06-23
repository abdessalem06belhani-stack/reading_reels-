
"""
Rendering engine.

Pipeline:
  1. Pillow builds a tall transparent PNG "text strip" with the intro phrases
     (bold, large) then the reading lines stacked sentence-under-sentence,
     each with an outline + shadow for contrast over ANY background.
  2. Pillow builds a full-frame "scrim" PNG (dark contrast layer + vignette).
  3. ffmpeg composites:  background  ->  scrim  ->  slowly-scrolling text strip
     then muxes the (optional) audio and exports a TikTok-ready 1080x1920 MP4.

The slow upward "credit scroll" keeps text on screen and readable from the
first second to the last, which is the core retention mechanic.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from app.utils import get_logger, run_ffmpeg, ensure_dir

log = get_logger()

_DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJAVU_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _hex(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))


def _load_font(cfg, bold: bool, size: int) -> ImageFont.FreeTypeFont:
    rel = cfg.get("text", "font_bold" if bold else "font_regular")
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
            lines.append(cur); cur = wd
    if cur:
        lines.append(cur)
    return lines


class Renderer:
    def __init__(self, cfg):
        self.cfg = cfg
        v = cfg.get("video", default={})
        self.W = v.get("width", 1080)
        self.H = v.get("height", 1920)
        self.fps = v.get("fps", 30)
        self.crf = v.get("crf", 20)
        self.preset = v.get("preset", "medium")
        self.pix_fmt = v.get("pix_fmt", "yuv420p")
        self.t = cfg.get("text", default={})

    # ------------------------------------------------------------------
    def build_text_strip(self, intro: List[str], lines: List[str], out_png: Path):
        W = self.W
        margin = self.t.get("side_margin", 96)
        max_w = W - 2 * margin
        intro_font = _load_font(self.cfg, bold=True, size=self.t.get("intro_font_size", 86))
        body_font  = _load_font(self.cfg, bold=False, size=self.t.get("body_font_size", 60))
        spacing_mult = self.t.get("line_spacing", 1.35)
        block_gap = self.t.get("block_spacing", 56)
        top_pad = bottom_pad = 60

        # measure with a scratch canvas
        scratch = ImageDraw.Draw(Image.new("RGBA", (W, 10)))
        blocks = [("intro", p) for p in intro] + [("body", ln) for ln in lines]
        plan = []   # (font, wrapped_lines, line_height, is_intro)
        total_h = top_pad
        for kind, text in blocks:
            font = intro_font if kind == "intro" else body_font
            asc, desc = font.getmetrics()
            line_h = int((asc + desc) * spacing_mult)
            wl = _wrap(scratch, text, font, max_w)
            plan.append((font, wl, line_h, kind == "intro"))
            total_h += len(wl) * line_h + block_gap + (40 if kind == "intro" else 0)
        total_h += bottom_pad

        img = Image.new("RGBA", (W, total_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        fill = _hex(self.t.get("text_color", "#FFFFFF"))
        stroke = _hex(self.t.get("stroke_color", "#000000"))
        sw = self.t.get("stroke_width", 6)
        shadow = self.t.get("shadow", True)
        soff = self.t.get("shadow_offset", 5)

        y = top_pad
        for font, wl, line_h, is_intro in plan:
            for sub in wl:
                tw = draw.textlength(sub, font=font)
                x = (W - tw) / 2
                if shadow:
                    draw.text((x + soff, y + soff), sub, font=font,
                              fill=(0, 0, 0, 150), stroke_width=sw, stroke_fill=(0, 0, 0, 150))
                draw.text((x, y), sub, font=font, fill=fill + (255,),
                          stroke_width=sw, stroke_fill=stroke + (255,))
                y += line_h
            y += block_gap + (40 if is_intro else 0)

        ensure_dir(out_png.parent)
        img.save(out_png)
        log.info("text strip: %dx%d (%d blocks)", W, total_h, len(plan))
        return out_png, W, total_h

    # ------------------------------------------------------------------
    def build_scrim(self, out_png: Path):
        s = self.cfg.get("scrim", default={})
        W, H = self.W, self.H
        opacity = float(s.get("opacity", 0.42))
        base = np.full((H, W), int(255 * opacity), dtype=np.float32)
        if s.get("vignette", True):
            yy = np.linspace(-1, 1, H)[:, None]
            edge = np.clip(yy**2, 0, 1)            # darker at very top & bottom
            base = base + edge * (255 * 0.30)
        alpha = np.clip(base, 0, 255).astype(np.uint8)
        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        rgba[..., 3] = alpha                       # black with variable alpha
        ensure_dir(out_png.parent)
        Image.fromarray(rgba, "RGBA").save(out_png)
        return out_png

    # ------------------------------------------------------------------
    def _scroll_expr(self, strip_h: int, duration: float):
        H = self.H
        start_frac = self.t.get("start_offset_frac", 0.10)
        end_frac = self.t.get("end_visible_frac", 0.80)
        direction = self.t.get("scroll_direction", "up")
        y0 = H * start_frac
        if direction != "up" or strip_h <= H * (end_frac - start_frac):
            y_static = (H - strip_h) / 2
            return f"{y_static:.1f}"
        travel = strip_h - H * (end_frac - start_frac)
        speed = travel / max(1.0, duration)
        return f"{y0:.1f}-{speed:.4f}*t"

    # ------------------------------------------------------------------
    def _audio_args(self, audio_path: Optional[str], music: Optional[str],
                    music_gain: int, voice_gain: int, duration: float):
        """Return (extra_inputs, filter_str, out_label). Always yields audio."""
        extra, filt = [], []
        idx = 3  # inputs 0,1,2 are bg/scrim/strip
        voice_lbl = music_lbl = None
        if audio_path:
            extra += ["-i", audio_path]
            filt.append(f"[{idx}:a]volume={voice_gain}dB,apad,atrim=0:{duration}[v]")
            voice_lbl = "[v]"; idx += 1
        if music:
            extra += ["-stream_loop", "-1", "-i", music]
            filt.append(f"[{idx}:a]volume={music_gain}dB,atrim=0:{duration}[m]")
            music_lbl = "[m]"; idx += 1
        if voice_lbl and music_lbl:
            filt.append(f"{voice_lbl}{music_lbl}amix=inputs=2:duration=longest:dropout_transition=0[outa]")
            out = "[outa]"
        elif voice_lbl:
            filt.append(f"{voice_lbl}anull[outa]"); out = "[outa]"
        elif music_lbl:
            filt.append(f"{music_lbl}anull[outa]"); out = "[outa]"
        else:
            extra += ["-f", "lavfi", "-t", str(duration), "-i", "anullsrc=r=48000:cl=stereo"]
            out = f"{idx}:a"
        return extra, filt, out

    # ------------------------------------------------------------------
    def compose(self, background: Dict, strip_png: Path, strip_h: int,
                scrim_png: Path, duration: float, out_mp4: Path,
                audio_path: Optional[str] = None) -> Path:
        W, H, fps = self.W, self.H, self.fps
        bg = self.cfg.get("background", default={})
        a = self.cfg.get("audio", default={})
        frames = int(duration * fps) + 1
        is_video = background["type"] == "video"

        inputs = []
        if is_video:
            inputs += ["-stream_loop", "-1", "-i", background["path"]]
        else:
            inputs += ["-loop", "1", "-t", str(duration), "-i", background["path"]]
        inputs += ["-loop", "1", "-t", str(duration), "-i", str(scrim_png)]
        inputs += ["-loop", "1", "-t", str(duration), "-i", str(strip_png)]

        # background filter
        is_gradient = background.get("source") == "gradient"
        kenburns = bg.get("kenburns", True) and not is_gradient
        if is_video:
            bg_f = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                    f"crop={W}:{H},fps={fps},setsar=1,format=rgba[bg]")
        elif kenburns:
            # cheap, smooth Ken Burns: prescale ~12% then slowly pan the crop
            # window diagonally across the clip (orders of magnitude faster
            # than zoompan, no per-frame full-frame resampling).
            ov = float(bg.get("kenburns_zoom", 1.10))
            sw, sh = int(W * ov), int(H * ov)
            bg_f = (f"[0:v]scale={sw}:{sh},"
                    f"crop={W}:{H}:x='(in_w-{W})*(t/{duration})':y='(in_h-{H})*(t/{duration})',"
                    f"fps={fps},setsar=1,format=rgba[bg]")
        else:
            bg_f = f"[0:v]scale={W}:{H},fps={fps},setsar=1,format=rgba[bg]"

        yexpr = self._scroll_expr(strip_h, duration)
        vfilters = [
            bg_f,
            "[bg][1:v]overlay=0:0:format=auto[bgs]",
            f"[bgs][2:v]overlay=x=0:y='{yexpr}':eval=frame:format=auto[outv]",
        ]

        extra, afilters, alabel = self._audio_args(
            audio_path, a.get("music_file") or None,
            a.get("music_gain_db", -22), a.get("voice_gain_db", 0), duration)

        filter_complex = ";".join(vfilters + afilters)
        args = [*inputs, *extra,
                "-filter_complex", filter_complex,
                "-map", "[outv]", "-map", alabel,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", str(self.crf),
                "-pix_fmt", self.pix_fmt, "-r", str(fps),
                "-threads", "1",
                "-max_muxing_queue_size", "1024",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(duration), "-movflags", "+faststart",
                str(out_mp4)]
        ensure_dir(out_mp4.parent)
        try:
            run_ffmpeg(args, desc=f"render {out_mp4.name}")
        except RuntimeError:
            log.warning("main render failed → retrying with format=yuv420p on bg")
            bg_f_yuv = bg_f.replace("format=rgba", "format=yuv420p")
            vf_yuv = [bg_f_yuv] + vfilters[1:]
            fc_yuv = ";".join(vf_yuv + afilters)
            args_yuv = [
                *inputs, *extra,
                "-filter_complex", fc_yuv,
                "-map", "[outv]", "-map", alabel,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", str(self.crf),
                "-pix_fmt", self.pix_fmt, "-r", str(fps),
                "-threads", "1",
                "-max_muxing_queue_size", "1024",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(duration), "-movflags", "+faststart",
                str(out_mp4)]
            run_ffmpeg(args_yuv, desc=f"render {out_mp4.name} (fallback)")
        return out_mp4
