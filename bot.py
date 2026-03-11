#!/usr/bin/env python3
"""
Telegram Auto-Post Bot — Railway Edition
Runs 24/7 and posts at scheduled times every day (GMT+7 timezone).
"""

import json
import logging
import requests
import time
from datetime import datetime, timezone, timedelta

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
BOT_TOKEN   = "8540608510:AAG_Y33NDGpj8WbPeuEOzOGlOpyXSHliB8g"
CHANNEL_ID  = ["@yanxuuu0", "@mrm18jingnu"]
GDRIVE_ID   = "1mpwCJ0YhzEx_fDTY6jiZI8FhYcH8sQes"
BUTTON_TEXT = "点击观看更加精彩"
BUTTON_URL  = "https://d1gxij0kbua97p.cloudfront.net/?parent_icode=1411059883"

# ── Timezone GMT+7 ─────────────────────────────────────────────────────────────
GMT7 = timezone(timedelta(hours=7))

# ── Post times in YOUR local time GMT+7 (HH:MM) ───────────────────────────────
POST_TIMES = ["11:55", "14:00", "16:27", "20:00", "22:30"]


def download_from_gdrive(file_id: str) -> bytes:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    session = requests.Session()
    response = session.get(url, stream=True)

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


def send_video(video_bytes: bytes, channel: str) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"

    reply_markup = json.dumps({
        "inline_keyboard": [[
            {"text": BUTTON_TEXT, "url": BUTTON_URL}
        ]]
    })

    files = {"video": ("video.mp4", video_bytes, "video/mp4")}
    data  = {
        "chat_id": channel,
        "reply_markup": reply_markup,
        "supports_streaming": "true",
        "width": 1080,
        "height": 1602
    }

    response = requests.post(url, data=data, files=files, timeout=120)

    if response.status_code == 200:
        log.info("✅ Video posted successfully!")
        return True
    else:
        log.error(f"❌ Failed: {response.text}")
        return False


def job():
    now = datetime.now(GMT7).strftime("%H:%M")
    log.info(f"── Running post job at {now} GMT+7 ──")
    try:
        log.info("Downloading video from Google Drive...")
        video_bytes = download_from_gdrive(GDRIVE_ID)
        for channel in CHANNEL_ID:
            log.info(f"Posting to {channel}...")
            send_video(video_bytes, channel)
    except Exception as e:
        log.error(f"Error: {e}")


LAST_POST_FILE = "/tmp/last_post.txt"

def get_last_posted() -> str:
    try:
        with open(LAST_POST_FILE) as f:
            return f.read().strip()
    except:
        return ""

def save_last_posted(val: str):
    with open(LAST_POST_FILE, "w") as f:
        f.write(val)


def main():
    log.info("🚀 Bot started!")
    for t in POST_TIMES:
        log.info(f"  ⏰ Scheduled at {t} GMT+7")
    log.info("✅ Bot is running 24/7. Waiting for scheduled times...")

    while True:
        now = datetime.now(GMT7).strftime("%H:%M")
        today = datetime.now(GMT7).strftime("%Y-%m-%d")
        last_posted = get_last_posted()
        key = f"{today}_{now}"

        if now in POST_TIMES and last_posted != key:
            save_last_posted(key)
            job()
            time.sleep(61)
        time.sleep(20)


if __name__ == "__main__":
    main()
