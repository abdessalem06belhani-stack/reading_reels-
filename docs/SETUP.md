# Setup & Run Locally

Works on **Linux, macOS, and Windows**. Python **3.9+** (3.10–3.12 recommended).

## 1. Get the code
Unzip `reading_reels.zip` and open a terminal in the `reading_reels/` folder.

## 2. Create a virtual environment (recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows PowerShell
```

## 3. Install dependencies
```bash
pip install -r requirements.txt
```
This installs Pillow, numpy, requests, PyYAML, python-dotenv, moviepy, gTTS, pyttsx3,
and **imageio-ffmpeg** — which ships a static **ffmpeg** binary, so you do **not** need
to install ffmpeg system-wide. (If you already have system ffmpeg, it will be used.)

## 4. Verify the environment
```bash
python -m app.main doctor
```
You should see the ffmpeg path, which keys are set, the AI model, levels, and accounts.

## 5. Make your first video (no keys required)
```bash
python -m app.main one --level B1
```
Output appears in `outputs/jobs/<timestamp>_<name>/`:
- `*.mp4`         → the finished 1080×1920 video
- `caption.txt`   → ready-to-paste caption + hashtags
- `metadata.json` → title, level, caption, hashtags, account
- `script.json`   → the generated reading script
- `timing.json`   → per-line timing map

## 6. (Optional) add free API keys
See **[API_KEYS.md](API_KEYS.md)** to enable AI scripts (NVIDIA NIM) and real
photo/video backgrounds (Pexels / Pixabay). Copy `.env.example` → `.env` and fill in.

---

## Platform notes

**ffmpeg:** bundled via imageio-ffmpeg — nothing to install. To force a specific ffmpeg,
put it on your PATH; the tool prefers a system `ffmpeg` if present.

**pyttsx3 (offline TTS):**
- Linux: needs `espeak` → `sudo apt-get install espeak` (or `espeak-ng`).
- macOS: works out of the box (uses NSSpeechSynthesizer).
- Windows: works out of the box (uses SAPI5).
- If pyttsx3 is unavailable, the tool uses gTTS (online) or renders silently.

**gTTS (online TTS):** needs internet. Best free voice quality. Set the accent in
`config/config.yaml` → `audio.tts_tld` (`com`=US, `co.uk`=UK, `com.au`=AU, `ca`=CA).

**Rendering time:** a full ~2-minute 1080×1920 video typically renders in a few minutes
on a laptop CPU. Speed it up with `video.preset: veryfast` (or `ultrafast`) in
`config/config.yaml` while prototyping; use `medium`/`slow` for final quality.

## Run without the module syntax
You can also run:
```bash
python app/main.py one --level A2
```
Both forms work (the CLI fixes up the import path).
