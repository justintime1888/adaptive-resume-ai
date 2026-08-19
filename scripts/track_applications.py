#!/usr/bin/env python3
"""
Job Application Pipeline & CSV Sync Utility
Scans application notes in applications/ and exports structured jobs_tracker.csv.
"""

import os
import re
import csv
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
APPS_DIR = REPO_ROOT / "applications"
CSV_FILE = APPS_DIR / "jobs_tracker.csv"

def sync_applications_to_csv():
    rows = [["Company", "Role", "Status", "Date Applied", "Match Score", "Location", "Job URL"]]
    
    files = list(APPS_DIR.glob("*.md"))
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            if "career/application" not in content:
                continue

            def get_field(name):
                m = re.search(rf'{name}:\s*["\']?(.*?)["\']?\n', content)
                return m.group(1).strip() if m else ""

            comp = get_field("company") or f.stem.split(" - ")[0]
            role = get_field("role") or "Candidate"
            stat = get_field("status") or "Applied"
            date = get_field("applied_date") or ""
            score = get_field("match_score") or ""
            loc = get_field("location") or ""
            url = get_field("job_url") or ""

            rows.append([comp, role, stat, date, score, loc, url])
        except Exception:
            continue

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)

    print(f"[✓] Synced {len(rows)-1} applications to CSV: {CSV_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track applications & sync CSV.")
    parser.add_argument("--sync", action="store_true", help="Sync markdown application notes to CSV")
    args = parser.parse_args()
    sync_applications_to_csv()