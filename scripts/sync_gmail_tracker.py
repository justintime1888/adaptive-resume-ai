#!/usr/bin/env python3
"""
Autonomous Email Application Scraper & Status Tracker
Connects to Gmail via IMAP (Google App Passwords), detects job application updates,
rejections, OAs, and interview invitations.
- Automatically logs application status updates.
- Feeds positive/negative signals into adaptive_learning.py.
- Auto-triggers generate_interview_prep.py upon interview/screen detection!
"""

import os
import re
import sys
import email
import imaplib
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from email.header import decode_header
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
APPS_DIR = REPO_ROOT / "applications"

load_dotenv(dotenv_path=REPO_ROOT / ".env")
load_dotenv(dotenv_path=SCRIPT_DIR / ".env")

sys.path.insert(0, str(SCRIPT_DIR))
from adaptive_learning import analyze_applications
from track_applications import sync_applications_to_csv
from generate_interview_prep import generate_interview_prep
from discord_alerts import push_application_update

def clean_header_str(val) -> str:
    if not val:
        return ""
    decoded_parts = decode_header(val)
    text = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            try:
                text += part.decode(encoding or "utf-8", errors="replace")
            except Exception:
                text += part.decode("latin-1", errors="replace")
        else:
            text += str(part)
    return text.strip()

def parse_email_signal(subject: str, sender: str, snippet: str) -> dict:
    text = f"{subject} {sender} {snippet}".lower()
    
    # 1. Detect Company
    comp_match = re.search(r'(?:applying to|application (?:to|at|with)|interest in|interview with|from)\s+([A-Z0-9][A-Za-z0-9\s&.,-]+?)(?:\s+(?:for|regarding|-|!|\.|\'s|\n|$))', subject, re.IGNORECASE)
    company = comp_match.group(1).strip() if comp_match else ""
    if not company and sender:
        s_clean = re.sub(r'<.*?>', '', sender).replace('"', '').strip()
        s_clean = re.sub(r'(?i)(recruiting|careers|talent|team|jobs|no-reply|notifications)', '', s_clean).strip()
        company = s_clean if len(s_clean) > 1 else "Target Company"

    # Check for Handshake patterns: "Vanguard just messaged you...", "Insmed sent you a new message", "Rebecca Walsh via Handshake"
    if "handshake" in sender.lower() or "handshake" in text:
        hs_comp = re.search(r'^([A-Z0-9][A-Za-z0-9\s&.,-]+?)\s+(?:just messaged you|sent you a new message)', subject, re.IGNORECASE)
        if hs_comp:
            company = hs_comp.group(1).strip()
        elif "via handshake" in sender.lower():
            hs_sender = re.search(r'^([^<]+?)\s+via\s+Handshake', sender, re.IGNORECASE)
            if hs_sender:
                company = f"{hs_sender.group(1).strip()} (Handshake)"

    company = re.sub(r' (Inc|LLC|Corp|Corporation|Team|Careers) ', '', company, flags=re.IGNORECASE).strip()
    if not company:
        company = "Target Company"

    # 2. Detect Role
    role = "Engineering Candidate"
    role_match = re.search(r'(?:for|position:?|role:?)\s+([A-Za-z0-9\s/,-]+?(?:Engineer|Intern|Developer|Associate|Specialist))', subject + " " + snippet, re.IGNORECASE)
    if role_match:
        role = role_match.group(1).strip()

    # 3. Detect Status Signal
    status = "Applied"
    is_interview_invite = False

    if any(k in text for k in ["interview invitation", "schedule your interview", "invite you to interview", "technical interview", "recruiter screen"]):
        status = "Technical"
        is_interview_invite = True
    elif any(k in text for k in ["online assessment", "codesignal", "hackerrank", "take-home challenge"]):
        status = "OA / Screen"
        is_interview_invite = True
    elif any(k in text for k in ["offer letter", "congratulations", "offer of employment", "job offer"]):
        status = "Offer"
    elif any(k in text for k in ["not moving forward", "other candidates", "unable to offer", "pursuing other candidates"]):
        status = "Rejected"
    elif "handshake" in sender.lower() and any(k in text for k in ["sent you a new message", "messaged you", "sees you as a top applicant"]):
        status = "OA / Screen"
        is_interview_invite = True

    return {
        "company": company,
        "role": role,
        "status": status,
        "is_interview_invite": is_interview_invite,
        "subject": subject,
        "snippet": snippet
    }


def scan_inbox():
    user_email = os.getenv("GMAIL_EMAIL", "").strip()
    app_pass = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()

    if not user_email or not app_pass:
        print("[*] Gmail credentials not found in .env (GMAIL_EMAIL, GMAIL_APP_PASSWORD).")
        print("    Skipping live IMAP scan. Configure .env to enable autonomous email status scraping.")
        return

    print(f"[*] Connecting to {user_email} to scan application signals...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user_email, app_pass)
        mail.select("INBOX")
    except Exception as e:
        print(f"[!] IMAP Connection Error: {e}")
        return

    since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    status, msg_ids = mail.search(None, f'(SINCE {since_date})')

    if not msg_ids or not msg_ids[0]:
        print("[+] No new emails found in the last 7 days.")
        return

    id_list = msg_ids[0].split()[-40:]
    for mid in id_list:
        try:
            _, data = mail.fetch(mid, '(RFC822.HEADER BODY.PEEK[TEXT])')
            raw = data[0][1]
            msg = email.message_from_bytes(raw)
            sub = clean_header_str(msg.get("Subject", ""))
            sender = clean_header_str(msg.get("From", ""))
            
            snippet = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        p = part.get_payload(decode=True)
                        if p:
                            snippet = p.decode(errors="replace")[:250]
                            break
            else:
                p = msg.get_payload(decode=True)
                if p:
                    snippet = p.decode(errors="replace")[:250]

            signal = parse_email_signal(sub, sender, snippet)
            if signal["status"] != "Applied" or "application" in sub.lower():
                print(f"[+] Found signal: {signal['company']} — {signal['role']} ({signal['status']})")
                
                # Auto-generate .docx interview packet if interview/OA detected!
                if signal["is_interview_invite"]:
                    print(f"    -> [🎉] Interview invite detected! Generating .docx Interview Prep Dossier...")
                    generate_interview_prep(signal["company"], signal["role"])
                
                push_application_update(signal["company"], signal["role"], signal["status"], sub)
        except Exception:
            continue

    try:
        mail.close()
        mail.logout()
    except Exception:
        pass

    sync_applications_to_csv()
    analyze_applications()

if __name__ == "__main__":
    scan_inbox()