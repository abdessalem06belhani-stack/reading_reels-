# GitHub Actions Setup Guide

This guide helps you configure the enhanced GitHub Actions workflow for video generation with Telegram integration.

## Prerequisites

1. **GitHub Repository** — Your project must be pushed to GitHub
2. **Telegram Bot Token** — Create a bot via [@BotFather](https://t.me/botfather) on Telegram
3. **Telegram Chat/Channel ID** — Your personal chat or channel ID where videos will be sent
4. **API Keys** — NVIDIA NIM, Pexels, Pixabay (optional but recommended)

---

## Step 1: Get Your Telegram Credentials

### Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` then `/newbot`
3. Follow the prompts:
   - Bot name: e.g., "Reading Reels Generator"
   - Bot username: e.g., "reading_reels_bot"
4. **Copy the Bot Token** — It looks like: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`

### Get Your Chat ID

1. Send a message to your new bot
2. Visit this URL in your browser (replace `{TOKEN}` with your bot token):
   ```
   https://api.telegram.org/bot{TOKEN}/getUpdates
   ```
3. Look for `"chat":{"id":{YOUR_CHAT_ID}}` — that's your Chat ID (e.g., `-1002141621308`)

### For Channel IDs

If sending to a channel:
1. Add your bot as an admin to the channel
2. Send a test message in the channel
3. Check `getUpdates` for the channel chat ID (usually negative, like `-1002141621308`)

---

## Step 2: Add GitHub Secrets

1. Go to **GitHub Repository Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add these:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456789:ABCdefGHIjklmnoPQRstuvWXYZ` |
| `TELEGRAM_CHAT_ID` | Your chat/channel ID | `-1002141621308` |
| `NVIDIA_API_KEY` | NVIDIA NIM API key (optional) | `nvapi-...` |
| `PEXELS_API_KEY` | Pexels API key (optional) | `563492ad6f91...` |
| `PIXABAY_API_KEY` | Pixabay API key (optional) | `12345678-...` |

**Test the secrets:**
```bash
# After adding secrets, GitHub Actions will have access to them
# They won't be logged or exposed in workflow output
```

---

## Step 3: GitHub Actions Workflow Inputs Explained

When you manually trigger the workflow via **Actions** → **generate-reading-videos** → **Run workflow**, you'll see these input fields:

### Video Content
- **Level** (A1–C1): CEFR proficiency level
- **Topic**: Custom topic (leave blank for random)
- **Count**: Number of videos (1, 2, 3, 5, or 10)
- **Duration**: Target video length in seconds (60–180)
- **Seed**: Optional random seed for reproducibility

### Text Styling
- **Text Font**: DejaVuSans, DejaVuSans-Bold, Courier, or Arial
- **Text Size Intro**: Intro text size (60–120 px)
- **Text Size Body**: Body text size (40–90 px)
- **Text Color**: Hex color for text (e.g., `#FFFFFF` for white, `#FF0000` for red)
- **Text Stroke Width**: Outline thickness (1–5 px)
- **Text Scroll Speed**: Animation speed (0.5–3x, default 1.0)

### Background
- **Background Source**: auto (Pexels/Pixabay), pexels, or pixabay
- **Mood Override**: Custom background query (e.g., "cozy morning", "beach sunset")

### Audio & Narration
- **Enable Narration**: Include full-text TTS (yes/no)
- **TTS Speed**: Narration speed (0.8–1.5x, default 1.0)
- **Background Music**: Include background music (yes/no)
- **Music Gain**: Background music volume (−30 to −10 dB, default −22 dB)

### Metadata & Publishing
- **Title Override**: Custom video title (leave blank to auto-generate)
- **Caption Override**: Custom TikTok caption (leave blank to auto-generate)
- **Hashtags Override**: Comma-separated hashtags (e.g., `#EnglishLearning,#Reading,#ESL`)
- **Auto Upload TikTok**: Post to TikTok immediately (requires account setup)

### Telegram & Delivery
- **Send Telegram**: Send generated videos to Telegram (yes/no) — **Enable this!**
- **Telegram Chat Override**: Alternative Telegram chat ID (leave blank to use secret)

---

## Step 4: Trigger Your First Workflow

1. Go to **GitHub** → **Actions** tab
2. Click **generate-reading-videos** (left sidebar)
3. Click **Run workflow** (top right)
4. Fill in the inputs:
   - **Level**: B1
   - **Topic**: "morning routine"
   - **Count**: 1
   - **Send Telegram**: ✅ Yes
   - Leave others as default
5. Click **Run workflow**

### Monitor Execution

- Workflow will take **5–15 minutes** depending on:
  - Video duration (longer = more rendering time)
  - API key availability (NVIDIA NIM faster than local fallback)
  - GitHub Actions queue

- Click on the workflow run to see logs:
  - **Doctor check** — Environment validation
  - **Generate videos** — Script, timing, background, TTS, rendering
  - **Send to Telegram** — Video delivery status
  - **Upload artifacts** — Backup video files

### Check Results

- Video appears in your **Telegram chat** with:
  - Title + Level (e.g., "Morning Routine | Level: B1")
  - Caption + Hashtags
  - MP4 file ready to download

---

## Step 5: Advanced Examples

### Example 1: High-Quality Long Video

```
Level: B2
Topic: "a day in my life"
Count: 1
Duration: 150
Text Font: DejaVuSans-Bold
Text Color: #00FF00 (green)
Text Scroll Speed: 0.8 (slower)
Enable Narration: Yes
Background Music: Yes
Music Gain: -18
Send Telegram: Yes
```

### Example 2: Batch Generation with Custom Styling

```
Level: A2
Count: 5
Text Color: #FFFF00 (yellow)
Text Size Intro: 100
Text Size Body: 70
Enable Narration: No (only music)
Send Telegram: Yes
```

### Example 3: Cinematic with Long Duration

```
Level: B1
Duration: 180
Text Font: Courier
Text Stroke Width: 3
Background Source: pexels
Mood Override: "peaceful mountains at sunset"
Enable Narration: Yes
TTS Speed: 0.9 (slower speech)
Send Telegram: Yes
```

---

## Step 6: Scheduled Automatic Generation

The workflow also runs **daily at 7 AM UTC** (configured in `cron: "0 7 * * *"`):
- Uses **per-account settings** from `config/accounts.yaml`
- Videos are **NOT** automatically sent to Telegram by default (cron trigger)
- To enable cron→Telegram: Edit `.github/workflows/generate.yml` and modify the `if:` condition

---

## Troubleshooting

### Workflow Fails with "TELEGRAM_BOT_TOKEN not set"
✅ **Fix:** Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` secrets to GitHub Actions (see Step 2)

### Video Generated but NOT Sent to Telegram
✅ **Fix:** Check that **"Send Telegram"** input was set to `Yes` in the workflow run

### Video File Too Large
✅ **Fix:** Reduce video duration or increase CRF quality setting:
- Edit `config/config.yaml` → `video.crf` (increase from 20 to 26)

### "Unknown level 'X'" Error
✅ **Fix:** Use one of: A1, A2, B1, B2, C1

### API Key Errors (NVIDIA/Pexels/Pixabay)
✅ **Fix:** Add missing API keys to GitHub secrets, or workflow will use fallback (local content bank + gradient backgrounds)

### Chat ID Invalid Error
✅ **Fix:** Verify chat ID format:
- Personal chat: `-1002141621308` (11 digits, starts with -100)
- Or use positive chat ID if available

---

## Customization Options

### Change Default Telegram Chat

Edit `.github/workflows/generate.yml`:
```yaml
- name: Send to Telegram
  env:
    TELEGRAM_CHAT_ID: ${{ inputs.telegram_chat_override || secrets.TELEGRAM_CHAT_ID }}
    # To use a different default, replace with:
    TELEGRAM_CHAT_ID: "-1234567890"  # hardcoded fallback
```

### Disable Cron Trigger

Edit `.github/workflows/generate.yml`:
```yaml
on:
  workflow_dispatch:
    inputs: ...
  # schedule:
  #   - cron: "0 7 * * *"  # Commented out to disable
```

### Always Send to Telegram (Even on Cron)

Edit `.github/workflows/generate.yml`:
```yaml
- name: Send to Telegram
  # Remove the "if:" condition to always send
  env:
    ...
```

---

## File Locations

- **Workflow file:** [.github/workflows/generate.yml](.github/workflows/generate.yml)
- **CLI tool:** [app/main.py](app/main.py)
- **Telegram sender:** [telegram_sender.py](telegram_sender.py)
- **Config overrides:** [app/config_loader.py](app/config_loader.py)
- **Pipeline:** [app/pipeline.py](app/pipeline.py)

---

## Next Steps

1. ✅ Set up Telegram bot & get credentials (Step 1)
2. ✅ Add GitHub secrets (Step 2)
3. ✅ Review workflow inputs (Step 3)
4. ✅ Trigger first workflow run (Step 4)
5. ✅ Try advanced examples (Step 5)
6. ✅ Set up auto-generation schedule (Step 6)

**Questions?** Check the main [README.md](../README.md) or [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
