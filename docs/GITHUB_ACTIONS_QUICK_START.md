# Quick Start: GitHub Actions Video Generation + Telegram

## 🚀 One-Time Setup (5 minutes)

### 1. Telegram Bot + Chat ID
```
1. Message @BotFather on Telegram → /newbot
2. Copy Bot Token: 123456789:ABCdefGHIjklmnoPQRstuvWXYZ
3. Send message to your bot, then visit:
   https://api.telegram.org/bot{TOKEN}/getUpdates
4. Copy chat ID: -1002141621308
```

### 2. GitHub Secrets
Go to **Settings** → **Secrets and variables** → **Actions** → **New secret**

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_CHAT_ID` | From getUpdates |

Optional but recommended:
| Name | Value |
|------|-------|
| `NVIDIA_API_KEY` | From NVIDIA NIM |
| `PEXELS_API_KEY` | From pexels.com/api |
| `PIXABAY_API_KEY` | From pixabay.com/api |

---

## ⚡ Generate Your First Video (1 minute)

1. Go to **GitHub Actions** → **generate-reading-videos**
2. Click **Run workflow**
3. Set:
   - **Level**: B1
   - **Count**: 1
   - **Send Telegram**: ✅ Yes
4. Leave others as default
5. Click **Run workflow**
6. Wait 5–15 minutes
7. Video appears in **Telegram** ✨

---

## 🎨 Customization Examples

### Blue Text Video
```
Text Color: #0000FF
Text Stroke Width: 3
Text Scroll Speed: 0.8
Duration: 100
```

### Fast Narration Batch (3 videos)
```
Count: 3
Enable Narration: Yes
TTS Speed: 1.2
Duration: 90
```

### Cinematic Sunset
```
Duration: 150
Background Source: pexels
Mood Override: "sunset over ocean"
Text Scroll Speed: 0.5 (very slow)
Text Font: Courier
```

---

## 📊 What Gets Passed to Telegram

Each video includes:
- **Title** + **Level** (e.g., "Morning Routine | Level: B1")
- **Caption** (from config or custom)
- **Hashtags** (from config or custom)
- **Video file** (MP4)

---

## 🔧 Environment Variables (Auto-Set by Workflow)

The workflow automatically passes these to Python:
```
GH_DURATION              → video duration (seconds)
GH_TEXT_COLOR            → #RRGGBB hex color
GH_TEXT_FONT             → font name
GH_ENABLE_NARRATION      → true/false
GH_TTS_SPEED             → 0.8–1.5x multiplier
GH_BACKGROUND_MUSIC      → true/false
GH_MUSIC_GAIN            → -30 to -10 dB
GH_BACKGROUND_SOURCE     → pexels/pixabay/auto
GH_MOOD_OVERRIDE         → custom mood query
```

These are read by `app/config_loader.py` and override default config.

---

## ✅ Features

| Feature | Supported |
|---------|-----------|
| **Video Customization** | ✅ Duration, text styling, background, audio |
| **Telegram Integration** | ✅ Auto-send to personal chat/channel |
| **Batch Generation** | ✅ Generate 1–10 videos at once |
| **Auto-Upload TikTok** | ✅ Post directly (requires account setup) |
| **Scheduled Generation** | ✅ Daily at 7 AM UTC (cron) |
| **Config Overrides** | ✅ Via GitHub Actions inputs → environment variables |
| **CLI Compatibility** | ✅ Same customization options for local CLI |

---

## 📝 Workflow Files Modified

| File | Changes |
|------|---------|
| [.github/workflows/generate.yml](.github/workflows/generate.yml) | Added 30+ input fields for customization |
| [app/config_loader.py](app/config_loader.py) | Added `_apply_github_overrides()` to read GH_* env vars |
| [app/main.py](app/main.py) | Added CLI flags: `--duration`, `--text-color`, `--tts-speed` |
| [app/pipeline.py](app/pipeline.py) | Added params: `duration`, `text_color`, `tts_speed` |
| [render/renderer.py](render/renderer.py) | Added `text_color` override parameter |
| [telegram_sender.py](telegram_sender.py) | Already supports `--bot-token` & `--chat-id` |

---

## 🐛 Troubleshooting

**"TELEGRAM_BOT_TOKEN not set"**
→ Add secrets to GitHub Actions (Settings → Secrets)

**"Video NOT sent to Telegram"**
→ Check "Send Telegram" input is set to `Yes`

**"Unknown level 'X'"**
→ Use A1, A2, B1, B2, or C1

**"Chat ID invalid"**
→ Verify format: `-1002141621308` (negative, 11 digits)

**"API key not found"**
→ Workflow uses fallback (local content bank + gradients)

---

## 📚 Full Documentation

- [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) — Detailed setup guide
- [README.md](../README.md) — Project overview
- [USAGE.md](USAGE.md) — CLI usage examples
