# Auto-Upload to TikTok

Two methods. Pick one in `config/config.yaml` under `upload.method`.

> **Honest note on safety:** TikTok has no open public upload API for personal accounts.
> The **web** method automates *your own* logged-in browser session; TikTok's page can
> change, so the CSS/XPath selectors live in `config/config.yaml` and are easy to update.
> Post at a human pace. The **api** method is fully compliant but needs an approved app.

---

## Method 1 — Web (browser automation) — recommended for a solo creator on Windows 10

**Requirements:** Google Chrome installed + `pip install selenium` (already in
`requirements.txt`). Selenium 4 auto-manages the Chrome driver.

**Enable it:**
```yaml
# config/config.yaml
upload:
  enabled: true        # or just pass --auto-upload on the CLI
  method: "web"
  web:
    chrome_profile_dir: "assets/chrome_profile"   # you log in here ONCE
    headless: false                               # keep false
```

**First run (one-time login):**
```bash
python -m app.main one --level B1 --auto-upload
```
1. A Chrome window opens at the TikTok upload page using a **persistent profile**.
2. If you're not logged in, the terminal pauses: **log in to TikTok in that window**,
   then return to the terminal and press **ENTER**.
3. The tool selects the rendered `.mp4`, types the caption from `caption.txt`, waits for
   processing, and clicks **Post**. A screenshot `upload_result.png` is saved in the job
   folder.

Every later run reuses the saved login, so uploads are fully automatic.

**Upload an already-made video:**
```bash
python -m app.main upload --video "outputs/jobs/XXXX/video.mp4" --caption-file "outputs/jobs/XXXX/caption.txt"
```

**If TikTok changes its UI** and a step fails, update the selectors:
```yaml
upload:
  web:
    selectors:
      file_input: "input[type='file']"
      caption: "div[contenteditable='true']"
      post_button_xpath: "//button[.//div[contains(., 'Post')] or contains(., 'Post')]"
```
On failure, an `upload_error.png` screenshot is saved in the job folder to help you find
the right selector (right-click the element in Chrome → Inspect).

**Tips**
- Keep `headless: false` — TikTok blocks most headless uploads.
- Set `keep_browser_open: true` while debugging selectors.
- Don't mass-post unrealistically fast; space uploads out.

---

## Method 2 — Official Content Posting API (compliant, needs app review)

1. Create an app at **https://developers.tiktok.com/** and request the
   **Content Posting API** with scope **`video.publish`**.
2. Complete OAuth to obtain an **access token** for your account.
3. Put the token in `.env`:
   ```
   TIKTOK_ACCESS_TOKEN=your_access_token
   ```
4. Configure:
   ```yaml
   upload:
     enabled: true
     method: "api"
     api:
       access_token_env: "TIKTOK_ACCESS_TOKEN"
       privacy_level: "SELF_ONLY"   # required until your app is audited; then PUBLIC_TO_EVERYONE
   ```
5. Run with `--auto-upload`. The tool calls
   `…/v2/post/publish/video/init/` then uploads the file (Direct Post / FILE_UPLOAD).

**Notes**
- Unaudited apps can only post as `SELF_ONLY` (private). After TikTok audits your app you
  may use `PUBLIC_TO_EVERYONE`.
- Tokens expire — refresh them per TikTok's OAuth docs.

---

## Which should I use?
| | Web | API |
|---|-----|-----|
| Setup effort | low (just log in once) | high (app review) |
| Compliance | uses your own session | fully official |
| Stability | breaks if UI changes | stable |
| Best for | one creator, Windows 10 | businesses / scale |
