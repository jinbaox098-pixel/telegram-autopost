#!/usr/bin/env python3
"""
Telegram Auto-Post Bot — Railway Edition
Downloads video from Google Drive and posts to Telegram on schedule.
"""

import json
import logging
import requests
import schedule
import time
from datetime import datetime

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
BOT_TOKEN    = "8540608510:AAG_Y33NDGpj8WbPeuEOzOGlOpyXSHliB8g"
CHANNEL_ID   = "@yanxuuu0"
GDRIVE_ID    = "1mpwCJ0YhzEx_fDTY6jiZI8FhYcH8sQes"
BUTTON_TEXT  = "点击观看更加精彩"
BUTTON_URL   = "https://d1gxij0kbua97p.cloudfront.net/?parent_icode=1411059883"

# ── Post times (24h format) ────────────────────────────────────────────────────
POST_TIMES = ["11:55", "14:00", "15:40", "20:00", "22:30"]


def download_from_gdrive(file_id: str) -> bytes:
    """Download a file from Google Drive by file ID."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    session = requests.Session()
    response = session.get(url, stream=True)

    # Handle Google's virus scan warning for large files
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={value}"
            response = session.get(url, stream=True)
            break

    content = b""
    for chunk in response.iter_content(chunk_size=32768):
        if chunk:
            content += chunk

    log.info(f"Downloaded {len(content) / 1024 / 1024:.1f} MB from Google Drive")
    return content


def send_video(video_bytes: bytes) -> bool:
    """Send video to Telegram channel with inline button."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"

    reply_markup = json.dumps({
        "inline_keyboard": [[
            {"text": BUTTON_TEXT, "url": BUTTON_URL}
        ]]
    })

    files = {"video": ("video.mp4", video_bytes, "video/mp4")}
    data  = {
        "chat_id": CHANNEL_ID,
        "reply_markup": reply_markup,
        "supports_streaming": "true"
    }

    response = requests.post(url, data=data, files=files, timeout=120)

    if response.status_code == 200:
        log.info("✅ Video posted successfully!")
        return True
    else:
        log.error(f"❌ Failed: {response.text}")
        return False


def job():
    log.info(f"── Running post job at {datetime.now().strftime('%H:%M')} ──")
    try:
        log.info("Downloading video from Google Drive...")
        video_bytes = download_from_gdrive(GDRIVE_ID)
        send_video(video_bytes)
    except Exception as e:
        log.error(f"Error: {e}")


def main():
    log.info("🚀 Bot started! Scheduling posts...")

    for t in POST_TIMES:
        schedule.every().day.at(t).do(job)
        log.info(f"  ⏰ Scheduled at {t}")

    log.info("✅ Bot is running 24/7. Waiting for scheduled times...")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
