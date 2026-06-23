"""
Agent: auto-upload a finished video to TikTok.

Two methods (configurable in config/config.yaml -> upload.method):

  "web"  (default, no developer approval needed)
        Drives a real Chrome window with Selenium using a PERSISTENT profile,
        so you log in to TikTok ONCE and every later upload is automatic.
        Best for a single creator on their own Windows 10 machine.

  "api"  (official TikTok Content Posting API – Direct Post)
        Uses an access token (scope: video.publish) from an approved TikTok
        developer app. Most robust/compliant, but needs app review.

⚠️  IMPORTANT / HONEST NOTES
  • The web method automates your own logged-in session. TikTok's page layout
    changes often, so selectors are in config (upload.web.selectors) and easy to
    update. Use responsibly and at a human pace to keep your account safe.
  • Selenium + Google Chrome must be installed (see docs/UPLOAD_TIKTOK.md).
  • All imports are lazy, so the rest of the tool works even without Selenium.
"""
from __future__ import annotations
import os, time
from pathlib import Path
from typing import Dict, Optional
from app.utils import get_logger

log = get_logger()


class TikTokUploader:
    def __init__(self, cfg):
        self.cfg = cfg
        self.u = cfg.get("upload", default={}) or {}

    # ------------------------------------------------------------------
    def upload(self, video_path: str, caption: str, job_dir: Optional[str] = None) -> Dict:
        method = (self.u.get("method") or "web").lower()
        log.info("uploading to TikTok via '%s' method ...", method)
        if method == "api":
            return self.upload_api(video_path, caption)
        return self.upload_web(video_path, caption, job_dir=job_dir)

    # ============================ WEB =================================
    def upload_web(self, video_path: str, caption: str, job_dir: Optional[str] = None) -> Dict:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.keys import Keys
        except Exception as e:
            raise RuntimeError(
                "Selenium is not installed. Run:  pip install selenium\n"
                "and make sure Google Chrome is installed."
            ) from e

        web = self.u.get("web", {}) or {}
        sel = web.get("selectors", {}) or {}
        profile_dir = self.cfg.abspath(web.get("chrome_profile_dir", "assets/chrome_profile"))
        profile_dir.mkdir(parents=True, exist_ok=True)
        upload_url = web.get("upload_url", "https://www.tiktok.com/tiktokstudio/upload")
        wait_secs = int(web.get("post_button_timeout", 180))
        headless = bool(web.get("headless", False))

        opts = Options()
        opts.add_argument(f"--user-data-dir={profile_dir}")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--start-maximized")
        if headless:
            opts.add_argument("--headless=new")

        driver = webdriver.Chrome(options=opts)
        try:
            driver.get(upload_url)
            wait = WebDriverWait(driver, wait_secs)

            # If not logged in, pause for a one-time manual login.
            if "login" in driver.current_url or self._needs_login(driver, By):
                print("\n" + "=" * 64)
                print(" TikTok login required. A Chrome window is open.")
                print(" 1) Log in to your TikTok account in that window.")
                print(" 2) When you can see the Upload page, come back here")
                print("    and press ENTER to continue the automatic upload.")
                print("=" * 64)
                try:
                    input(" Press ENTER once you are logged in... ")
                except EOFError:
                    time.sleep(45)
                driver.get(upload_url)

            # 1) file input (often inside an iframe on the studio page)
            self._maybe_switch_iframe(driver, By)
            file_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, sel.get("file_input", "input[type='file']"))))
            file_input.send_keys(str(Path(video_path).resolve()))
            log.info("video selected, waiting for TikTok to process it ...")

            # 2) caption editor (contenteditable). Clear prefilled text, type caption.
            cap_sel = sel.get("caption", "div[contenteditable='true']")
            editor = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, cap_sel)))
            time.sleep(3)
            editor.click()
            editor.send_keys(Keys.CONTROL, "a")
            editor.send_keys(Keys.DELETE)
            for chunk in caption.split("\n"):
                editor.send_keys(chunk)
                editor.send_keys(Keys.SHIFT, Keys.ENTER)
            log.info("caption written")

            # 3) wait until the Post button is enabled (i.e. upload finished)
            post_xpath = sel.get("post_button_xpath",
                                 "//button[.//div[contains(., 'Post')] or contains(., 'Post')]")
            post_btn = wait.until(EC.element_to_be_clickable((By.XPATH, post_xpath)))
            time.sleep(2)
            post_btn.click()
            log.info("clicked Post — finalizing ...")
            time.sleep(int(web.get("post_finalize_wait", 12)))

            shot = None
            if job_dir:
                shot = str(Path(job_dir) / "upload_result.png")
                try:
                    driver.save_screenshot(shot)
                except Exception:
                    shot = None
            return {"status": "submitted", "method": "web", "screenshot": shot}
        except Exception as e:
            if job_dir:
                try:
                    driver.save_screenshot(str(Path(job_dir) / "upload_error.png"))
                except Exception:
                    pass
            raise RuntimeError(f"web upload failed: {e}") from e
        finally:
            if not bool(web.get("keep_browser_open", False)):
                time.sleep(3)
                driver.quit()

    def _needs_login(self, driver, By) -> bool:
        try:
            driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            return False
        except Exception:
            return True

    def _maybe_switch_iframe(self, driver, By):
        try:
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            for fr in frames:
                driver.switch_to.frame(fr)
                if driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
                    return
                driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()

    # ============================ API =================================
    def upload_api(self, video_path: str, caption: str) -> Dict:
        import requests
        api = self.u.get("api", {}) or {}
        token = os.getenv(api.get("access_token_env", "TIKTOK_ACCESS_TOKEN"), "").strip()
        if not token:
            raise RuntimeError(
                "No TikTok access token. Set the env var named in "
                "config.upload.api.access_token_env (default TIKTOK_ACCESS_TOKEN). "
                "Requires an approved developer app with scope video.publish.")
        privacy = api.get("privacy_level", "SELF_ONLY")
        size = os.path.getsize(video_path)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        init = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            headers=headers,
            json={"post_info": {"title": caption[:2200], "privacy_level": privacy,
                                "disable_comment": False, "disable_duet": False,
                                "disable_stitch": False},
                  "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                  "chunk_size": size, "total_chunk_count": 1}},
            timeout=60)
        init.raise_for_status()
        data = init.json().get("data", {})
        publish_id, upload_url = data.get("publish_id"), data.get("upload_url")
        if not upload_url:
            raise RuntimeError(f"init failed: {init.text}")
        with open(video_path, "rb") as f:
            put = requests.put(
                upload_url, data=f.read(), timeout=600,
                headers={"Content-Type": "video/mp4",
                         "Content-Range": f"bytes 0-{size-1}/{size}"})
        put.raise_for_status()
        log.info("API upload sent (publish_id=%s)", publish_id)
        return {"status": "submitted", "method": "api", "publish_id": publish_id}
