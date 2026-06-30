# reddit-reels — Execution Plan

## Goal
Build a standalone Reddit story video generator (`../reddit-reels/`) that:
- Pulls popular stories from justice/drama subreddits
- Generates TTS via edge-tts
- Creates word-by-word animated captions via Whisper timing
- Composes video with trending gameplay backgrounds + transformative edits
- Uploads auto to TikTok + YouTube + Instagram
- Runs free on GitHub Actions + cloud free tiers

## Architecture
```
main.py CLI → pipeline.py Orchestrator
  ├── reddit_scraper.py    → story_text + metadata
  ├── tts_edgetts.py       → audio.mp3
  ├── whisper_timing.py    → word_timestamps[]
  ├── background_pool.py   → download trending clips + scrub metadata
  ├── metadata_scrubber.py → strip EXIF/headers
  ├── caption_renderer.py  → word-by-word animated subs
  ├── composer.py          → MoviePy: bg + subs + audio + transitions
  └── uploaders/           → TikTok + YouTube + Instagram
```

## Files to Create (in order)

### Phase 1 — Scaffold & Core
1. `../reddit-reels/` project directory + folder structure
2. `requirements.txt` — all dependencies
3. `config/config.yaml` — main settings
4. `config/subreddits.yaml` — subreddit lists
5. `config/accounts.yaml` — platform accounts
6. `app/__init__.py` + `app/main.py` — CLI entry point (argparse)
7. `app/pipeline.py` — orchestration pipeline
8. `app/config_loader.py` — YAML + .env loading (copy pattern from reading_reels)
9. `app/utils.py` — logging, helpers

### Phase 2 — Content Agents
10. `agents/reddit_scraper.py` — PRAW + scoring
11. `agents/tts_edgetts.py` — edge-tts async
12. `agents/whisper_timing.py` — Whisper word alignment

### Phase 3 — Video Pipeline
13. `agents/metadata_scrubber.py` — strip EXIF
14. `agents/background_pool.py` — clip manager
15. `agents/caption_renderer.py` — word-by-word subs
16. `agents/composer.py` — MoviePy composition
17. `agents/metadata.py` — captions + hashtags (from reading_reels)

### Phase 4 — Upload & Deploy
18. `uploaders/tiktok_uploader.py`
19. `uploaders/youtube_uploader.py`
20. `uploaders/instagram_uploader.py`
21. `.github/workflows/generate.yml` — GitHub Actions
22. `deploy/Dockerfile` + `deploy/railway.json`
23. `tests/test_smoke.py` + `tests/test_agents.py`
24. `README.md`

## Acceptance Criteria
- `python -m app.main one --subreddit ProRevenge` produces a valid 60-90s MP4
- Word-by-word captions are synced with edge-tts audio
- Background clip is from pool, metadata-stripped, speed/color modified
- `python -m app.main upload --all` uploads to TikTok + YouTube Shorts + Instagram Reels
- GitHub Actions cron generates and uploads daily
- Zero API key cost (all free tiers)
- All metadata stripped from final outputs

## Execution Strategy
- Parallel delegation: Phase 1+2+3 can overlap
- Agents that are independent run simultaneously
- composer.py is the bottleneck — depends on all agents above
- tests run in parallel with implementation
