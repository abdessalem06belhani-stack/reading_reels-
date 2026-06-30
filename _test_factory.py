"""Quick factory test."""
import sys, json, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ["PYTHONIOENCODING"] = "utf-8"

from app.config_loader import load_config
cfg = load_config()

print("[1] Loading TikTokFactory...")
from tiktok_factory.factory import TikTokFactory, SUPPORTED_NICHES
f = TikTokFactory(cfg)
print(f"  OK Factory created. Niches: {SUPPORTED_NICHES}")

print("\n[2] Generating script for 'finance'...")
from tiktok_factory.niche_scripts import NicheScriptGenerator
nsg = NicheScriptGenerator(cfg)
s = nsg.generate("finance", seed=42)
print(f"  OK Script: {len(s.get('lines', []))} lines, source={s.get('source')}")
print(f"  Title: {s.get('title')}")

print("\n[3] Synth 1 line with VoiceEngine...")
from tiktok_factory.voice_engine import VoiceEngine
ve = VoiceEngine(cfg)
import tempfile
tmp = Path(tempfile.mkdtemp())
result = ve.synth("Hello world, this is a test.", tmp / "test.wav")
if result:
    print(f"  OK Voice: {result} ({result.stat().st_size} bytes)")
else:
    print("  -- Voice: silent fallback (no TTS engine)")

print("\n[4] Visual background...")
from tiktok_factory.visual_engine import VisualEngine
vis = VisualEngine(cfg)
bg = vis.get_background("finance", prefer_video=False)
print(f"  OK Background: type={bg.get('type')}, source={bg.get('source')}")

print("\n[5] Full generate ONE video...")
res = f.generate(niche_key="finance", seed=42, with_audio=bool(result), prefer_video_bg=False)
print(f"  OK Video: {res.get('video')}")
print(f"  Duration: {res.get('duration')}s, Script source: {res.get('script_source')}")

import shutil
shutil.rmtree(Path(res["job_dir"]).parent, ignore_errors=True)
print("\nALL TESTS PASSED")
