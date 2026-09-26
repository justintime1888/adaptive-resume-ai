#!/usr/bin/env python3
"""
Job Postings & ATS Lead Fetcher
Fetches and structures job postings from raw text, files, direct URLs, and Handshake.
"""

import os
import sys
import re
import time
import base64
import zlib
import urllib.parse
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import argparse
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

VAULT_ENV = Path(r"C:\Users\jstnp\Documents\obsidianvault\scripts\.env")

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=REPO_ROOT / ".env")
    load_dotenv(dotenv_path=SCRIPT_DIR / ".env")
    if VAULT_ENV.exists():
        load_dotenv(dotenv_path=VAULT_ENV)
except ImportError:
    for env_path in [REPO_ROOT / ".env", SCRIPT_DIR / ".env", VAULT_ENV]:
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def decode_str(val):
    if not val:
        return ""
    parts = decode_header(val)
    res = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            res += part.decode(enc or "utf-8", errors="replace")
        else:
            res += str(part)
    return res.strip()

def decode_handshake_url(track_url: str) -> str:
    m = re.search(r'/c/([a-zA-Z0-9_-]+)', track_url)
    if not m:
        return track_url
    token = m.group(1)
    try:
        raw = base64.urlsafe_b64decode(token + '==')
        decomp = zlib.decompress(raw, 15).decode('utf-8', errors='ignore')
        params = urllib.parse.parse_qs(decomp)
        if 'l' in params and params['l']:
            return params['l'][0]
    except Exception:
        pass
    return track_url

def fetch_handshake_leads() -> list:
    """Extracts live Handshake job listings from Gmail IMAP or Handshake session API."""
    user_email = os.getenv("GMAIL_EMAIL_1") or os.getenv("GMAIL_EMAIL", "").strip()
    app_pass = os.getenv("GMAIL_APP_PASSWORD_1") or os.getenv("GMAIL_APP_PASSWORD", "").strip()
    leads = []
    seen_urls = set()

    if not user_email or not app_pass or not BeautifulSoup:
        return leads

    print(f"[*] Scanning Handshake job opportunities from {user_email}...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user_email, app_pass)
        mail.select("INBOX")

        since_date = (datetime.now() - timedelta(days=14)).strftime("%d-%b-%Y")
        status, msg_ids = mail.search(None, f'(SINCE {since_date} FROM "handshake")')
        if msg_ids and msg_ids[0]:
            ids = msg_ids[0].split()
            for mid in ids:
                try:
                    _, d = mail.fetch(mid, "(RFC822)")
                    msg = email.message_from_bytes(d[0][1])
                    date_header = decode_str(msg.get("Date", ""))
                    email_epoch = int(time.time())
                    try:
                        dt = parsedate_to_datetime(date_header)
                        email_epoch = int(dt.timestamp())
                    except Exception:
                        pass

                    html = ""
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            break
                    if not html:
                        continue

                    soup = BeautifulSoup(html, "html.parser")
                    for a in soup.find_all("a", href=True):
                        raw_txt = a.get_text(" | ", strip=True)
                        href = a["href"]
                        if not href:
                            continue
                        dest = decode_handshake_url(href)

                        if ("/job-search/" in dest or "/postings/" in dest or "/jobs/" in dest) and "joinhandshake.com" in dest:
                            base_job_url = dest.split("?")[0]
                            if base_job_url in seen_urls:
                                continue

                            parts = [p.strip() for p in raw_txt.split("|") if p.strip()]
                            if len(parts) >= 2:
                                company = parts[0]
                                title = parts[1]
                                extra = " | ".join(parts[2:]) if len(parts) > 2 else ""

                                salary = "Not Disclosed"
                                loc = "United States"
                                term = "Summer / Fall"

                                m_sal = re.search(r'(\$[\d.,]+(?:\s*[-–]\s*[\d.,]+)?(?:\s*(?:/hr|hr|/yr|yr|K/yr|k/yr))?)', extra)
                                if m_sal:
                                    salary = re.sub(r'[^\x00-\x7F]+', '–', m_sal.group(1)).strip()

                                m_loc = re.search(r'(?:|\b)([\w\s.-]+,\s*[A-Z]{2}(?:\s*\+\d+)?(?:\s*\((?:Hybrid|Onsite|Remote)\))?)', extra)
                                if m_loc:
                                    loc = re.sub(r'[^\x00-\x7F]+', '', m_loc.group(1)).strip()
                                elif "remote" in extra.lower():
                                    loc = "Remote"

                                if "full-time" in extra.lower():
                                    term = "Full-Time (2027 New Grad)"
                                elif "intern" in extra.lower() or "co-op" in extra.lower():
                                    term = "Internship / Co-op"

                                seen_urls.add(base_job_url)
                                leads.append({
                                    "company_name": company,
                                    "title": title,
                                    "url": base_job_url,
                                    "locations": [loc],
                                    "terms": [term],
                                    "salary": salary,
                                    "date_posted": email_epoch,
                                    "active": True,
                                    "source": "🤝 Handshake (Rutgers Campus Exclusive)"
                                })
                except Exception:
                    continue
        mail.logout()
    except Exception as e:
        print(f"[!] Handshake scan notice: {e}")

    return leads

def parse_job_text(raw_text: str) -> dict:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    title = lines[0] if lines else "Target Position"
    return {
        "title": title,
        "description": raw_text,
        "word_count": len(raw_text.split())
    }

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Fetch and parse job descriptions and Handshake leads.")
    parser.add_argument("--text", type=str, help="Job description text")
    parser.add_argument("--file", type=str, help="Path to job description file")
    parser.add_argument("--handshake", action="store_true", help="Fetch live Handshake opportunity leads")
    args = parser.parse_args()

    if args.handshake:
        hs_jobs = fetch_handshake_leads()
        print(f"[+] Retrieved {len(hs_jobs)} Handshake opportunity leads:")
        for j in hs_jobs:
            print(f"- {j['company_name']} — {j['title']} ({j['terms'][0]} | Pay: {j['salary']}) -> {j['url']}")
    else:
        content = args.text or ""
        if args.file and Path(args.file).exists():
            content = Path(args.file).read_text(encoding="utf-8")

        if content:
            res = parse_job_text(content)
            print(f"[✓] Parsed Job: {res['title']} ({res['word_count']} words)")
        else:
            print("[!] Provide --text, --file, or --handshake to parse.")