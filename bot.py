#!/usr/bin/env python3
"""
Telegram Auto-Post Bot — Railway Edition
Runs 24/7 and posts at scheduled times every day.
"""

import json
import random
import logging
import subprocess
import requests
import schedule
import time
from pathlib import Path
from datetime import datetime

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
STATE_FILE  = BASE_DIR / "state.json"
MEDIA_DIR   = BASE_DIR / "media"

# ── Media extensions ───────────────────────────────────────────────────────────
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv"}
ALL_EXTS   = IMAGE_EXTS | VIDEO_EXTS

# ── Post times (24h format) ────────────────────────────────────────────────────
POST_TIMES = ["11:55", "14:00", "17:30", "20:00", "22:30"]


def load_config() -> dict:
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"posted": [], "last_post": None}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_media_files() -> list:
    if not MEDIA_DIR.exists():
        MEDIA_DIR.mkdir()
    files = [f for f in MEDIA_DIR.iterdir() if f.suffix.lower() in ALL_EXTS]
    return sorted(files)


def pick_next_file(files: list, state: dict, mode: str):
    if not files:
        return None
    if mode == "sequential":
        for f in files:
            if f.name not in state["posted"]:
                return f
        log.info("All media posted. Resetting cycle.")
        state["posted"] = []
        save_state(state)
        return files[0]
    elif mode == "random":
        unposted = [f for f in files if f.name not in state["posted"]]
        if not unposted:
            log.info("All media posted (random). Resetting cycle.")
            state["posted"] = []
            save_state(state)
            unposted = files
        return random.choice(unposted)
    return files[0]


def get_video_dimensions(file_path: Path):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            str(file_path)
        ], capture_output=True, text=True, timeout=10)
        parts = result.stdout.strip().split(",")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except Exception:
        pass
    return None, None


def send_media(token: str, chat_id: str, file_path: Path, caption: str) -> bool:
    ext = file_path.suffix.lower()
    base_url = f"https://api.telegram.org/bot{token}"

    reply_markup = json.dumps({
        "inline_keyboard": [[
            {
                "text": "点击观看更加精彩",
                "url": "https://d1gxij0kbua97p.cloudfront.net/?parent_icode=1411059883"
            }
        ]]
    })

    with open(file_path, "rb") as media_file:
        if ext in IMAGE_EXTS and ext != ".gif":
            endpoint = f"{base_url}/sendPhoto"
            files    = {"photo": media_file}
            data     = {"chat_id": chat_id, "reply_markup": reply_markup}
        else:
            endpoint = f"{base_url}/sendVideo"
            files    = {"video": media_file}
            w, h = get_video_dimensions(file_path)
            data = {
                "chat_id": chat_id,
                "reply_markup": reply_markup,
                "supports_streaming": "true"
            }
            if w and h:
                data["width"]  = w
                data["height"] = h

        if caption:
            data["caption"]    = caption
            data["parse_mode"] = "HTML"

        response = requests.post(endpoint, data=data, files=files, timeout=60)

    if response.status_code == 200:
        log.info(f"✅ Posted: {file_path.name}")
        return True
    else:
        log.error(f"❌ Failed: {response.text}")
        return False


def job():
    log.info("── Running post job ──")
    try:
        config = load_config()
    except Exception as e:
        log.error(str(e))
        return

    token            = config["bot_token"]
    chat_id          = config["channel_id"]
    mode             = config.get("post_mode", "sequential")
    caption          = config.get("caption", "")

    files = get_media_files()
    if not files:
        log.warning("No media files found.")
        return

    state        = load_state()
    file_to_post = pick_next_file(files, state, mode)
    if not file_to_post:
        return

    success = send_media(token, chat_id, file_to_post, caption)
    if success:
        state["posted"].append(file_to_post.name)
        state["last_post"] = datetime.now().isoformat()
        save_state(state)


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
