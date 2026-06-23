# Architecture

## Executive summary
`reading_reels` is a Python pipeline that turns a **(level, topic)** pair into a finished,
upload-ready vertical reading-practice video. Every external dependency is **free-first**
and has a **fallback**, so the system runs at zero cost and never hard-fails.

## Pipeline (text diagram)

```
            ┌─────────────────────────────────────────────────────────────┐
   level ─► │                        Pipeline (app/pipeline.py)            │
   topic ─► │                                                              │
            │  1 ScriptGenerator ─ NVIDIA NIM ──(fail/no key)──► local bank│
            │        │  {title, lines[], hook, ending, caption, hashtags}  │
            │  2 Segmenter ─ clean whitespace, keep sentences              │
            │  3 Timing ─ per-line durations, fit to ~120s (readable)      │
            │  4 Background ─ Pexels ─► Pixabay ─► generated gradient      │
            │  5 TTS ─ gTTS ─► pyttsx3 ─► silent  (intro phrases)          │
            │  6 Renderer:                                                 │
            │        a Pillow builds tall text strip (intro + lines)       │
            │        b Pillow builds dark scrim (contrast + vignette)      │
            │        c ffmpeg composites bg → scrim → scrolling strip      │
            │           + Ken Burns pan (photos) + audio mux + loudnorm    │
            │  7 Metadata ─ caption + hashtags + filename                  │
            └───────────────────────────┬─────────────────────────────────┘
                                         ▼
                       outputs/jobs/<ts>_<name>/  (mp4 + caption + json)
```

## Stage table

| Stage | Tool (primary) | Why | Free? | Fallback |
|-------|----------------|-----|-------|----------|
| Topic/level select | YAML config + rotation | deterministic, editable | ✅ open source | random across families |
| Script generation | **NVIDIA NIM** (OpenAI-compatible) | strong free hosted LLMs for prototyping | ✅ free for prototyping | **offline content engine** (`content/fallback_bank.py`) |
| Segmentation | pure Python | zero deps | ✅ open source | — |
| Timing map | pure Python | precise pacing per level | ✅ open source | — |
| Backgrounds | **Pexels** (video+photo) | generous free tier, portrait | ✅ free tier | **Pixabay** → **generated gradient** (offline) |
| TTS | **gTTS** | natural, free | ✅ free (online) | **pyttsx3** (offline) → silent |
| Rendering | **ffmpeg** via imageio-ffmpeg + **Pillow** | fast, no system install, full control | ✅ open source | system ffmpeg if present |
| Packaging | Python/JSON | upload-ready | ✅ open source | — |
| Scheduling | GitHub Actions cron | free CI minutes | ✅ free tier | local cron / Render / Fly |

## Retention engineering (why the format holds attention)
- **Two fixed intro phrases** = instant brand recognition + a 0–2s hook.
- **Easy first lines** pull beginners in; difficulty bumps gently mid-video.
- **One idea per line**, short width-wrapped lines = effortless reading rhythm.
- **Slow upward scroll** keeps new text arriving so there's always a reason to stay.
- **`end_visible_frac`** keeps the **last line on screen at the final second** → high
  completion + natural re-watch (loop psychology).
- **Calm visuals** (dark scrim + subtle motion) reduce cognitive load = longer holds.
- **Per-line timing** scales to the level's WPM so pacing is readable, never rushed.

These map directly to settings: `text.start_offset_frac`, `text.end_visible_frac`,
`levels.*.words_per_minute`, `levels.*.max_words_per_line`, `scrim.opacity`.

## MVP vs Advanced vs Self-hosted

**MVP (free, this repo, runs anywhere):**
offline content engine + gradient backgrounds + gTTS + local ffmpeg render. Zero keys.

**Advanced free-first (recommended):**
+ `NVIDIA_API_KEY` for AI scripts, + `PEXELS_API_KEY`/`PIXABAY_API_KEY` for real
backgrounds, + GitHub Actions cron for hands-off daily batches, + object storage
(Cloudflare R2 / GitHub Releases / artifacts) for outputs, + a metadata store
(Supabase free tier or a committed `assets/used_assets.json`) for dedup.

**Self-hosted:**
run a NIM container locally/on a GPU box for unlimited script generation; render on the
same machine; schedule with system cron or a small worker queue. Highest control, no
rate limits, but you manage infra.

## Parallelism / agentic batch
`generate_batch` and `accounts` iterate jobs independently — each video is a self-contained
unit (own script, background, audio, render). This maps cleanly onto parallel workers or
sub-agents: shard the account/level matrix, render in parallel, collect packages. The
dedup DB is the only shared state (append-only, keyed per account).

## Key modules
- `app/pipeline.py` — orchestrator
- `agents/script_generator.py` — NIM + offline fallback (strict JSON parsing)
- `agents/background.py` — Pexels/Pixabay/gradient + dedup
- `agents/tts.py` — gTTS/pyttsx3 + loudness normalization
- `render/renderer.py` — Pillow text strip + scrim + ffmpeg compositing & scroll
- `content/fallback_bank.py` — offline, level-aware content engine
- `config/*.yaml` — all tunables
