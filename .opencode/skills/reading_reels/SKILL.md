---
name: reading-reels
description: Use ONLY when working on the reading_reels project - a Python video generator for English reading practice reels. Covers: video generation pipeline (script, segment, timing, background, TTS, render, upload), CEFR levels A1-C1, ffmpeg/Pillow rendering, TikTok automation, NVIDIA NIM prompts, offline fallback content, Telegram bot, Docker deployment, GitHub Actions CI/CD.
---

# reading_reels - Video Generator Project

## Project Overview
مولد فيديوهات قراءة إنجليزية تفاعلية بتقنية TikTok scroll. يعمل بدون إنترنت للوظائف الأساسية، ويدعم API مجانية للجودة العالية.

## Quick Commands

```powershell
# توليد فيديو واحد
python -m app.main one --level A1 --topic travel

# توليد مجموعة فيديوهات
python -m app.main batch --level B1 --count 5 --topic nature

# تشغيل بوت تيليجرام
python telegram_bot/bot.py
```

## Pipeline Flow
1. **script_generator.py** → NVIDIA NIM API (أو fallback offline) → JSON script
2. **segmenter.py** → تقسيم النص لأسطر حسب max_words_per_line
3. **timing.py** → حساب توقيت كل سطر (WPM لكل مستوى CEFR)
4. **background.py** → Pexels → Pixabay → Gradient fallback (بدون إنترنت)
5. **tts.py** → gTTS → pyttsx3 → Silent (تسلسل fallback)
6. **render.py** → Pillow + ffmpeg → فيديو 1080×1920
7. **metadata.py** → caption + hashtags + filename
8. **uploader.py** → TikTok (Selenium أو API)

## Key Files
- `app/main.py` - CLI entry point (argparse)
- `config/config.yaml` - إعدادات الفيديو الأساسية
- `config/levels.yaml` - معايير CEFR (A1-C1)
- `prompts/reading_prompts.py` - قوالب NVIDIA NIM
- `render/renderer.py` - محرك التوليف
- `content/fallback_bank.py` - محتوى احتياطي بدون إنترنت

## Free API Keys (اختياري)
- **NVIDIA NIM**: مجاني تماماً مع signup
- **Pexels/Pixabay**: مجاني للصور/الفيديو
- **Telegram Bot**: @BotFather → مجاني
