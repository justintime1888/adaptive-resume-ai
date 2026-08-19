#!/usr/bin/env python3
"""
Google Sheets Real-Time Application Sync
Reads applications/jobs_tracker.csv and pushes live rows to Google Sheets via Webhook.
"""

import os
import csv
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CSV_FILE = REPO_ROOT / "applications" / "jobs_tracker.csv"

load_dotenv(dotenv_path=REPO_ROOT / ".env")
load_dotenv(dotenv_path=SCRIPT_DIR / ".env")

WEBHOOK_URL = os.getenv("GOOGLE_SHEETS_WEBHOOK_URL", "").strip()

def sync_to_google_sheets():
    if not CSV_FILE.exists():
        print("[-] jobs_tracker.csv not found.")
        return

    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        print("[-] No rows to sync.")
        return

    if not WEBHOOK_URL:
        print("[*] Local CSV updated (applications/jobs_tracker.csv).")
        print("    To enable live cloud sync to Google Sheets:")
        print("    1. Create a Google Sheet & paste scripts/google_sheets_apps_script.js in Extensions > Apps Script.")
        print("    2. Deploy as Web App & add GOOGLE_SHEETS_WEBHOOK_URL to .env")
        return

    print(f"[*] Pushing {len(rows)} rows to Google Sheets...")
    try:
        resp = requests.post(WEBHOOK_URL, json=rows, timeout=10)
        if resp.status_code == 200:
            print("[✓] Live Google Sheet successfully updated!")
        else:
            print(f"[!] Google Sheets sync notice (HTTP {resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"[!] Google Sheets sync error: {e}")

if __name__ == "__main__":
    sync_to_google_sheets()