# reading_reels — Free-first TikTok English Reading Video Generator

Automatically generates **vertical (1080×1920) ~2-minute English reading-practice videos**
in the TikTok "slow reading" style: two spoken intro phrases, then level-appropriate
reading lines stacked sentence-under-sentence that **scroll slowly upward** so the viewer
keeps reading to the very last second (the core retention mechanic).

- 🎚️ **5 CEFR levels** — A1, A2, B1, B2, C1 (vocabulary, sentence length & pacing tuned per level)
- 📖 **One coherent paragraph per video** — a connected mini-story on a single topic (not random lines), with words matched to the level
- 🧠 **AI scripts via NVIDIA NIM** (free hosted endpoints for prototyping) with a built-in **offline content engine** fallback
- 🖼️ **Fresh background per video** from **Pexels / Pixabay** free tiers, with an always-available **generated gradient** fallback (no key needed)
- 🗣️ **Free TTS** for the intro phrases (gTTS online → pyttsx3 offline → silent)
- 🎬 **Fast renderer** — Pillow builds the text layer, a static **ffmpeg** binary composites it (no system install required)
- ⬆️ **Auto-upload to TikTok** — browser automation (your own login) or the official API
- 🪟 **Windows 10 ready** — `setup.bat` + `run.bat` (double-click), plus an Arabic guide
- 🏭 **Batch + multi-account** content operation, upload-ready packages (video + caption + hashtags)
- 💸 **Runs with ZERO keys and ZERO cost** out of the box

> ⚡ **Works the moment you unzip it.** No API keys required for the first video — it uses the
> offline content engine + generated gradient background. Add keys later to upgrade quality.

> 🪟 **Windows 10:** install Python 3.10+ (tick *Add to PATH*), then **double-click `setup.bat`**,
> then **double-click `run.bat`** and use the menu. Arabic walkthrough: **[README_AR.md](README_AR.md)**.

---

## 60-second quickstart

```bash
# 1. unzip and enter
cd reading_reels

# 2. (recommended) create a virtual env
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 3. install dependencies (includes a bundled ffmpeg via imageio-ffmpeg)
pip install -r requirements.txt

# 4. check everything is wired up
python -m app.main doctor

# 5. make your first video (no keys needed)
python -m app.main one --level B1
```

The finished video + caption + hashtags land in `outputs/jobs/<timestamp>_<name>/`.

Make a batch, or one batch per configured account:

```bash
python -m app.main batch --count 5 --level A2
python -m app.main accounts
```

---

## Add the free upgrades (optional, all free)

Copy `.env.example` to `.env` and fill in whichever keys you have:

| Capability                     | Variable          | Where to get it (free)                 | Without it |
|--------------------------------|-------------------|----------------------------------------|------------|
| Better AI reading scripts      | `NVIDIA_API_KEY`  | https://build.nvidia.com               | offline content engine |
| Real photo/video backgrounds   | `PEXELS_API_KEY`  | https://www.pexels.com/api/            | gradient backgrounds |
| Extra background source        | `PIXABAY_API_KEY` | https://pixabay.com/api/docs/          | gradient backgrounds |

Step-by-step instructions for each key are in **[docs/API_KEYS.md](docs/API_KEYS.md)**.

---

## Documentation

| Doc | What's inside |
|-----|---------------|
| [docs/SETUP.md](docs/SETUP.md)            | Install & run locally (Windows/macOS/Linux) |
| [docs/API_KEYS.md](docs/API_KEYS.md)      | **Step-by-step** for every API key + where it goes |
| [docs/ACCOUNT_SETUP.md](docs/ACCOUNT_SETUP.md) | TikTok account matrix, niches, uploading, policy-safe operation |
| [docs/UPLOAD_TIKTOK.md](docs/UPLOAD_TIKTOK.md) | **Auto-upload** setup (browser automation + official API) |
| [README_AR.md](README_AR.md)              | الدليل الكامل بالعربية خطوة بخطوة (ويندوز) |
| [docs/USAGE.md](docs/USAGE.md)            | Every CLI command, switching levels, tuning |
| [docs/BATCH_WORKFLOW.md](docs/BATCH_WORKFLOW.md) | Mass production & multi-account batches |
| [docs/CLOUD_DEPLOY.md](docs/CLOUD_DEPLOY.md) | Free cloud automation (GitHub Actions, Docker, schedulers) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, stages, MVP vs advanced, fallbacks |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Fixes for common issues |

## Folder structure

```
reading_reels/
├── app/            # CLI + orchestration pipeline + config loader + utils
├── agents/         # script_generator, segmenter, timing, background, tts, metadata
├── render/         # Pillow + ffmpeg rendering engine
├── content/        # offline content engine (no-API fallback)
├── prompts/        # NVIDIA NIM prompt templates
├── config/         # config.yaml, levels.yaml, topics.yaml, accounts.yaml
├── fonts/          # bundled Lexend (reading-optimized) + drop-in fonts
├── assets/         # background cache + dedup db
├── outputs/jobs/   # finished videos + caption.txt + metadata.json
├── deploy/         # GitHub Actions workflow + Dockerfile
├── examples/       # ready-to-run example scripts
├── docs/           # all guides
├── requirements.txt
└── .env.example
```

## License / assets note
Code: use freely. Backgrounds from Pexels/Pixabay are free to use; review their terms.
Bundled font: **Lexend** (SIL Open Font License) — designed to improve reading proficiency.
This tool **prepares** upload-ready video packages; it does not auto-post. See ACCOUNT_SETUP.md.
