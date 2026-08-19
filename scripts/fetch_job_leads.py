#!/usr/bin/env python3
"""
Job Postings & ATS Lead Fetcher
Fetches and structures job postings from raw text, files, or direct URLs.
"""

import re
import argparse
from pathlib import Path

def parse_job_text(raw_text: str) -> dict:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    title = lines[0] if lines else "Target Position"
    return {
        "title": title,
        "description": raw_text,
        "word_count": len(raw_text.split())
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and parse job descriptions.")
    parser.add_argument("--text", type=str, help="Job description text")
    parser.add_argument("--file", type=str, help="Path to job description file")
    args = parser.parse_args()

    content = args.text or ""
    if args.file and Path(args.file).exists():
        content = Path(args.file).read_text(encoding="utf-8")

    if content:
        res = parse_job_text(content)
        print(f"[✓] Parsed Job: {res['title']} ({res['word_count']} words)")
    else:
        print("[!] Provide --text or --file to parse.")