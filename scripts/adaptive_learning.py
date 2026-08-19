#!/usr/bin/env python3
"""
Adaptive Learning & Resume Conversion Analytics Engine
Analyzes application outcomes (Applied, OA, Technical, Offer, Rejected),
tracks conversion rates across resume archetypes and keywords, and dynamically
optimizes resume tailoring for future applications.
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
APPS_DIR = REPO_ROOT / "applications"
ANALYTICS_DIR = REPO_ROOT / "analytics"
DATA_FILE = ANALYTICS_DIR / "learning_data.json"
DASHBOARD_FILE = ANALYTICS_DIR / "Resume_Performance_Dashboard.md"

DEFAULT_ARCHETYPES = [
    "Software Engineering",
    "Embedded Systems & Firmware",
    "Robotics & Autonomous Systems",
    "Hardware & Digital EE",
    "Data Science & AI"
]

def load_or_init_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    initial = {
        "archetypes": {},
        "top_converting_keywords": {},
        "history": []
    }
    for arch in DEFAULT_ARCHETYPES:
        initial["archetypes"][arch] = {"applied": 0, "interviews": 0, "offers": 0, "keywords": {}}
    return initial

def analyze_applications():
    data = load_or_init_data()
    
    # Reset counters
    for arch in data["archetypes"]:
        data["archetypes"][arch] = {"applied": 0, "interviews": 0, "offers": 0, "keywords": {}}
    data["top_converting_keywords"] = {}
    data["history"] = []

    files = list(APPS_DIR.glob("*.md"))
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            if "career/application" not in content:
                continue

            def get_field(field_name):
                m = re.search(rf'{field_name}:\s*["\']?(.*?)["\']?\n', content)
                return m.group(1).strip() if m else ""

            comp = get_field("company") or f.stem.split(" - ")[0]
            role = get_field("role") or "Software Engineer"
            status = get_field("status") or "Applied"
            date = get_field("applied_date") or datetime.now().strftime("%Y-%m-%d")

            # Determine archetype
            full_text = f"{comp} {role} {content}".lower()
            if any(k in full_text for k in ["robotics", "autopilot", "controls", "kinematics", "navigation"]):
                arch = "Robotics & Autonomous Systems"
            elif any(k in full_text for k in ["embedded", "firmware", "microcontroller", "esp32", "rtos"]):
                arch = "Embedded Systems & Firmware"
            elif any(k in full_text for k in ["hardware", "pcb", "asic", "fpga", "verilog", "circuits"]):
                arch = "Hardware & Digital EE"
            elif any(k in full_text for k in ["data", "machine learning", "ai", "pytorch", "deep learning"]):
                arch = "Data Science & AI"
            else:
                arch = "Software Engineering"

            if arch not in data["archetypes"]:
                data["archetypes"][arch] = {"applied": 0, "interviews": 0, "offers": 0, "keywords": {}}

            is_interview = status in ["OA / Screen", "Technical", "Final Round", "Offer"]
            is_offer = status == "Offer"

            data["archetypes"][arch]["applied"] += 1
            if is_interview:
                data["archetypes"][arch]["interviews"] += 1
            if is_offer:
                data["archetypes"][arch]["offers"] += 1

            # Keyword win tracking
            common_keywords = ["c++", "python", "c", "rust", "go", "rtos", "linux", "docker", "aws", "pid", "esp32", "fpga", "sql", "git"]
            for kw in common_keywords:
                if kw in full_text:
                    data["archetypes"][arch]["keywords"][kw] = data["archetypes"][arch]["keywords"].get(kw, 0) + 1
                    if is_interview:
                        data["top_converting_keywords"][kw] = data["top_converting_keywords"].get(kw, 0) + 1

            data["history"].append({
                "company": comp,
                "role": role,
                "archetype": arch,
                "status": status,
                "date": date,
                "interview_won": is_interview
            })
        except Exception:
            continue

    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    render_dashboard(data)
    return data

def render_dashboard(data: dict):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    rows = []
    for arch, stats in data["archetypes"].items():
        app = stats["applied"]
        inte = stats["interviews"]
        off = stats["offers"]
        rate = f"{(inte / app * 100):.1f}%" if app > 0 else "N/A"
        rows.append(f"| **{arch}** | {app} | {inte} | {rate} | {off} |")

    top_kws = sorted(data["top_converting_keywords"].items(), key=lambda x: x[1], reverse=True)[:10]
    top_kw_str = ", ".join([f"`{k} ({v} wins)`" for k, v in top_kws]) if top_kws else "*(Log more applications to discover keyword win rates)*"

    md = f"""---
tags:
  - career/analytics
last_updated: "{now_str}"
---

# 🧠 AI Resume Performance & Learning Analytics Dashboard

> **Adaptive Feedback Loop**: Automatically analyzes your job applications, measures interview response rates across resume archetypes, and optimizes keyword targeting for future applications.

---

## 📊 Conversion Rate by Resume Archetype

| Resume Track & Archetype | Applications Sent | Interviews / Screens | 🎯 Interview Rate | 🎉 Offers |
| :--- | :---: | :---: | :---: | :---: |
{chr(10).join(rows)}

---

## 🏆 Highest-Converting Keywords & Skills
Technologies present in resumes that converted to recruiter screens or technical interviews:
> {top_kw_str}

---

## 🔄 How the Learning Loop Adapts Your Resumes
```mermaid
graph LR
    A[Apply with Tailored Resume] --> B[Log Status in applications/]
    B --> C{{Status Update}}
    C -->|Interview / OA| D[+Score to Archetype & Bullets]
    C -->|No Response| E[Adjust Keyword Weights]
    D --> F[AI Tailorer Prioritizes Winning Formulas]
    E --> F
```
"""
    DASHBOARD_FILE.write_text(md.strip(), encoding="utf-8")
    print(f"[✓] Analytics Dashboard refreshed: {DASHBOARD_FILE}")

def recommend_best_archetype(job_text: str) -> str:
    data = load_or_init_data()
    text = job_text.lower()

    scores = {arch: 0 for arch in data.get("archetypes", {})}
    if not scores:
        for a in DEFAULT_ARCHETYPES:
            scores[a] = 0

    if any(k in text for k in ["robotics", "controls", "kinematics", "autopilot", "navigation"]):
        scores["Robotics & Autonomous Systems"] = scores.get("Robotics & Autonomous Systems", 0) + 10
    if any(k in text for k in ["embedded", "firmware", "microcontroller", "esp32", "stm32", "rtos", "i2c", "spi"]):
        scores["Embedded Systems & Firmware"] = scores.get("Embedded Systems & Firmware", 0) + 10
    if any(k in text for k in ["hardware", "pcb", "asic", "fpga", "verilog", "circuit", "digital logic"]):
        scores["Hardware & Digital EE"] = scores.get("Hardware & Digital EE", 0) + 10
    if any(k in text for k in ["data", "machine learning", "ai", "pytorch", "deep learning", "llm"]):
        scores["Data Science & AI"] = scores.get("Data Science & AI", 0) + 10
    if any(k in text for k in ["software", "backend", "full stack", "distributed", "algorithms", "c++", "go", "python"]):
        scores["Software Engineering"] = scores.get("Software Engineering", 0) + 8

    # Apply historical win rate boost
    for arch, stats in data.get("archetypes", {}).items():
        if stats.get("applied", 0) > 0:
            rate = stats.get("interviews", 0) / stats.get("applied", 1)
            scores[arch] = scores.get(arch, 0) + (rate * 6)

    return max(scores, key=scores.get)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run adaptive learning analytics.")
    args = parser.parse_args()
    analyze_applications()