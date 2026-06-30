"""
reading_reels CLI.

Examples:
  python -m app.main doctor
  python -m app.main one --level B1
  python -m app.main one --level A2 --topic "a quiet morning routine" --no-audio
  python -m app.main one --level B1 --auto-upload          # generate + post to TikTok
  python -m app.main batch --count 5 --level B1
  python -m app.main accounts --auto-upload
  python -m app.main upload --video outputs/jobs/.../video.mp4 --caption-file .../caption.txt
"""
from __future__ import annotations
import argparse, os, sys, json
from pathlib import Path

# allow running both as `python -m app.main` and `python app/main.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config_loader import load_config
from app.pipeline import Pipeline
from app.utils import get_logger, ffmpeg_bin

# TikTok Factory — اختياري، silent if not installed
try:
    from tiktok_factory.factory import TikTokFactory, SUPPORTED_NICHES
    _HAS_FACTORY = True
except ImportError:
    _HAS_FACTORY = False

log = get_logger()


def cmd_doctor(cfg, args):
    print("reading_reels environment check")
    print("-" * 50)
    try:
        print(f"ffmpeg            : {ffmpeg_bin()}")
    except Exception as e:
        print(f"ffmpeg            : MISSING ({e})")
    print(f"NVIDIA_API_KEY    : {'set' if os.getenv('NVIDIA_API_KEY') else 'NOT set -> local fallback'}")
    print(f"PEXELS_API_KEY    : {'set' if os.getenv('PEXELS_API_KEY') else 'NOT set'}")
    print(f"PIXABAY_API_KEY   : {'set' if os.getenv('PIXABAY_API_KEY') else 'NOT set'}")
    print(f"AI provider/model : {cfg.get('ai','provider')} / {cfg.get('ai','model')}")
    print(f"Levels available  : {list(cfg.levels)}")
    print(f"Accounts          : {[a['id'] for a in cfg.accounts.get('accounts', [])]}")
    print(f"Upload enabled    : {cfg.get('upload','enabled', default=False)} (method={cfg.get('upload','method', default='web')})")
    for mod in ("gtts", "pyttsx3", "selenium"):
        try:
            __import__(mod); print(f"module {mod:9s}   : available")
        except Exception:
            print(f"module {mod:9s}   : not installed")
    print("-" * 50)
    print("OK - ready to generate. Run:  python -m app.main one --level B1")


def cmd_one(cfg, args):
    pipe = Pipeline(cfg)
    res = pipe.generate_one(args.level, topic=args.topic, seed=args.seed,
                            with_audio=not args.no_audio, auto_upload=args.auto_upload,
                            title_override=args.title, caption_override=args.caption,
                            hashtags_override=args.hashtags, duration=args.duration,
                            text_color=args.text_color, tts_speed=args.tts_speed,
                            use_slideshow=args.slideshow)
    keys = ("video", "job_dir", "duration", "script_source")
    out = {k: res[k] for k in keys}
    if "upload" in res:
        out["upload"] = res["upload"]
    print(json.dumps(out, indent=2))


def cmd_batch(cfg, args):
    pipe = Pipeline(cfg)
    res = pipe.generate_batch(args.count, level=args.level, with_audio=not args.no_audio,
                              auto_upload=args.auto_upload,
                              title_override=args.title, caption_override=args.caption,
                              hashtags_override=args.hashtags, duration=args.duration,
                              text_color=args.text_color, tts_speed=args.tts_speed,
                              use_slideshow=args.slideshow)
    print(f"\nGenerated {len(res)} videos:")
    for r in res:
        print(" -", r["video"], ("[uploaded]" if r.get("upload", {}).get("status") == "submitted" else ""))


def cmd_accounts(cfg, args):
    pipe = Pipeline(cfg)
    total = []
    for acc in cfg.accounts.get("accounts", []):
        n = args.per_account or acc.get("posting", {}).get("per_day", 1)
        log.info("account %s -> %d videos", acc["id"], n)
        total += pipe.generate_batch(n, level=acc.get("level"), account=acc,
                                     with_audio=not args.no_audio, auto_upload=args.auto_upload)
    print(f"\nGenerated {len(total)} videos across {len(cfg.accounts.get('accounts', []))} accounts.")


def cmd_upload(cfg, args):
    """Upload an already-generated video to TikTok."""
    from agents.uploader import TikTokUploader
    caption = ""
    if args.caption_file and Path(args.caption_file).exists():
        caption = Path(args.caption_file).read_text()
    elif args.caption:
        caption = args.caption
    res = TikTokUploader(cfg).upload(args.video, caption, job_dir=str(Path(args.video).parent))
    print(json.dumps(res, indent=2))


# ─── TikTok Factory CLI ─────────────────────────────────────────
def cmd_factory_one(cfg, args):
    """Generate one factory video for a given niche."""
    if not _HAS_FACTORY:
        print("ERROR: tiktok_factory not installed. Run: pip install -r requirements.txt")
        return
    factory = TikTokFactory(cfg)
    res = factory.generate(
        niche_key=args.niche,
        seed=args.seed,
        with_audio=not args.no_audio,
        prefer_video_bg=not args.no_video,
    )
    keys = ("video", "job_dir", "niche", "niche_name", "duration", "script_source")
    out = {k: res[k] for k in keys}
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_factory_batch(cfg, args):
    """Generate multiple factory videos."""
    if not _HAS_FACTORY:
        print("ERROR: tiktok_factory not installed. Run: pip install -r requirements.txt")
        return
    factory = TikTokFactory(cfg)
    if args.niche:
        results = factory.generate_niche_batch(args.niche, count=args.count,
                                               with_audio=not args.no_audio)
    else:
        results = factory.generate_batch(count=args.count, niche=None,
                                         with_audio=not args.no_audio)
    print(f"\n✅ Factory generated {len(results)}/{args.count} videos:")
    for r in results:
        print(f"   • {r['niche_emoji'] if 'niche_emoji' in r else '📹'} "
              f"[{r['niche']}] {r['video']}")


def cmd_factory_report(cfg, args):
    """Show niches report."""
    if not _HAS_FACTORY:
        print("ERROR: tiktok_factory not installed.")
        return
    factory = TikTokFactory(cfg)
    print(factory.niche_report())


def build_parser():
    p = argparse.ArgumentParser(prog="reading_reels",
                                description="Free-first TikTok English reading video generator")
    p.add_argument("--config", default=None, help="path to config dir")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="check environment & keys"); d.set_defaults(fn=cmd_doctor)

    o = sub.add_parser("one", help="generate a single video")
    o.add_argument("--level", default="B1")
    o.add_argument("--topic", default=None)
    o.add_argument("--seed", type=int, default=None)
    o.add_argument("--duration", type=int, default=None, help="target duration in seconds (60-180)")
    o.add_argument("--text-color", default=None, help="text color hex (#RRGGBB)")
    o.add_argument("--tts-speed", type=float, default=None, help="TTS speed multiplier (0.8-1.5)")
    o.add_argument("--slideshow", action="store_true", help="use slideshow mode with multiple images")
    o.add_argument("--title", default=None, help="override video title")
    o.add_argument("--caption", default=None, help="override TikTok caption")
    o.add_argument("--hashtags", default=None, help="override hashtags (comma-separated)")
    o.add_argument("--no-audio", action="store_true")
    o.add_argument("--auto-upload", action="store_true", help="post to TikTok after rendering")
    o.set_defaults(fn=cmd_one)

    b = sub.add_parser("batch", help="generate N videos")
    b.add_argument("--count", type=int, default=3)
    b.add_argument("--level", default=None)
    b.add_argument("--duration", type=int, default=None)
    b.add_argument("--text-color", default=None)
    b.add_argument("--tts-speed", type=float, default=None)
    b.add_argument("--slideshow", action="store_true")
    b.add_argument("--title", default=None)
    b.add_argument("--caption", default=None)
    b.add_argument("--hashtags", default=None)
    b.add_argument("--no-audio", action="store_true")
    b.add_argument("--auto-upload", action="store_true")
    b.set_defaults(fn=cmd_batch)

    a = sub.add_parser("accounts", help="generate per account from accounts.yaml")
    a.add_argument("--per-account", type=int, default=None)
    a.add_argument("--no-audio", action="store_true")
    a.add_argument("--auto-upload", action="store_true")
    a.set_defaults(fn=cmd_accounts)

    u = sub.add_parser("upload", help="upload an existing video to TikTok")
    u.add_argument("--video", required=True)
    u.add_argument("--caption-file", default=None)
    u.add_argument("--caption", default=None)
    u.set_defaults(fn=cmd_upload)

    if _HAS_FACTORY:
        # ── Factory: one ──
        fo = sub.add_parser("factory-one", help="generate one factory video for a niche")
        fo.add_argument("--niche", default="finance",
                        choices=SUPPORTED_NICHES,
                        help="niche to generate (finance, ai_tools, real_estate, health_biohacking, productivity)")
        fo.add_argument("--seed", type=int, default=None)
        fo.add_argument("--no-audio", action="store_true")
        fo.add_argument("--no-video", action="store_true", help="use images instead of video background")
        fo.set_defaults(fn=cmd_factory_one)

        # ── Factory: batch ──
        fb = sub.add_parser("factory-batch", help="generate multiple factory videos")
        fb.add_argument("--count", type=int, default=3)
        fb.add_argument("--niche", default=None, choices=SUPPORTED_NICHES,
                        help="specific niche (random if omitted)")
        fb.add_argument("--no-audio", action="store_true")
        fb.set_defaults(fn=cmd_factory_batch)

        # ── Factory: report ──
        fr = sub.add_parser("factory-report", help="show factory niches report")
        fr.set_defaults(fn=cmd_factory_report)

    return p


def main():
    args = build_parser().parse_args()
    cfg = load_config(args.config)
    args.fn(cfg, args)


if __name__ == "__main__":
    main()
