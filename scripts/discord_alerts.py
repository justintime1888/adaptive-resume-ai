#!/usr/bin/env python3
"""
Discord Webhook Notification Dispatcher
Sends rich embeds for tailored resumes, application status updates, interview prep packets,
and adaptive learning breakthroughs.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

load_dotenv(dotenv_path=REPO_ROOT / ".env")
load_dotenv(dotenv_path=SCRIPT_DIR / ".env")

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

def send_embed(embed: dict, file_path: Path = None):
    if not WEBHOOK_URL:
        return
    payload = {"username": "Career AI Copilot", "embeds": [embed]}
    try:
        if file_path and file_path.exists() and file_path.stat().st_size > 0:
            with open(file_path, "rb") as f:
                bytes_data = f.read()
            files = {"file": (file_path.name, bytes_data, "application/octet-stream")}
            data = {"payload_json": json.dumps(payload)}
            requests.post(WEBHOOK_URL, data=data, files=files, timeout=15)
        else:
            requests.post(WEBHOOK_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
    except Exception as e:
        print(f"[!] Discord push error: {e}")

def push_tailored_resume(company: str, role: str, score: int, track: str, pdf_path: Path):
    embed = {
        "title": f"🎯 [{track}] {role} @ {company}",
        "color": 1095987, # Green
        "fields": [
            {"name": "🎯 ATS Match Score", "value": f"`{score}%`", "inline": True},
            {"name": "🧠 Resume Track", "value": f"`{track}`", "inline": True},
            {"name": "📄 Tailored PDF", "value": f"`{pdf_path.name}` (Attached below)", "inline": False}
        ],
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    send_embed(embed, pdf_path)

def push_application_update(company: str, role: str, status: str, email_subject: str = ""):
    color_map = {
        "Offer": 65280,       # Green
        "Technical": 3899894, # Blue
        "OA / Screen": 16753920, # Orange
        "Rejected": 16711680  # Red
    }
    embed = {
        "title": f"📬 Status Update: {company} — {role}",
        "color": color_map.get(status, 10070709),
        "fields": [
            {"name": "📌 Current Status", "value": f"**`{status}`**", "inline": True},
            {"name": "✉️ Email Subject", "value": f"{email_subject or 'N/A'}", "inline": False}
        ],
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    send_embed(embed)