# GitHub Actions Setup Guide

## Step 1: Add Telegram Secrets to GitHub Repository

To enable automatic sending of generated videos to Telegram via GitHub Actions, you need to add your Telegram bot credentials as repository secrets.

### Get Your Telegram Bot Token and Chat ID

1. **Create a Telegram Bot** (if you don't have one):
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` and follow the instructions
   - You'll receive a **Bot Token** in the format: `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`

2. **Get Your Chat ID**:
   - You provided: `-2001621308` (this is your personal chat ID)
   - Chat IDs starting with `-` are group chats or channels (without the minus in the actual ID)
   - Personal chat IDs are typically negative for groups/channels

### Add Secrets to GitHub

1. Go to your GitHub repository: **Settings → Secrets and variables → Actions**

2. Click **"New repository secret"** and add these two secrets:

   | Secret Name | Value |
   |------------|-------|
   | `TELEGRAM_BOT_TOKEN` | `8759505095:AAH7d1BSTITsc5uqFH9cNZHWY-G_RxnRqzA` |
   | `TELEGRAM_CHAT_ID` | `-2001621308` |

3. Verify both secrets appear in the list with ✓ status

---

## Step 2: Verify Telegram Bot Permissions

Make sure your bot:
1. Has permission to send messages to the target chat/channel
2. For channels: Has admin rights and can post in the channel

To test manually (before GitHub Actions):
```bash
python telegram_sender.py \
  --file "path/to/video.mp4" \
  --caption "Test video" \
  --bot-token "8759505095:AAH7d1BSTITsc5uqFH9cNZHWY-G_RxnRqzA" \
  --chat-id "-2001621308"
```

---

## Step 3: Use the Enhanced Generate Workflow

### Option A: Manual Dispatch (Recommended for Testing)

1. Go to **Actions → generate-reading-videos → Run workflow**
2. Configure these parameters:
   - **CEFR Level**: B1 (or A1-C1)
   - **Topic**: (optional, leave blank for random)
   - **Number of videos**: 1
   - **Target video duration**: 120 (seconds, 60-180)
   - **Text color**: #FFFFFF (hex format)
   - **Enable narration**: ✓ (checked)
   - **Background music**: ✓ (checked)
   - **Send result to Telegram**: ✓ (checked)
   - **Telegram chat ID override**: (leave blank to use secret)

3. Click **"Run workflow"**

4. Monitor the run in the **Actions** tab

5. Check your Telegram chat for the video!

### Option B: Scheduled Generation (Daily)

The workflow is configured to run daily at **7:00 AM UTC** with default settings:
- Level: Random
- Topic: Random (per account if using accounts.yaml)
- Batch size: Per account config
- Send to Telegram: Yes

To modify the schedule, edit `.github/workflows/generate.yml` and change the cron:
```yaml
schedule:
  - cron: "0 7 * * *"   # 7 AM UTC daily
```

---

## Advanced: Customization Examples

### Example 1: Generate with Custom Text Color

```
Level: A2
Topic: morning routine
Duration: 90
Text color: #FF0000 (red)
Text size intro: 100
Enable narration: Yes
Auto-upload TikTok: No
Send Telegram: Yes
```

### Example 2: Generate Batch for Different Levels

Run the workflow multiple times with different levels:
1. **Run 1:** Level=A1, Count=2 → 2 beginner videos
2. **Run 2:** Level=B1, Count=2 → 2 intermediate videos
3. **Run 3:** Level=C1, Count=1 → 1 advanced video

All videos will be sent to Telegram.

### Example 3: Generate + Auto-Upload to TikTok

```
Level: B1
Topic: studying tips
Auto-upload TikTok: Yes (requires account setup in config/accounts.yaml)
Send Telegram: Yes
```

---

## Troubleshooting

### Issue: "Telegram send failed"

**Possible causes:**
1. `TELEGRAM_BOT_TOKEN` secret not set correctly
2. `TELEGRAM_CHAT_ID` secret is wrong or user blocked the bot
3. Chat ID format is incorrect (should include the `-` for groups)

**Solution:**
- Verify secrets in GitHub Settings
- Test the bot locally: `python telegram_sender.py --file test.mp4 --bot-token "..." --chat-id "..."`

### Issue: "Video too large for Telegram"

Telegram has a file size limit (~2GB, but practical limit ~100MB). If your video is too large:
- Reduce duration (lower target in workflow inputs)
- Increase CRF quality value (trades quality for size) in `config/config.yaml`

### Issue: "Workflow failed - ffmpeg not found"

The GitHub Actions runner doesn't have ffmpeg. This shouldn't happen since the workflow installs it:
```yaml
sudo apt-get install -y ffmpeg espeak-ng
```

Check the workflow logs for the actual error.

---

## Configuration Files Reference

After the first successful run, you can customize behavior:

- **`config/config.yaml`**: Default video parameters (dimensions, quality, text styling, etc.)
- **`config/levels.yaml`**: CEFR level specifications (A1-C1)
- **`config/topics.yaml`**: Topic families and mood queries
- **`config/accounts.yaml`**: Multi-account generation config

See [SETUP.md](SETUP.md) for full configuration details.

---

## Next Steps

1. ✅ Add secrets to GitHub
2. ✅ Test manual workflow dispatch
3. ✅ Monitor first run in Telegram
4. (Optional) Enable scheduled daily generation
5. (Optional) Set up TikTok auto-upload with account credentials

---

## More Help

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- Check the workflow logs: **Actions → [Run] → [Step]** for detailed error messages
