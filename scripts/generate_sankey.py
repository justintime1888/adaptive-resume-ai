#!/usr/bin/env python3
"""
Autonomous Job Search Sankey Diagram & Funnel Pipeline Generator
Parses 04-Career/jobs_tracker.csv and Obsidian application notes.
Generates:
  1. An interactive, standalone HTML Sankey visualization (04-Career/Job_Search_Sankey.html)
     matching the user's SankeyMATIC layout and aesthetics.
  2. A live Obsidian dashboard note with embedded diagram & KPIs (04-Career/Job Search Pipeline Sankey.md).
  3. Live SankeyMATIC copyable syntax.
"""

import os
import sys
import csv
import json
import re
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if (PROJECT_ROOT / "04-Career").exists():
    CAREER_DIR = PROJECT_ROOT / "04-Career"
    CSV_PATH = CAREER_DIR / "jobs_tracker.csv"
    TAILORED_DIR = CAREER_DIR / "Tailored Resumes"
    APPS_DIR = CAREER_DIR / "Applications"
    HTML_OUTPUT = CAREER_DIR / "Job_Search_Sankey.html"
    MD_OUTPUT = CAREER_DIR / "Job Search Pipeline Sankey.md"
else:
    CAREER_DIR = PROJECT_ROOT
    CSV_PATH = PROJECT_ROOT / "applications" / "jobs_tracker.csv"
    TAILORED_DIR = PROJECT_ROOT / "resumes" / "tailored"
    APPS_DIR = PROJECT_ROOT / "applications"
    HTML_OUTPUT = PROJECT_ROOT / "analytics" / "Job_Search_Sankey.html"
    MD_OUTPUT = PROJECT_ROOT / "analytics" / "Job Search Pipeline Sankey.md"


def load_jobs():
    jobs = []
    seen = set()

    # 1. Read CSV
    if CSV_PATH.exists():
        with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                comp = (row.get("Company") or "").strip()
                role = (row.get("Role") or "").strip()
                if not comp and not role:
                    continue
                key = f"{comp.lower()}::{role.lower()}"
                status = (row.get("Status") or "Ready to Apply").strip()
                date_applied = (row.get("Date Applied") or "").strip()
                response = (row.get("Response Received") or "No").strip()
                location = (row.get("Location") or "").strip()
                comp_pay = (row.get("Compensation") or "").strip()
                follow_up = (row.get("Follow-up Target") or "").strip()

                jobs.append({
                    "company": comp,
                    "role": role,
                    "status": status,
                    "date_applied": date_applied,
                    "response": response,
                    "location": location,
                    "compensation": comp_pay,
                    "follow_up": follow_up,
                    "source": "csv"
                })
                seen.add(key)

    # 2. Check Obsidian Application / Tailored Notes for any additional entries or updates
    for scan_dir in [APPS_DIR, TAILORED_DIR]:
        if scan_dir.exists():
            for p in scan_dir.glob("*.md"):
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
                    if fm_match:
                        fm = fm_match.group(1)
                        comp_m = re.search(r'company:\s*["\']?(.*?)["\']?$', fm, re.M)
                        role_m = re.search(r'role:\s*["\']?(.*?)["\']?$', fm, re.M)
                        status_m = re.search(r'status:\s*["\']?(.*?)["\']?$', fm, re.M)
                        date_m = re.search(r'applied_date:\s*["\']?(.*?)["\']?$', fm, re.M)

                        comp = comp_m.group(1).strip() if comp_m else ""
                        role = role_m.group(1).strip() if role_m else ""
                        if comp and role:
                            key = f"{comp.lower()}::{role.lower()}"
                            status = status_m.group(1).strip() if status_m else "Ready to Apply"
                            date_applied = date_m.group(1).strip() if date_m else ""
                            if key not in seen:
                                jobs.append({
                                    "company": comp,
                                    "role": role,
                                    "status": status,
                                    "date_applied": date_applied,
                                    "response": "No",
                                    "location": "US",
                                    "compensation": "Open",
                                    "follow_up": "",
                                    "source": "note"
                                })
                                seen.add(key)
                except Exception:
                    pass

    return jobs

def categorize_funnel(jobs):
    total_tracked = len(jobs)
    ready_to_apply = []
    applied_all = []

    for j in jobs:
        st = j["status"].strip().lower()
        if any(k in st for k in ["ready", "wishlist", "queue", "dispatched", "to apply"]):
            ready_to_apply.append(j)
        else:
            applied_all.append(j)

    no_answer = []
    app_rejected = []
    first_interviews = []
    first_rejected = []
    first_in_progress = []
    second_interviews = []
    second_rejected = []
    second_in_progress = []
    offers = []
    accepted = []
    declined = []
    considering = []

    for j in applied_all:
        st = j["status"].strip().lower()
        resp = j["response"].strip().lower()

        if "accepted" in st or "accept" in st:
            accepted.append(j)
            offers.append(j)
            second_interviews.append(j)
            first_interviews.append(j)
        elif "declined" in st or "decline" in st:
            declined.append(j)
            offers.append(j)
            second_interviews.append(j)
            first_interviews.append(j)
        elif "offer" in st:
            considering.append(j)
            offers.append(j)
            second_interviews.append(j)
            first_interviews.append(j)
        elif any(k in st for k in ["final", "onsite", "2nd", "second"]):
            if "reject" in st or "denied" in st or "no offer" in st:
                second_rejected.append(j)
            else:
                second_in_progress.append(j)
            second_interviews.append(j)
            first_interviews.append(j)
        elif any(k in st for k in ["interview", "screen", "oa", "assessment", "phone", "technical", "1st", "first"]):
            if "reject" in st or "denied" in st or "no offer" in st:
                first_rejected.append(j)
            else:
                first_in_progress.append(j)
            first_interviews.append(j)
        elif "reject" in st or "denied" in st:
            app_rejected.append(j)
        else:
            no_answer.append(j)

    return {
        "total_tracked": total_tracked,
        "ready_to_apply": ready_to_apply,
        "applied_all": applied_all,
        "no_answer": no_answer,
        "app_rejected": app_rejected,
        "first_interviews": first_interviews,
        "first_rejected": first_rejected,
        "first_in_progress": first_in_progress,
        "second_interviews": second_interviews,
        "second_rejected": second_rejected,
        "second_in_progress": second_in_progress,
        "offers": offers,
        "accepted": accepted,
        "declined": declined,
        "considering": considering
    }

def generate_sankeymatic_text(data, mode="applied"):
    lines = []
    if mode == "pipeline":
        lines.append("// Job Search Pipeline (End-to-End)")
        if len(data["ready_to_apply"]) > 0:
            lines.append(f"Tracked Opportunities [{len(data['ready_to_apply'])}] Ready to Apply")
        if len(data["applied_all"]) > 0:
            lines.append(f"Tracked Opportunities [{len(data['applied_all'])}] Applications")
        lines.append("")

    lines.append("// Application Funnel")
    n_app = len(data["applied_all"])
    n_first = len(data["first_interviews"])
    n_reject = len(data["app_rejected"])
    n_no_ans = len(data["no_answer"])

    if n_first > 0:
        lines.append(f"Applications [{n_first}] 1st Interviews")
    if n_reject > 0:
        lines.append(f"Applications [{n_reject}] Rejected")
    if n_no_ans > 0:
        lines.append(f"Applications [{n_no_ans}] No Answer")

    # 1st Interviews stage
    n_second = len(data["second_interviews"])
    n_first_rej = len(data["first_rejected"])
    n_first_prog = len(data["first_in_progress"])
    if n_second > 0:
        lines.append(f"1st Interviews [{n_second}] 2nd Interviews")
    if n_first_rej > 0:
        lines.append(f"1st Interviews [{n_first_rej}] No Offer")
    if n_first_prog > 0:
        lines.append(f"1st Interviews [{n_first_prog}] In Progress")

    # 2nd Interviews stage
    n_offers = len(data["offers"])
    n_second_rej = len(data["second_rejected"])
    n_second_prog = len(data["second_in_progress"])
    if n_offers > 0:
        lines.append(f"2nd Interviews [{n_offers}] Offers")
    if n_second_rej > 0:
        lines.append(f"2nd Interviews [{n_second_rej}] No Offer")
    if n_second_prog > 0:
        lines.append(f"2nd Interviews [{n_second_prog}] In Progress")

    # Offers stage
    n_acc = len(data["accepted"])
    n_dec = len(data["declined"])
    n_cons = len(data["considering"])
    if n_acc > 0:
        lines.append(f"Offers [{n_acc}] Accepted")
    if n_dec > 0:
        lines.append(f"Offers [{n_dec}] Declined")
    if n_cons > 0:
        lines.append(f"Offers [{n_cons}] Decision Pending")

    return "\n".join(lines)

def build_html_dashboard(jobs, data):
    total_tracked = len(jobs)
    total_applied = len(data["applied_all"])
    total_interviews = len(data["first_interviews"])
    total_offers = len(data["offers"])
    total_accepted = len(data["accepted"])
    
    response_rate = (len(data["first_interviews"]) + len(data["app_rejected"])) / total_applied * 100 if total_applied > 0 else 0
    interview_rate = total_interviews / total_applied * 100 if total_applied > 0 else 0
    offer_rate = total_offers / total_applied * 100 if total_applied > 0 else 0

    sankeymatic_text = generate_sankeymatic_text(data, mode="applied")
    sankeymatic_pipeline_text = generate_sankeymatic_text(data, mode="pipeline")

    jobs_json = json.dumps(jobs, indent=2)
    stats_json = json.dumps({
        "total_tracked": total_tracked,
        "ready_to_apply": len(data["ready_to_apply"]),
        "applied": total_applied,
        "no_answer": len(data["no_answer"]),
        "app_rejected": len(data["app_rejected"]),
        "first_interviews": len(data["first_interviews"]),
        "first_rejected": len(data["first_rejected"]),
        "first_in_progress": len(data["first_in_progress"]),
        "second_interviews": len(data["second_interviews"]),
        "second_rejected": len(data["second_rejected"]),
        "second_in_progress": len(data["second_in_progress"]),
        "offers": len(data["offers"]),
        "accepted": len(data["accepted"]),
        "declined": len(data["declined"]),
        "considering": len(data["considering"]),
        "response_rate": round(response_rate, 1),
        "interview_rate": round(interview_rate, 1),
        "offer_rate": round(offer_rate, 1)
    })

    now_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Search Funnel & Sankey Visualizer — Justin Parra</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.2);
      --success: #34d399;
      --warning: #fbbf24;
      --danger: #f87171;
    }}

    body.light-theme {{
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --card-border: #e2e8f0;
      --text: #0f172a;
      --text-muted: #64748b;
      --accent: #0284c7;
      --accent-glow: rgba(2, 132, 199, 0.15);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background: radial-gradient(circle at top right, #1e1b4b 0%, #0f172a 40%, #020617 100%);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem 1.5rem 4rem;
      line-height: 1.5;
      transition: background 0.3s ease, color 0.3s ease;
    }}

    body.light-theme {{
      background: #f1f5f9;
    }}

    .container {{
      max-width: 1280px;
      margin: 0 auto;
    }}

    /* Header */
    header {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 1.5rem;
      margin-bottom: 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--card-border);
    }}

    .header-titles h1 {{
      font-size: 1.85rem;
      font-weight: 800;
      letter-spacing: -0.025em;
      background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    body.light-theme .header-titles h1 {{
      background: linear-gradient(135deg, #0f172a 30%, #475569 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .header-titles p {{
      color: var(--text-muted);
      font-size: 0.9rem;
      margin-top: 0.25rem;
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.6rem 1.1rem;
      font-size: 0.85rem;
      font-weight: 600;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: var(--card-bg);
      color: var(--text);
      cursor: pointer;
      transition: all 0.2s ease;
      text-decoration: none;
    }}

    .btn:hover {{
      background: rgba(51, 65, 85, 0.8);
      border-color: rgba(255, 255, 255, 0.2);
      transform: translateY(-1px);
    }}

    .btn-primary {{
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
      border-color: #38bdf8;
      color: #ffffff;
      box-shadow: 0 4px 14px var(--accent-glow);
    }}

    .btn-primary:hover {{
      background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
    }}

    /* Metrics Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }}

    .kpi-card {{
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem 1rem;
      text-align: center;
      position: relative;
      overflow: hidden;
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}

    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--accent);
      opacity: 0.7;
    }}

    .kpi-card.success::before {{ background: var(--success); }}
    .kpi-card.warning::before {{ background: var(--warning); }}
    .kpi-card.danger::before {{ background: var(--danger); }}

    .kpi-value {{
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      margin-top: 0.25rem;
    }}

    .kpi-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      font-weight: 600;
    }}

    /* Chart Card */
    .chart-card {{
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.4);
    }}

    .chart-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid var(--card-border);
    }}

    .chart-tabs {{
      display: flex;
      gap: 0.5rem;
      background: rgba(15, 23, 42, 0.6);
      padding: 0.3rem;
      border-radius: 10px;
      border: 1px solid var(--card-border);
    }}

    body.light-theme .chart-tabs {{
      background: #e2e8f0;
    }}

    .tab-btn {{
      padding: 0.45rem 0.9rem;
      border-radius: 7px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}

    .tab-btn.active {{
      background: #0284c7;
      color: #ffffff;
      box-shadow: 0 2px 8px var(--accent-glow);
    }}

    /* Sankey Canvas */
    #sankey-wrap {{
      width: 100%;
      overflow-x: auto;
      min-height: 520px;
      display: flex;
      justify-content: center;
      align-items: center;
      position: relative;
      background: rgba(0, 0, 0, 0.15);
      border-radius: 12px;
      padding: 1rem;
    }}

    body.light-theme #sankey-wrap {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
    }}

    svg.sankey-svg {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      user-select: none;
    }}

    .ribbon {{
      fill-opacity: 0.48;
      transition: fill-opacity 0.2s, stroke 0.2s;
      cursor: pointer;
    }}

    .ribbon:hover {{
      fill-opacity: 0.78;
    }}

    .node-group {{
      cursor: ns-resize;
    }}

    .node-group rect {{
      rx: 3px;
      transition: opacity 0.2s, filter 0.2s;
    }}

    .node-group:hover rect {{
      filter: brightness(1.15);
    }}

    .node-label {{
      font-size: 13px;
      font-weight: 700;
      fill: var(--text);
      pointer-events: none;
    }}

    .node-val {{
      font-size: 16px;
      font-weight: 800;
      fill: var(--text);
      pointer-events: none;
    }}

    /* Empty state notice */
    .empty-state {{
      text-align: center;
      padding: 3.5rem 1.5rem;
      background: rgba(15, 23, 42, 0.4);
      border-radius: 12px;
      border: 1px dashed rgba(255, 255, 255, 0.15);
      margin: 1rem 0;
      width: 100%;
    }}

    .empty-state h3 {{
      font-size: 1.25rem;
      margin-bottom: 0.5rem;
      color: #38bdf8;
    }}

    .empty-state p {{
      color: var(--text-muted);
      max-width: 620px;
      margin: 0 auto 1.5rem;
      font-size: 0.92rem;
    }}

    /* Sankeymatic Syntax Drawer */
    .syntax-box {{
      background: #090d16;
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
      margin-top: 1.5rem;
    }}

    body.light-theme .syntax-box {{
      background: #f1f5f9;
    }}

    .syntax-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }}

    .syntax-header h4 {{
      font-size: 0.85rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    pre.code-block {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      color: #38bdf8;
      background: rgba(0, 0, 0, 0.35);
      padding: 1rem;
      border-radius: 8px;
      overflow-x: auto;
      white-space: pre-wrap;
      line-height: 1.6;
    }}

    body.light-theme pre.code-block {{
      background: #ffffff;
      color: #0369a1;
      border: 1px solid #cbd5e1;
    }}

    /* Table Section */
    .table-card {{
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 1.5rem;
    }}

    .table-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      flex-wrap: wrap;
      gap: 1rem;
    }}

    .table-header h3 {{
      font-size: 1.15rem;
      font-weight: 700;
    }}

    .table-search {{
      padding: 0.5rem 0.9rem;
      font-size: 0.85rem;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: rgba(15, 23, 42, 0.8);
      color: #ffffff;
      outline: none;
      width: 260px;
    }}

    body.light-theme .table-search {{
      background: #ffffff;
      color: #0f172a;
      border-color: #cbd5e1;
    }}

    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}

    table.data-table th {{
      text-align: left;
      padding: 0.75rem 1rem;
      background: rgba(15, 23, 42, 0.7);
      color: var(--text-muted);
      font-weight: 600;
      border-bottom: 1px solid var(--card-border);
    }}

    body.light-theme table.data-table th {{
      background: #f8fafc;
    }}

    table.data-table td {{
      padding: 0.85rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--text);
    }}

    body.light-theme table.data-table td {{
      border-bottom: 1px solid #e2e8f0;
    }}

    table.data-table tr:hover td {{
      background: rgba(255, 255, 255, 0.03);
    }}

    .status-badge {{
      display: inline-block;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: capitalize;
    }}

    .badge-applied {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }}
    .badge-ready {{ background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }}
    .badge-screen {{ background: rgba(129, 140, 248, 0.15); color: #818cf8; border: 1px solid rgba(129, 140, 248, 0.3); }}
    .badge-offer {{ background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }}
    .badge-reject {{ background: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); }}

    /* Toast */
    #toast {{
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: #0284c7;
      color: #ffffff;
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.85rem;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s ease, transform 0.3s ease;
      transform: translateY(10px);
      z-index: 1000;
    }}

    #toast.show {{
      opacity: 1;
      transform: translateY(0);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-titles">
        <h1>📊 Job Search Pipeline & Sankey Funnel</h1>
        <p>Real-Time Application Telemetry &bull; Last Synced: <strong>{now_str}</strong></p>
      </div>
      <div class="header-actions">
        <button class="btn" onclick="toggleTheme()">🌓 Toggle Light/Dark</button>
        <button class="btn" onclick="location.reload()">🔄 Refresh Data</button>
        <button class="btn" onclick="copySankeyMatic()">📋 Copy SankeyMATIC Syntax</button>
        <button class="btn" onclick="downloadSVG()">💾 Download SVG</button>
        <a class="btn btn-primary" href="https://sankeymatic.com/build/" target="_blank">🌐 Open SankeyMATIC.com</a>
      </div>
    </header>

    <!-- Top KPIs -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Tracked Roles</div>
        <div class="kpi-value">{total_tracked}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Applications Submitted</div>
        <div class="kpi-value" style="color: #e066a3;">{total_applied}</div>
      </div>
      <div class="kpi-card success">
        <div class="kpi-label">Active Interviews</div>
        <div class="kpi-value" style="color: #38bdf8;">{total_interviews}</div>
      </div>
      <div class="kpi-card success">
        <div class="kpi-label">Offers Received</div>
        <div class="kpi-value" style="color: #34d399;">{total_offers}</div>
      </div>
      <div class="kpi-card warning">
        <div class="kpi-label">Interview Rate</div>
        <div class="kpi-value">{round(interview_rate, 1)}%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Awaiting Response</div>
        <div class="kpi-value" style="color: #2dd4bf;">{len(data['no_answer'])}</div>
      </div>
    </div>

    <!-- Main Sankey Visualization -->
    <div class="chart-card">
      <div class="chart-header">
        <div>
          <h2 style="font-size: 1.25rem; font-weight: 700;">Job Application Funnel Flow</h2>
          <p style="font-size: 0.82rem; color: var(--text-muted);">Interactive Sankey Diagram &bull; Matches SankeyMATIC format &bull; Drag nodes vertically</p>
        </div>
        <div class="chart-tabs">
          <button class="tab-btn active" id="tab-applied" onclick="setMode('applied')">Active Applications</button>
          <button class="tab-btn" id="tab-pipeline" onclick="setMode('pipeline')">Full Pipeline (With Queued)</button>
          <button class="tab-btn" id="tab-sample" onclick="setMode('sample')">Sample Funnel (17 Apps)</button>
        </div>
      </div>

      <div id="sankey-wrap">
        <svg id="sankey-svg" class="sankey-svg" width="920" height="540"></svg>
      </div>

      <!-- SankeyMATIC Text Box -->
      <div class="syntax-box">
        <div class="syntax-header">
          <h4>SankeyMATIC Compliant Syntax (Ready for Paste)</h4>
          <button class="btn" style="padding: 0.35rem 0.75rem; font-size: 0.75rem;" onclick="copySankeyMatic()">Copy Text</button>
        </div>
        <pre class="code-block" id="sankeymatic-code">{sankeymatic_text if sankeymatic_text else '// No applications submitted yet. React in Discord or set status to Applied!'}</pre>
      </div>
    </div>

    <!-- Detailed Tracking Table -->
    <div class="table-card">
      <div class="table-header">
        <h3>📋 Live Application Ledger ({total_tracked} Positions)</h3>
        <input type="text" class="table-search" id="table-search" placeholder="Search company, role..." oninput="filterTable()">
      </div>
      <div style="overflow-x: auto;">
        <table class="data-table" id="jobs-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Role</th>
              <th>Status</th>
              <th>Date Applied</th>
              <th>Response</th>
              <th>Location</th>
              <th>Compensation</th>
            </tr>
          </thead>
          <tbody>
          """

    for j in jobs:
        st = j["status"]
        badge_cls = "badge-applied"
        if "ready" in st.lower():
            badge_cls = "badge-ready"
        elif "screen" in st.lower() or "interview" in st.lower():
            badge_cls = "badge-screen"
        elif "offer" in st.lower() or "accept" in st.lower():
            badge_cls = "badge-offer"
        elif "reject" in st.lower():
            badge_cls = "badge-reject"

        html += f"""
            <tr>
              <td style="font-weight: 700; color: #38bdf8;">{j['company']}</td>
              <td>{j['role']}</td>
              <td><span class="status-badge {badge_cls}">{st}</span></td>
              <td>{j['date_applied'] if j['date_applied'] else '<span style=\"color:#64748b;\">—</span>'}</td>
              <td>{'🟢 Yes' if j['response'].lower() == 'yes' else '⚪ Waiting'}</td>
              <td style="color: #94a3b8; font-size: 0.8rem;">{j['location']}</td>
              <td style="color: #94a3b8; font-size: 0.8rem;">{j['compensation']}</td>
            </tr>"""

    html += f"""
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div id="toast">Copied SankeyMATIC syntax to clipboard!</div>

  <script>
    const LIVE_DATA = {stats_json};
    const ALL_JOBS = {jobs_json};
    let currentMode = 'applied';

    const COLOR_MAP = {{
      'Tracked Opportunities': '#6366f1',
      'Ready to Apply': '#f59e0b',
      'Applications': '#e066a3',
      '1st Interviews': '#4b9cd3',
      '2nd Interviews': '#e09f58',
      'Offers': '#f29e84',
      'Accepted': '#5bb462',
      'Declined': '#e74c3c',
      'Rejected': '#ccb732',
      'No Answer': '#64c7cf',
      'No Offer': '#64c7cf',
      'In Progress': '#38bdf8',
      'Decision Pending': '#a78bfa'
    }};

    function toggleTheme() {{
      document.body.classList.toggle('light-theme');
      renderSankey();
    }}

    function setMode(mode) {{
      currentMode = mode;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-' + mode).classList.add('active');

      const codeBox = document.getElementById('sankeymatic-code');
      if (mode === 'pipeline') {{
        codeBox.innerText = `{sankeymatic_pipeline_text}`;
      }} else if (mode === 'applied') {{
        codeBox.innerText = `{sankeymatic_text if sankeymatic_text else '// No applications submitted yet. Set status to Applied or react in Discord!'}`;
      }} else {{
        codeBox.innerText = `// Sample Job Search diagram:\\nApplications [4] 1st Interviews\\nApplications [9] Rejected\\nApplications [4] No Answer\\n1st Interviews [2] 2nd Interviews\\n1st Interviews [2] No Offer\\n2nd Interviews [2] Offers\\nOffers [1] Accepted\\nOffers [1] Declined`;
      }}

      renderSankey();
    }}

    function getFlows() {{
      if (currentMode === 'sample') {{
        return [
          {{ source: 'Applications', target: '1st Interviews', value: 4 }},
          {{ source: 'Applications', target: 'Rejected', value: 9 }},
          {{ source: 'Applications', target: 'No Answer', value: 4 }},
          {{ source: '1st Interviews', target: '2nd Interviews', value: 2 }},
          {{ source: '1st Interviews', target: 'No Offer', value: 2 }},
          {{ source: '2nd Interviews', target: 'Offers', value: 2 }},
          {{ source: 'Offers', target: 'Accepted', value: 1 }},
          {{ source: 'Offers', target: 'Declined', value: 1 }}
        ];
      }}

      const flows = [];
      const d = LIVE_DATA;

      if (currentMode === 'pipeline') {{
        if (d.ready_to_apply > 0) {{
          flows.push({{ source: 'Tracked Opportunities', target: 'Ready to Apply', value: d.ready_to_apply }});
        }}
        if (d.applied > 0) {{
          flows.push({{ source: 'Tracked Opportunities', target: 'Applications', value: d.applied }});
        }}
      }}

      // Application branches
      if (d.first_interviews > 0) {{
        flows.push({{ source: 'Applications', target: '1st Interviews', value: d.first_interviews }});
      }}
      if (d.app_rejected > 0) {{
        flows.push({{ source: 'Applications', target: 'Rejected', value: d.app_rejected }});
      }}
      if (d.no_answer > 0) {{
        flows.push({{ source: 'Applications', target: 'No Answer', value: d.no_answer }});
      }}

      // 1st Interview branches
      if (d.second_interviews > 0) {{
        flows.push({{ source: '1st Interviews', target: '2nd Interviews', value: d.second_interviews }});
      }}
      if (d.first_rejected > 0) {{
        flows.push({{ source: '1st Interviews', target: 'No Offer', value: d.first_rejected }});
      }}
      if (d.first_in_progress > 0) {{
        flows.push({{ source: '1st Interviews', target: 'In Progress', value: d.first_in_progress }});
      }}

      // 2nd Interview branches
      if (d.offers > 0) {{
        flows.push({{ source: '2nd Interviews', target: 'Offers', value: d.offers }});
      }}
      if (d.second_rejected > 0) {{
        flows.push({{ source: '2nd Interviews', target: 'No Offer', value: d.second_rejected }});
      }}
      if (d.second_in_progress > 0) {{
        flows.push({{ source: '2nd Interviews', target: 'In Progress', value: d.second_in_progress }});
      }}

      // Offers branches
      if (d.accepted > 0) {{
        flows.push({{ source: 'Offers', target: 'Accepted', value: d.accepted }});
      }}
      if (d.declined > 0) {{
        flows.push({{ source: 'Offers', target: 'Declined', value: d.declined }});
      }}
      if (d.considering > 0) {{
        flows.push({{ source: 'Offers', target: 'Decision Pending', value: d.considering }});
      }}

      return flows;
    }}

    /**
     * High-Definition Standalone SVG Sankey Layout Engine
     * Zero external runtime dependencies; 100% offline resilient.
     */
    function renderSankey() {{
      const flows = getFlows();
      const wrap = document.getElementById('sankey-wrap');

      if (!flows || flows.length === 0) {{
        wrap.innerHTML = `
          <div class="empty-state">
            <h3>⏳ 5 Applications Queued in "Ready to Apply"</h3>
            <p>You have 5 curated top-tier roles ready. When you submit them and react in Discord (or set status to <strong>Applied</strong> in your tracker), they will automatically stream across this Sankey diagram!</p>
            <div style="display:flex; justify-content:center; gap:0.75rem;">
              <button class="btn btn-primary" onclick="setMode('pipeline')">View in Full Pipeline Mode</button>
              <button class="btn" onclick="setMode('sample')">View Sample 17-Job Funnel</button>
            </div>
          </div>
        `;
        return;
      }}

      const width = 920;
      const height = 520;
      const margin = {{ top: 35, right: 140, bottom: 35, left: 140 }};
      const nodeWidth = 10;
      const nodePadding = 24;

      // 1. Column assignment for nodes
      const colMap = {{
        'Tracked Opportunities': 0,
        'Ready to Apply': 1,
        'Applications': currentMode === 'pipeline' ? 1 : 0,
        '1st Interviews': currentMode === 'pipeline' ? 2 : 1,
        'Rejected': currentMode === 'pipeline' ? 2 : 1,
        'No Answer': currentMode === 'pipeline' ? 2 : 1,
        '2nd Interviews': currentMode === 'pipeline' ? 3 : 2,
        'No Offer': currentMode === 'pipeline' ? 3 : 2,
        'In Progress': currentMode === 'pipeline' ? 3 : 2,
        'Offers': currentMode === 'pipeline' ? 4 : 3,
        'Accepted': currentMode === 'pipeline' ? 5 : 4,
        'Declined': currentMode === 'pipeline' ? 5 : 4,
        'Decision Pending': currentMode === 'pipeline' ? 5 : 4
      }};

      // Group nodes
      const nodesByName = {{}};
      flows.forEach(f => {{
        if (!nodesByName[f.source]) nodesByName[f.source] = {{ name: f.source, outVal: 0, inVal: 0, sourceLinks: [], targetLinks: [] }};
        if (!nodesByName[f.target]) nodesByName[f.target] = {{ name: f.target, outVal: 0, inVal: 0, sourceLinks: [], targetLinks: [] }};
        nodesByName[f.source].outVal += f.value;
        nodesByName[f.target].inVal += f.value;
      }});

      const nodes = Object.values(nodesByName);
      nodes.forEach(n => {{
        n.value = Math.max(n.outVal, n.inVal);
        n.col = colMap[n.name] !== undefined ? colMap[n.name] : 0;
      }});

      const maxCol = Math.max(...nodes.map(n => n.col));
      const colStep = (width - margin.left - margin.right) / Math.max(1, maxCol);

      // Group by column
      const cols = [];
      for (let c = 0; c <= maxCol; c++) {{
        cols.push(nodes.filter(n => n.col === c));
      }}

      // Compute scale
      const availHeight = height - margin.top - margin.bottom;
      let maxColVal = 0;
      cols.forEach(cNodes => {{
        const sumVal = cNodes.reduce((acc, n) => acc + n.value, 0);
        if (sumVal > maxColVal) maxColVal = sumVal;
      }});

      const ky = (availHeight - (Math.max(...cols.map(c => c.length)) - 1) * nodePadding) / Math.max(1, maxColVal);

      // Position nodes
      cols.forEach(cNodes => {{
        const totalNodeH = cNodes.reduce((acc, n) => acc + n.value * ky, 0) + (cNodes.length - 1) * nodePadding;
        let y = margin.top + (availHeight - totalNodeH) / 2;

        cNodes.forEach(n => {{
          n.x = margin.left + n.col * colStep;
          n.y = y;
          n.h = Math.max(4, n.value * ky);
          n.w = nodeWidth;
          y += n.h + nodePadding;
        }});
      }});

      // Links positioning
      const links = flows.map(f => ({{
        source: nodesByName[f.source],
        target: nodesByName[f.target],
        value: f.value
      }}));

      nodes.forEach(n => {{
        n.sourceOffset = 0;
        n.targetOffset = 0;
      }});

      links.forEach(l => {{
        const linkH = l.value * ky;
        l.sy = l.source.y + l.source.sourceOffset;
        l.ty = l.target.y + l.target.targetOffset;
        l.h = linkH;
        l.source.sourceOffset += linkH;
        l.target.targetOffset += linkH;
      }});

      // Generate SVG
      let svgHtml = `<svg id="sankey-svg" class="sankey-svg" width="${{width}}" height="${{height}}" viewBox="0 0 ${{width}} ${{height}}">`;

      // Draw Ribbons
      links.forEach(l => {{
        const x0 = l.source.x + l.source.w;
        const x1 = l.target.x;
        const y0_top = l.sy;
        const y0_bot = l.sy + l.h;
        const y1_top = l.ty;
        const y1_bot = l.ty + l.h;
        const dx = (x1 - x0) * 0.5;

        const pathD = `M ${{x0}},${{y0_top}} C ${{x0 + dx}},${{y0_top}} ${{x1 - dx}},${{y1_top}} ${{x1}},${{y1_top}} L ${{x1}},${{y1_bot}} C ${{x1 - dx}},${{y1_bot}} ${{x0 + dx}},${{y0_bot}} ${{x0}},${{y0_bot}} Z`;
        const color = COLOR_MAP[l.target.name] || '#38bdf8';

        svgHtml += `
          <path class="ribbon" d="${{pathD}}" fill="${{color}}">
            <title>${{l.source.name}} → ${{l.target.name}}: ${{l.value}}</title>
          </path>
        `;
      }});

      // Draw Nodes
      nodes.forEach(n => {{
        const color = COLOR_MAP[n.name] || '#38bdf8';
        const isLeft = n.col === 0;
        const textAnchor = isLeft ? 'end' : 'start';
        const textX = isLeft ? n.x - 12 : n.x + n.w + 12;
        const centerY = n.y + n.h / 2;

        svgHtml += `
          <g class="node-group" id="node-${{n.name.replace(/\\W+/g, '_')}}" data-name="${{n.name}}">
            <rect x="${{n.x}}" y="${{n.y}}" width="${{n.w}}" height="${{n.h}}" fill="${{color}}">
              <title>${{n.name}}: ${{n.value}}</title>
            </rect>
            <text class="node-val" x="${{textX}}" y="${{centerY - 6}}" text-anchor="${{textAnchor}}">${{n.value}}</text>
            <text class="node-label" x="${{textX}}" y="${{centerY + 14}}" text-anchor="${{textAnchor}}">${{n.name}}</text>
          </g>
        `;
      }});

      svgHtml += `</svg>`;
      wrap.innerHTML = svgHtml;
    }}

    function copySankeyMatic() {{
      const text = document.getElementById('sankeymatic-code').innerText;
      navigator.clipboard.writeText(text).then(() => {{
        const toast = document.getElementById('toast');
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2500);
      }});
    }}

    function downloadSVG() {{
      const svgEl = document.getElementById('sankey-svg');
      if (!svgEl) return;
      const svgData = new XMLSerializer().serializeToString(svgEl);
      const blob = new Blob([svgData], {{ type: 'image/svg+xml;charset=utf-8' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Job_Search_Sankey_${{currentMode}}.svg`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }}

    function filterTable() {{
      const q = document.getElementById('table-search').value.toLowerCase();
      const rows = document.querySelectorAll('#jobs-table tbody tr');
      rows.forEach(r => {{
        const txt = r.innerText.toLowerCase();
        r.style.display = txt.includes(q) ? '' : 'none';
      }});
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      renderSankey();
    }});
  </script>
</body>
</html>
"""
    return html

def generate_markdown_dashboard(jobs, data):
    total_tracked = len(jobs)
    total_applied = len(data["applied_all"])
    total_interviews = len(data["first_interviews"])
    total_offers = len(data["offers"])
    rate = round(total_interviews / total_applied * 100, 1) if total_applied > 0 else 0

    sankey_code = generate_sankeymatic_text(data, mode="applied")
    if not sankey_code:
        sankey_code = "// Waiting for submitted applications. Marked in tracker as 'Applied'."

    md = f"""---
tags:
  - career/pipeline-sankey
  - career/dashboard
updated: "{datetime.now().strftime('%Y-%m-%d %H:%M')}"
---

# 📊 Job Search Pipeline & Funnel (Sankey View)

> **Real-Time Job Funnel Telemetry** &bull; 1-Click Interactive HTML Visualization:  
> 🔗 **[Open Interactive Sankey Dashboard in Browser](file://{HTML_OUTPUT.as_posix()})**

---

## 📈 Pipeline Snapshot & Conversion KPIs

| 📝 Total Tracked | 📤 Applications Sent | 🎯 1st Interviews / Screen | 🏆 2nd / Technical | 🎉 Offers | 📊 Screen Conversion |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **{total_tracked}** | **{total_applied}** | **{total_interviews}** | **{len(data['second_interviews'])}** | **{total_offers}** | **{rate}%** |

---

## 🌊 Application Flow (SankeyMATIC Compliant)

You can copy and paste the block below directly into [SankeyMATIC.com](https://sankeymatic.com/build/) to reproduce the exact diagram:

```text
{sankey_code}
```

---

## 🧭 Visual Flow Diagram

```mermaid
graph LR
    classDef app fill:#e066a3,stroke:#fff,stroke-width:1px,color:#fff;
    classDef screen fill:#38bdf8,stroke:#fff,stroke-width:1px,color:#fff;
    classDef tech fill:#fb923c,stroke:#fff,stroke-width:1px,color:#fff;
    classDef offer fill:#34d399,stroke:#fff,stroke-width:1px,color:#fff;
    classDef rej fill:#eab308,stroke:#fff,stroke-width:1px,color:#fff;
    classDef wait fill:#2dd4bf,stroke:#fff,stroke-width:1px,color:#fff;
    classDef queue fill:#f59e0b,stroke:#fff,stroke-width:1px,color:#fff;

    Queue["📥 Ready to Apply ({len(data['ready_to_apply'])})"]:::queue
    Apps["📝 Applications ({total_applied})"]:::app

    Apps -->|"Screen ({len(data['first_interviews'])})"| Screen["🎯 1st Interviews ({len(data['first_interviews'])})"]:::screen
    Apps -->|"No Answer ({len(data['no_answer'])})"| Wait["⏳ No Answer ({len(data['no_answer'])})"]:::wait
    Apps -->|"Rejected ({len(data['app_rejected'])})"| Rej["❌ Rejected ({len(data['app_rejected'])})"]:::rej

    Screen -->|"Advanced ({len(data['second_interviews'])})"| Tech["💼 2nd Interviews ({len(data['second_interviews'])})"]:::tech
    Tech -->|"Offers ({total_offers})"| Offers["🏆 Offers ({total_offers})"]:::offer
```

---

## ⚡ 1-Click Actions
- **Open Interactive Browser Sankey:** [Job_Search_Sankey.html](file://{HTML_OUTPUT.as_posix()})
- **Desktop Shortcut:** Double click `Job Pipeline Sankey` on your Desktop to regenerate and open instantly!
"""
    return md

def run():
    print("[*] Generating Job Search Sankey Diagram & Pipeline Dashboard...")
    jobs = load_jobs()
    data = categorize_funnel(jobs)

    html = build_html_dashboard(jobs, data)
    HTML_OUTPUT.write_text(html, encoding="utf-8")
    print(f"[✓] Generated Interactive HTML: {HTML_OUTPUT}")

    md = generate_markdown_dashboard(jobs, data)
    MD_OUTPUT.write_text(md, encoding="utf-8")
    print(f"[✓] Generated Obsidian Dashboard: {MD_OUTPUT}")

    sankeymatic_txt = generate_sankeymatic_text(data, mode="applied")
    print("\n--- SankeyMATIC Syntax Preview ---")
    print(sankeymatic_txt if sankeymatic_txt else "(No submitted applications yet; 5 queued in Ready to Apply)")
    print("----------------------------------\n")

if __name__ == "__main__":
    run()
