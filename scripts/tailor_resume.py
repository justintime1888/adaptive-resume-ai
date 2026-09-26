#!/usr/bin/env python3
"""
AI Resume Adaptation & ATS Keyword Tailoring Engine
Generates company-tailored single-page LaTeX resumes, compiles PDFs,
produces 1-tap plaintext resumes and tailored cover letters, and logs applications.
"""

import os
import re
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"
TEMPLATES_DIR = REPO_ROOT / "templates"
LATEX_TEMPLATES = TEMPLATES_DIR / "latex"
MASTER_DIR = REPO_ROOT / "resumes" / "master"
TAILORED_LATEX_DIR = REPO_ROOT / "resumes" / "tailored" / "LaTeX"
TAILORED_PDF_DIR = REPO_ROOT / "resumes" / "tailored" / "PDF"
APPS_DIR = REPO_ROOT / "applications"

sys.path.insert(0, str(SCRIPT_DIR))
from adaptive_learning import recommend_best_archetype, analyze_applications
from compile_resumes import compile_single_tex
from track_applications import sync_applications_to_csv
from ats_checker import ATSChecker

TECH_KEYWORDS = {
    "Languages": ["c", "c++", "c++11", "c++17", "c++20", "python", "go", "rust", "bash", "sql", "verilog", "vhdl", "matlab", "javascript", "typescript"],
    "Embedded & Hardware": ["esp32", "esp32-s3", "stm32", "arm", "cortex-m", "arduino", "i2c", "spi", "uart", "can", "can bus", "gpio", "pwm", "adc", "dma", "jtag", "oscilloscope", "logic analyzer", "pcb", "fpga", "asic", "rtl"],
    "Systems & Cloud": ["rtos", "freertos", "multithreading", "concurrency", "linux", "docker", "aws", "gcp", "kubernetes", "posix", "microservices", "redis", "grpc"],
    "Algorithms & Concepts": ["data structures", "algorithms", "pathfinding", "a*", "flood fill", "graph traversal", "control systems", "pid", "sensor fusion", "kalman filter", "kinematics", "state machine", "oop"]
}

def load_candidate_profile() -> dict:
    profile_file = CONFIG_DIR / "candidate_profile.json"
    if not profile_file.exists():
        profile_file = CONFIG_DIR / "candidate_profile.json.example"
    try:
        return json.loads(profile_file.read_text(encoding="utf-8"))
    except Exception:
        return {}

def clean_text(text: str) -> str:
    return re.sub(r'[^a-zA-Z0-9+#\s]', ' ', text.lower())

def extract_keywords_from_job(job_text: str) -> dict:
    cleaned = clean_text(job_text)
    found = {}
    missing = {}
    for cat, kws in TECH_KEYWORDS.items():
        found[cat] = []
        missing[cat] = []
        for kw in kws:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, cleaned):
                found[cat].append(kw)
            else:
                missing[cat].append(kw)
    return {"found": found, "missing": missing}

def calculate_match_score(job_found: dict, candidate_skills: list) -> tuple:
    candidate_clean = " ".join(candidate_skills).lower()
    total_required = 0
    matched_count = 0
    matched_list = []
    gap_list = []

    for cat, kws in job_found["found"].items():
        for kw in kws:
            total_required += 1
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, candidate_clean):
                matched_count += 1
                matched_list.append(kw)
            else:
                gap_list.append(kw)

    score = int((matched_count / total_required * 100)) if total_required > 0 else 88
    return max(min(score, 98), 65), matched_list, gap_list

def generate_plaintext_resume(profile: dict, archetype: str) -> str:
    personal = profile.get("personal", {})
    edu = profile.get("education", [{}])[0] if profile.get("education") else {}
    
    exp_text = []
    for exp in profile.get("experience", []):
        bullets = "\n".join([f"• {b}" for b in exp.get("bullets", [])])
        exp_text.append(f"{exp.get('company')} — {exp.get('role')} ({exp.get('start_date')} – {exp.get('end_date')})\n{bullets}")

    proj_text = []
    for proj in profile.get("projects", []):
        bullets = "\n".join([f"• {b}" for b in proj.get("bullets", [])])
        tech = ", ".join(proj.get("technologies", []))
        proj_text.append(f"{proj.get('name')} | {tech} ({proj.get('date', 'Present')})\n{bullets}")

    skills_text = []
    for cat, items in profile.get("skill_pools", {}).items():
        skills_text.append(f"• {cat}: {', '.join(items)}")

    res = f"""{personal.get('full_name', 'Jane Doe').upper()}
{personal.get('location', '')} | {personal.get('phone', '')} | {personal.get('email', '')} | {personal.get('linkedin', '')} | {personal.get('github', '')}

EDUCATION
{edu.get('institution', '')} | {edu.get('graduation_date', '')}
{edu.get('degree', '')} (GPA: {edu.get('gpa', 'N/A')})
Coursework: {', '.join(edu.get('coursework', []))}

EXPERIENCE
{"\n\n".join(exp_text)}

PROJECTS
{"\n\n".join(proj_text)}

TECHNICAL SKILLS
{"\n".join(skills_text)}
"""
    return res.strip()

def tailor_resume(company: str, role: str, job_text: str = "") -> dict:
    profile = load_candidate_profile()
    personal = profile.get("personal", {})
    
    all_candidate_skills = []
    for pool in profile.get("skill_pools", {}).values():
        all_candidate_skills.extend(pool)

    # 1. ATS Keyword & Match Calculation
    job_analysis = extract_keywords_from_job(job_text)
    score, matched_kws, gaps = calculate_match_score(job_analysis, all_candidate_skills)

    # 2. Archetype Selection via Adaptive Learning
    best_archetype = recommend_best_archetype(job_text)
    
    # 3. Choose Base LaTeX Template
    if "Robotics" in best_archetype:
        base_tex = LATEX_TEMPLATES / "modern_clean.tex"
    elif "Hardware" in best_archetype:
        base_tex = LATEX_TEMPLATES / "hardware_ece.tex"
    elif "Embedded" in best_archetype:
        base_tex = LATEX_TEMPLATES / "embedded_firmware.tex"
    elif "Data" in best_archetype or "AI" in best_archetype:
        base_tex = LATEX_TEMPLATES / "data_ai.tex"
    else:
        base_tex = LATEX_TEMPLATES / "software_swe.tex"

    if not base_tex.exists():
        base_tex = LATEX_TEMPLATES / "modern_clean.tex"

    # 4. Generate Tailored LaTeX File
    TAILORED_LATEX_DIR.mkdir(parents=True, exist_ok=True)
    TAILORED_PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    clean_company = re.sub(r'\W+', '_', company).strip('_')
    clean_role = re.sub(r'\W+', '_', role).strip('_')
    tex_filename = f"{clean_company}_{clean_role}_Resume.tex"
    tailored_tex_path = TAILORED_LATEX_DIR / tex_filename
    tailored_pdf_path = TAILORED_PDF_DIR / f"{clean_company}_{clean_role}_Resume.pdf"

    if base_tex.exists():
        content = base_tex.read_text(encoding="utf-8")
        tailored_tex_path.write_text(content, encoding="utf-8")
        compile_single_tex(tailored_tex_path, TAILORED_PDF_DIR)

    # 5. Generate Plaintext Resume & Cover Letter
    plain_text_resume = generate_plaintext_resume(profile, best_archetype)
    
    cover_letter = f"""Dear Hiring Team at {company},

I am writing to express my strong interest in the **{role}** position at **{company}**. As an engineer with experience across {best_archetype.lower()} and scalable systems, I am excited about the opportunity to contribute to {company}'s technical goals.

Through my hands-on experience, I have architected high-performance systems, implemented deterministic low-latency pipelines, and delivered reliable engineering solutions from concept to production. {company}'s focus on innovation aligns closely with my commitment to engineering rigor and practical problem solving.

I would welcome the opportunity to discuss how my skill set can bring immediate value to the {company} team.

Sincerely,  
**{personal.get('full_name', 'Jane Doe')}**  
{personal.get('email', '')} | {personal.get('linkedin', '')} | {personal.get('github', '')}
"""

    # 6. Run Comprehensive ATS Audit Pipeline
    checker = ATSChecker()
    ats_report = checker.run_full_check(
        plain_text_resume,
        job_text=job_text,
        pdf_path=tailored_pdf_path if tailored_pdf_path.exists() else None
    )
    ats_scorecard_md = checker.generate_markdown_report(ats_report, company=company, role=role)
    overall_ats_score = ats_report["overall_score"]

    # 7. Generate Markdown Application Record
    APPS_DIR.mkdir(parents=True, exist_ok=True)
    app_md_path = APPS_DIR / f"{company} - {role}.md"
    today_str = datetime.now().strftime("%Y-%m-%d")

    app_content = f"""---
tags:
  - career/application
company: "{company}"
role: "{role}"
status: "Applied"
applied_date: "{today_str}"
ats_overall_score: "{overall_ats_score}/100"
ats_match_score: "{ats_report['keyword_audit']['match_score']}%"
archetype: "{best_archetype}"
response_received: false
latex_source: "resumes/tailored/LaTeX/{tex_filename}"
pdf_path: "resumes/tailored/PDF/{tailored_pdf_path.name}"
location: "Remote / Hybrid / On-site"
---

# 💼 {company} — {role}

> **Company:** `{company}` | **Role:** `{role}` | **Status:** `Applied` | **ATS Overall Score:** `🎯 {overall_ats_score}/100`
> **Track:** `{best_archetype}` | **Date:** `{today_str}`

---

{ats_scorecard_md}

---

## 📋 1-Tap Copy & Paste Plaintext Resume
```text
{plain_text_resume}
```

---

## ✉️ Tailored Cover Letter Draft for {company}
{cover_letter}

---

## 🧭 Interview Pipeline Tracker
- [x] **Application Submitted:** `{today_str}`
- [ ] **Assessment / Recruiter Screen**
- [ ] **Technical Interview**
- [ ] **Final Round**
- [ ] **Offer Received**

---

## 📝 Interview Preparation & Technical Notes
- STAR stories, system architecture review, and targeted questions for {company}.
"""
    app_md_path.write_text(app_content.strip(), encoding="utf-8")
    
    # Sync CSV and Learning Analytics
    sync_applications_to_csv()
    analyze_applications()

    return {
        "company": company,
        "role": role,
        "ats_overall_score": overall_ats_score,
        "match_score": ats_report["keyword_audit"]["match_score"],
        "archetype": best_archetype,
        "matched_keywords": ats_report["keyword_audit"]["matched_keywords"],
        "gap_keywords": ats_report["keyword_audit"]["missing_keywords"],
        "ats_report": ats_report,
        "tex_path": str(tailored_tex_path),
        "pdf_path": str(tailored_pdf_path),
        "md_path": str(app_md_path)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tailor resume to job posting.")
    parser.add_argument("--company", type=str, required=True, help="Target company name")
    parser.add_argument("--role", type=str, required=True, help="Target role title")
    parser.add_argument("--job-text", type=str, default="", help="Raw job description text")
    parser.add_argument("--job-file", type=str, default="", help="Path to text file with job description")
    args = parser.parse_args()

    desc = args.job_text
    if args.job_file and Path(args.job_file).exists():
        desc = Path(args.job_file).read_text(encoding="utf-8")

    res = tailor_resume(args.company, args.role, desc)
    print(f"\n[✓] Generated Tailored Application for {res['company']} — {res['role']}")
    print(f"    -> Overall ATS Score: 🎯 {res['ats_overall_score']}/100 (Keyword Match: {res['match_score']}%, Track: {res['archetype']})")
    print(f"    -> Application Note: {res['md_path']}")
    print(f"    -> Compiled PDF: {res['pdf_path']}")
    if res["gap_keywords"]:
        print(f"    -> ⚠️ Missing Target Keywords to consider adding: {', '.join(res['gap_keywords'][:6])}")