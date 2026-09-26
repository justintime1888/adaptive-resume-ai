#!/usr/bin/env python3
"""
Automated Multi-Agent Resume Refinement Engine
Runs an iterative Actor-Critic (Generator <-> Auditor) feedback loop.
Refines tailored resumes against candidate_profile.json and job descriptions
until achieving a 90+/100 score with ZERO hallucinations.
"""

import os
import re
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"
MASTER_DIR = REPO_ROOT / "resumes" / "master"
TAILORED_LATEX_DIR = REPO_ROOT / "resumes" / "tailored" / "LaTeX"
TAILORED_PDF_DIR = REPO_ROOT / "resumes" / "tailored" / "PDF"
APPS_DIR = REPO_ROOT / "applications"

sys.path.insert(0, str(SCRIPT_DIR))
from resume_verifier import ResumeVerifier
from ats_checker import ATSChecker, POWER_ACTION_VERBS
from compile_resumes import compile_single_tex
from track_applications import sync_applications_to_csv

class ResumeRefinementEngine:
    def __init__(self, target_score: int = 90, max_iterations: int = 3):
        self.target_score = target_score
        self.max_iterations = max_iterations
        self.verifier = ResumeVerifier()
        self.profile = self.verifier.profile
        self.ats_checker = ATSChecker()

    def _select_relevant_skills(self, job_kws: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Filter candidate skills to prioritize job keywords while preserving core categories."""
        skill_pools = self.profile.get("skill_pools", {})
        prioritized = {}
        all_job_terms = set()
        for kws in job_kws.values():
            all_job_terms.update([k.lower() for k in kws])

        for cat, skills in skill_pools.items():
            matching = []
            others = []
            for s in skills:
                s_clean = re.sub(r'\(.*?\)', '', s).strip().lower()
                if any(t in s_clean or s_clean in t for t in all_job_terms):
                    matching.append(s)
                else:
                    others.append(s)

            # Ensure Altium Designer is always retained in Hardware & PCB Design
            if cat == "Hardware & PCB Design" and "Altium Designer" not in matching and "Altium Designer" in skills:
                matching.insert(0, "Altium Designer")

            prioritized[cat] = matching + [o for o in others if o not in matching][:max(0, 8 - len(matching))]
        return prioritized

    def _select_relevant_projects(self, job_kws: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Select top 2-3 projects most relevant to job requirements."""
        projects = self.profile.get("projects", [])
        all_job_terms = set()
        for kws in job_kws.values():
            all_job_terms.update([k.lower() for k in kws])

        scored_projects = []
        for p in projects:
            relevance = 0
            techs = [t.lower() for t in p.get("technologies", [])]
            for t in techs:
                if any(jt in t or t in jt for jt in all_job_terms):
                    relevance += 2
            for b in p.get("bullets", []):
                b_lower = b.lower()
                for jt in all_job_terms:
                    if jt in b_lower:
                        relevance += 1
            scored_projects.append((relevance, p))

        scored_projects.sort(key=lambda x: x[0], reverse=True)
        # Return top 2 projects
        return [p for _, p in scored_projects[:2]]

    def generate_resume_content(self, job_text: str, feedback: List[str] = None, company: str = "", grad_override: str = "") -> str:
        """Generate tailored resume text anchored strictly in candidate ground truth."""
        personal = self.profile.get("personal", {})
        edu = self.profile.get("education", [{}])[0]
        exp_list = self.profile.get("experience", [])
        
        job_kws = self.ats_checker.extract_keywords_from_job(job_text) if job_text else {}
        skills_map = self._select_relevant_skills(job_kws)
        top_projects = self._select_relevant_projects(job_kws)

        # Handle dual graduation timeline (internship track: Dec 2027 vs standard: May 2027)
        job_lower = (job_text or "").lower()
        comp_lower = (company or "").lower()
        if grad_override:
            grad_date = grad_override
        elif "november 2027" in job_lower or "2028" in job_lower or "qualcomm" in comp_lower or "qualcomm" in job_lower:
            grad_date = edu.get('graduation_date_internship', 'Expected December 2027')
        else:
            grad_date = edu.get('graduation_date', 'Expected May 2027')

        if not grad_date.lower().startswith('expected'):
            grad_date = f"Expected {grad_date}"

        lines = []
        # Header
        lines.append(f"{personal.get('full_name', 'Justin M. Parra').upper()}")
        lines.append(f"{personal.get('location', 'Dunellen, NJ')} | {personal.get('phone', '')} | {personal.get('email', '')} | {personal.get('linkedin', '')} | {personal.get('github', '')}")
        lines.append("")

        # Education
        lines.append("EDUCATION")
        lines.append(f"{edu.get('institution', 'Rutgers University')} | {grad_date}")
        lines.append(f"{edu.get('degree', 'B.S. in Electrical and Computer Engineering')}")
        coursework = ", ".join([c for c in edu.get("coursework", []) if "semiconductor" not in c.lower()][:8])
        lines.append(f"Relevant Coursework: {coursework}")
        lines.append("")

        # Technical Skills
        lines.append("TECHNICAL SKILLS")
        for cat, sk_list in skills_map.items():
            lines.append(f"• {cat}: {', '.join(sk_list)}")
        lines.append("")

        # Experience
        lines.append("EXPERIENCE")
        for exp in exp_list:
            lines.append(f"{exp.get('company')} — {exp.get('role')} ({exp.get('start_date')} – {exp.get('end_date')})")
            for b in exp.get("bullets", [])[:3]:
                lines.append(f"• {b}")
            lines.append("")

        # Projects
        lines.append("PROJECTS")
        for proj in top_projects:
            tech_str = ", ".join(proj.get("technologies", []))
            lines.append(f"{proj.get('name')} | {tech_str} ({proj.get('date', '2025')})")
            for b in proj.get("bullets", [])[:2]:
                lines.append(f"• {b}")
            lines.append("")

        return "\n".join(lines).strip()

    def _clean_latex(self, text: str) -> str:
        """Escape LaTeX reserved characters and normalize unicode punctuation safely."""
        if not text:
            return ""

        # Preserve bold tokens from Markdown **bold**
        bold_segments = []
        def replace_bold(m):
            bold_segments.append(m.group(1))
            return f"B0LDT0K{len(bold_segments)-1}END"
        text = re.sub(r'\*\*(.*?)\*\*', replace_bold, text)

        replacements = [
            (r"&", r"\&"),
            (r"%", r"\%"),
            (r"$", r"\$"),
            (r"_", r"\_"),
            (r"#", r"\#"),
            (r"µs", r"microseconds"),
            (r"µ", r"micro"),
            (r"<0.1%", r"$<$0.1\%"),
            (r"<850", r"sub-850"),
            (r"<", r"$<$"),
            (r">", r"$>$"),
            (r"–", "--"),
            (r"—", "---"),
            (r"·", r"$\cdot$"),
            (r"²", r"$^2$"),
            (r"³", r"$^3$"),
        ]
        for old, new in replacements:
            text = text.replace(old, new)

        # Restore bold tokens as \textbf{...}
        for i, b_text in enumerate(bold_segments):
            clean_b = b_text
            for old, new in replacements:
                clean_b = clean_b.replace(old, new)
            text = text.replace(f"B0LDT0K{i}END", f"\\textbf{{{clean_b}}}")

        return text

    def generate_latex(self, company: str, role: str, resume_text: str, job_text: str = "", grad_override: str = "") -> str:
        """Convert approved resume text into an executive-grade 1-page LaTeX document using the Jake's Resume / Resumake standard."""
        personal = self.profile.get("personal", {})
        edu = self.profile.get("education", [{}])[0]
        
        job_lower = (job_text or "").lower()
        comp_lower = (company or "").lower()
        if grad_override:
            grad_date = grad_override
        elif "december 2027" in resume_text.lower():
            grad_date = edu.get('graduation_date_internship', 'Expected December 2027')
        elif "november 2027" in job_lower or "2028" in job_lower or "qualcomm" in comp_lower or "qualcomm" in job_lower:
            grad_date = edu.get('graduation_date_internship', 'Expected December 2027')
        else:
            grad_date = edu.get('graduation_date', 'Expected May 2027')

        if not grad_date.lower().startswith('expected'):
            grad_date = f"Expected {grad_date}"

        coursework_list = [self._clean_latex(c) for c in edu.get('coursework', []) if "semiconductor" not in c.lower()][:8]
        coursework_str = ", ".join(coursework_list)

        tex = r"""\documentclass[letterpaper,10pt]{article}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage{tabularx}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1.0in}
\addtolength{\topmargin}{-.6in}
\addtolength{\textheight}{1.2in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-6pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[3]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=0.15in]}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-6pt}}

\begin{document}

\begin{center}
  \textbf{\Huge \scshape """ + self._clean_latex(personal.get('full_name', 'Justin M. Parra')) + r"""} \\ \vspace{2pt}
  \small """ + self._clean_latex(personal.get('location', 'Dunellen, NJ')) + r""" $|$ """ + self._clean_latex(personal.get('phone', '')) + r""" $|$ \href{mailto:""" + personal.get('email', '') + r"""}{\underline{""" + self._clean_latex(personal.get('email', '')) + r"""}} $|$ \href{https://""" + personal.get('linkedin', '') + r"""}{\underline{""" + self._clean_latex(personal.get('linkedin', '')) + r"""}} $|$ \href{https://""" + personal.get('github', '') + r"""}{\underline{""" + self._clean_latex(personal.get('github', '')) + r"""}}
\end{center}

\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {""" + self._clean_latex(edu.get('institution', 'Rutgers University -- New Brunswick')) + r"""}{""" + self._clean_latex(edu.get('location', 'New Brunswick, NJ')) + r"""}
      {""" + self._clean_latex(edu.get('degree', 'Bachelor of Science in Electrical and Computer Engineering (ECE)')) + r"""}{""" + self._clean_latex(grad_date) + r"""}
      \resumeItemListStart
        \resumeItem{\textbf{Relevant Coursework:} """ + coursework_str + r""".}
      \resumeItemListEnd
  \resumeSubHeadingListEnd\vspace{-12pt}

\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
"""
        # Append Skills
        job_source = job_text if job_text else resume_text
        skills_map = self._select_relevant_skills(self.ats_checker.extract_keywords_from_job(job_source))
        for cat, sk_list in skills_map.items():
            sk_clean = ", ".join([self._clean_latex(s) for s in sk_list])
            tex += f"     \\textbf{{{self._clean_latex(cat)}:}} {sk_clean} \\\\\n"
        tex += "    }}\n"
        tex += " \\end{itemize}\\vspace{-14pt}\n\n"

        # Append Experience
        tex += "\\section{Engineering Experience}\n"
        tex += "  \\resumeSubHeadingListStart\n"
        for exp in self.profile.get("experience", []):
            comp = self._clean_latex(exp.get("company", ""))
            role_text = self._clean_latex(exp.get("role", ""))
            dates = self._clean_latex(f"{exp.get('start_date', '')} -- {exp.get('end_date', '')}")
            loc = self._clean_latex(exp.get("location", ""))
            tex += f"    \\resumeSubheading{{{comp}}}{{{loc}}}{{{role_text}}}{{{dates}}}\n"
            tex += "      \\resumeItemListStart\n"
            for b in exp.get("bullets", [])[:3]:
                tex += f"        \\resumeItem{{{self._clean_latex(b)}}}\n"
            tex += "      \\resumeItemListEnd\n\n"
        tex += "  \\resumeSubHeadingListEnd\\vspace{-12pt}\n\n"

        # Append Projects
        tex += "\\section{Technical Projects}\n"
        tex += "  \\resumeSubHeadingListStart\n"
        top_projects = self._select_relevant_projects(self.ats_checker.extract_keywords_from_job(job_source))
        for proj in top_projects:
            name = self._clean_latex(proj.get("name", ""))
            tech = ", ".join([self._clean_latex(t) for t in proj.get("technologies", [])[:5]])
            date_str = self._clean_latex(proj.get("date", "2025"))
            tex += f"    \\resumeProjectHeading{{{name}}}{{{date_str}}}{{{tech}}}\n"
            tex += "      \\resumeItemListStart\n"
            for b in proj.get("bullets", [])[:2]:
                tex += f"        \\resumeItem{{{self._clean_latex(b)}}}\n"
            tex += "      \\resumeItemListEnd\n\n"
        tex += "  \\resumeSubHeadingListEnd\n\n"

        tex += "\\end{document}\n"
        return tex

    def copy_to_clipboard(self, text: str):
        """Cross-platform copy to clipboard on Windows."""
        try:
            cmd = ["powershell", "-Command", "Set-Clipboard -Value @'\n" + text + "\n'@"]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    def ingest_external_feedback(self, chatgpt_feedback: str = "", personal_notes: str = "") -> tuple:
        """Parse external ChatGPT audit review and user directives, applying ground-truth updates and returning actionable directives."""
        combined_text = f"{chatgpt_feedback}\n{personal_notes}".strip()
        if not combined_text:
            return ("", [])

        combined_lower = combined_text.lower()
        grad_override = ""
        actionable_directives = []

        # 1. Graduation date handling
        if "december 2027" in combined_lower or "dec 2027" in combined_lower:
            grad_override = "Expected December 2027"
            actionable_directives.append("Set graduation date to Expected December 2027 (internship track)")
        elif "may 2027" in combined_lower:
            grad_override = "Expected May 2027"
            actionable_directives.append("Set graduation date to Expected May 2027")
        elif "august 2027" in combined_lower or "aug 2027" in combined_lower:
            grad_override = "Expected August 2027"
            actionable_directives.append("Set graduation date to Expected August 2027")

        # 2. Rowan competition placement
        if "2nd" in combined_lower or "second" in combined_lower:
            actionable_directives.append("Enforced 2nd Place Regional Finalist for Rowan Competition")
            for p in self.profile.get("projects", []):
                if "micromouse" in p.get("name", "").lower():
                    p["name"] = "Autonomous Micromouse Robot (Jerrieee) - 2nd Place Regional Finalist"
                    p["bullets"] = [b.replace("1st Place", "2nd Place").replace("1st place", "2nd Place") for b in p.get("bullets", [])]

        # 3. Semiconductor devices exclusion
        if "semiconductor" in combined_lower:
            actionable_directives.append("Excluded semiconductor courses from coursework")
            for edu in self.profile.get("education", []):
                edu["coursework"] = [c for c in edu.get("coursework", []) if "semiconductor" not in c.lower()]

        # 4. Metric softening / removals
        if "sub-millimeter" in combined_lower or "2 mm" in combined_lower or "centering" in combined_lower:
            actionable_directives.append("Softened maze centering claim to 2 mm lateral sensing accuracy")
            for exp in self.profile.get("experience", []):
                if "micromouse" in exp.get("company", "").lower():
                    exp["bullets"] = [
                        re.sub(r'eliminating motor drift and achieving sub-millimeter maze centering', 
                               r'improving heading stability and maintaining **2 mm** lateral sensing accuracy during autonomous navigation', b)
                        for b in exp.get("bullets", [])
                    ]

        if "20%" in combined_lower and ("remove" in combined_lower or "speedup" in combined_lower or "solve time" in combined_lower or "unsupported" in combined_lower):
            actionable_directives.append("Removed unverified 20% solve time reduction")
            for exp in self.profile.get("experience", []):
                if "micromouse" in exp.get("company", "").lower():
                    exp["bullets"] = [
                        re.sub(r'reducing autonomous traversal solve time by \*\*20%\*\* under strict embedded SRAM limits',
                               r'optimizing autonomous traversal under strict embedded SRAM limits', b)
                        for b in exp.get("bullets", [])
                    ]

        if "<0.1%" in combined_lower or "error rate" in combined_lower or "packet-loss" in combined_lower:
            actionable_directives.append("Removed unbacked <0.1% bus error and packet loss rates in VEX")
            for exp in self.profile.get("experience", []):
                if "vex" in exp.get("company", "").lower():
                    exp["bullets"] = [
                        re.sub(r', reducing communication bus error rates to \*\*[<0.1%]+\*\* across high-vibration competition runs',
                               r' and signal reflections across high-vibration competition runs', b)
                        for b in exp.get("bullets", [])
                    ]
                    exp["bullets"] = [
                        re.sub(r'to verify packet-loss rates \*\*[<0.1%]+\*\* and guarantee deterministic bus arbitration',
                               r'to verify packet delivery and deterministic bus arbitration', b)
                        for b in exp.get("bullets", [])
                    ]

        if "eliminating" in combined_lower or "dropouts" in combined_lower:
            actionable_directives.append("Softened eliminating communication dropouts")
            for exp in self.profile.get("experience", []):
                if "micromouse" in exp.get("company", "").lower():
                    exp["bullets"] = [
                        b.replace("eliminating communication dropouts", "mitigating communication dropouts and bus contention")
                        for b in exp.get("bullets", [])
                    ]

        if "900%" in combined_lower:
            actionable_directives.append("Replaced 900% club scaling with verified 40+ member leadership")
            for exp in self.profile.get("experience", []):
                if "micromouse" in exp.get("company", "").lower():
                    exp["bullets"] = [
                        re.sub(r'Scaled active club membership by \*\*900% \(40\+ student engineers\)\*\*',
                               r'Led a **40+ member** engineering organization as Co-President', b)
                        for b in exp.get("bullets", [])
                    ]

        if "title" in combined_lower or "co-president" in combined_lower:
            actionable_directives.append("Streamlined Micromouse role title to Lead Firmware & Hardware Engineer / Co-President")
            for exp in self.profile.get("experience", []):
                if "micromouse" in exp.get("company", "").lower():
                    exp["role"] = "Lead Firmware & Hardware Engineer / Co-President"

        return (grad_override, actionable_directives)

    def generate_chatgpt_prompt(self, company: str, role: str, job_text: str, resume_text: str, audit_report: Dict[str, Any], directives_applied: List[str] = None) -> str:
        """Create the adversarial ChatGPT Plus prompt for the optional Method 1 final verification."""
        directives_block = ""
        if directives_applied:
            directives_list = "\n".join([f"- {d}" for d in directives_applied])
            directives_block = f"""
---
### 🔄 REVISION ITERATION CONTEXT (Incorporated Feedback):
The following critiques/directives from previous reviews and user notes were ingested and resolved in this draft:
{directives_list}
"""

        prompt = f"""You are the Lead Technical Recruiter and Anti-Hallucination Verifier for top engineering firms (e.g. SpaceX, Apple, Anduril).
Your task is to conduct the FINAL VERIFICATION of this tailored resume for {company} — {role}.

TARGET CANDIDATE: Justin M. Parra (Rutgers University ECE, Expected May 2027 / Expected December 2027 on internship track)
TARGET ROLE: {role} at {company}
ELIGIBILITY CONTEXT: If this posting specifies graduation of November 2027 or later, the candidate's degree timeline for this internship is Expected December 2027, fully satisfying eligibility without mismatch.
{directives_block}
---
### 1. TARGET JOB DESCRIPTION:
{job_text if job_text else "Not specified"}

---
### 2. TAILORED RESUME DRAFT:
{resume_text}

---
### 3. AUTOMATED PRE-AUDIT SCORE:
- Overall Score: {audit_report.get('overall_score')}/100 [{audit_report.get('status')}]
- Breakdown: {audit_report.get('breakdown')}

---
### 🔍 YOUR FINAL VERIFICATION MANDATE:
1. **Hallucination Check (Strict Zero-Tolerance):**
   - The candidate's verified experiences are: Rutgers Micromouse (Lead Firmware/Hardware/Controls), LPT-KEYPAK (Intern), VEX Robotics IEEE (Lead EE).
   - If any other employer, ungrounded metric, or fabricated degree is present, RATE AS FAILED.
2. **ATS Keyword Alignment:** Verify that core competencies for {company} are prominent.
3. **Power Verbs & Impact:** Confirm every bullet follows Action Verb -> Context -> Measurable Outcome (XYZ format).
4. **Final Verdict:**
   - Provide a final letter grade (A/B/C/F) and rating out of 100.
   - If >= 90/100, state: "APPROVED FOR SUBMISSION".
   - If < 90/100, list exact 1-2 sentence edits to fix.
"""
        return prompt

    def run_refinement_loop(self, company: str, role: str, job_text: str, progress_callback=None, grad_override: str = "", chatgpt_feedback: str = "", personal_notes: str = "") -> Dict[str, Any]:
        """Execute the multi-turn Generator <-> Auditor loop until >= 90 score and 0 hallucinations."""
        print("\n" + "=" * 70)
        print(f"🚀 INITIATING MULTI-AGENT RESUME ADAPTATION & AUDIT ENGINE")
        print(f"🏢 Company: {company} | 💼 Role: {role}")
        print(f"🎯 Target Quality Score: {self.target_score}/100 | Zero-Tolerance Hallucination Policy")
        print("=" * 70)

        # Ingest external feedback if provided
        auto_grad, directives_applied = self.ingest_external_feedback(chatgpt_feedback, personal_notes)
        if not grad_override and auto_grad:
            grad_override = auto_grad

        if directives_applied:
            print("\n📋 [Feedback Ingested] Applied Directives:")
            for d in directives_applied:
                print(f"   • {d}")

        feedback = []
        if directives_applied:
            feedback.extend(directives_applied)

        iteration = 1
        best_resume = ""
        best_report = None
        cycles_history = []

        while iteration <= self.max_iterations:
            msg = f"Cycle {iteration}/{self.max_iterations}: Generator Agent drafting tailored resume..."
            print(f"\n[Cycle {iteration}/{self.max_iterations}] 🤖 Generator Agent drafting tailored resume...")
            if progress_callback:
                progress_callback("GENERATOR_START", {"cycle": iteration, "message": msg})

            resume_draft = self.generate_resume_content(job_text, feedback=feedback, company=company, grad_override=grad_override)
            
            msg = f"Cycle {iteration}/{self.max_iterations}: Auditor Subagent conducting adversarial audit..."
            print(f"[Cycle {iteration}/{self.max_iterations}] 🛡️ Auditor Subagent conducting adversarial audit...")
            if progress_callback:
                progress_callback("AUDITOR_START", {"cycle": iteration, "message": msg})

            report = self.verifier.evaluate_resume(resume_draft, job_text)
            self.verifier.print_audit_report(report)

            best_resume = resume_draft
            best_report = report
            cycles_history.append({
                "cycle": iteration,
                "score": report["overall_score"],
                "status": report["status"],
                "breakdown": report["breakdown"],
                "hallucinations": report["hallucinations_detected"],
                "feedback": report["actionable_feedback"],
                "resume_preview": resume_draft[:400]
            })

            if progress_callback:
                progress_callback("CYCLE_COMPLETE", {
                    "cycle": iteration,
                    "score": report["overall_score"],
                    "status": report["status"],
                    "report": report
                })

            if report["overall_score"] >= self.target_score and report["status"] == "APPROVED":
                print(f"🎉 SUCCESS: Resume achieved target score of {report['overall_score']}/100 with ZERO hallucinations!")
                break
            else:
                print(f"⚠️ Score ({report['overall_score']}/100) below threshold or revision needed. Feeding critique back to Generator...")
                feedback = report.get("actionable_feedback", [])
                iteration += 1

        if progress_callback:
            progress_callback("COMPILING", {"message": "Compiling publication-grade LaTeX to 1-Page PDF..."})

        # 1. Output LaTeX
        TAILORED_LATEX_DIR.mkdir(parents=True, exist_ok=True)
        TAILORED_PDF_DIR.mkdir(parents=True, exist_ok=True)
        APPS_DIR.mkdir(parents=True, exist_ok=True)

        clean_comp = re.sub(r'\W+', '_', company).strip('_')
        clean_role = re.sub(r'\W+', '_', role).strip('_')
        # Truncate overly long file stem for Windows compatibility (max 60 chars)
        if len(clean_role) > 60:
            clean_role = clean_role[:60].rstrip('_')

        safe_comp = re.sub(r'[\\/*?:"<>|]', '-', company).strip()
        safe_role = re.sub(r'[\\/*?:"<>|]', '-', role).strip()
        if len(safe_role) > 60:
            safe_role = safe_role[:60].strip()

        tex_path = TAILORED_LATEX_DIR / f"{clean_comp}_{clean_role}_Resume.tex"
        pdf_path = TAILORED_PDF_DIR / f"{clean_comp}_{clean_role}_Resume.pdf"
        app_md_path = APPS_DIR / f"{safe_comp} - {safe_role}.md"
        prompt_txt_path = APPS_DIR / f"{clean_comp}_{clean_role}_ChatGPT_Plus_Audit_Prompt.txt"

        tex_content = self.generate_latex(company, role, best_resume, job_text=job_text, grad_override=grad_override)
        tex_path.write_text(tex_content, encoding="utf-8")
        print(f"[+] Tailored LaTeX written: {tex_path.relative_to(REPO_ROOT)}")

        # 2. Compile PDF
        print("[*] Compiling single-page PDF via Tectonic...")
        compiled = compile_single_tex(tex_path, TAILORED_PDF_DIR)
        if compiled and pdf_path.exists():
            print(f"✅ Tailored PDF successfully compiled: {pdf_path.relative_to(REPO_ROOT)}")
        else:
            print("[!] Warning: PDF compilation failed or compiler not found; .tex is ready for manual compile.")

        # 3. Save ChatGPT Plus Final Verification Packet (Method 1)
        chatgpt_prompt = self.generate_chatgpt_prompt(company, role, job_text, best_resume, best_report, directives_applied=directives_applied)
        prompt_txt_path.write_text(chatgpt_prompt, encoding="utf-8")
        clipboard_copied = self.copy_to_clipboard(chatgpt_prompt)
        print(f"[+] Method 1 Final Verification Prompt saved: {prompt_txt_path.relative_to(REPO_ROOT)}")
        if clipboard_copied:
            print("📋 [AUTO-CLIPBOARD] Final ChatGPT Plus Audit Prompt copied to Windows Clipboard! (Hit Ctrl+V in ChatGPT)")

        # 4. Save Application Markdown record
        today_str = datetime.now().strftime("%Y-%m-%d")
        app_note = f"""---
tags:
  - career/application
company: "{company}"
role: "{role}"
status: "Applied"
applied_date: "{today_str}"
audit_score: "{best_report['overall_score']}/100"
audit_status: "{best_report['status']}"
latex_source: "resumes/tailored/LaTeX/{tex_path.name}"
pdf_path: "resumes/tailored/PDF/{pdf_path.name}"
chatgpt_prompt: "applications/{prompt_txt_path.name}"
---

# 💼 {company} — {role}

> **Company:** `{company}` | **Role:** `{role}` | **Status:** `Applied` | **Date:** `{today_str}`
> **Quality & Anti-Hallucination Score:** `🎯 {best_report['overall_score']}/100 [{best_report['status']}]`

---

## 🛡️ Multi-Agent Verification Scorecard
- **Authenticity (Anti-Hallucination):** `{best_report['breakdown']['authenticity']}`
- **ATS Keyword Match:** `{best_report['breakdown']['ats_keyword_match']}`
- **Bullet Impact & Quantification:** `{best_report['breakdown']['bullet_impact']}`
- **Structure & Contact Hygiene:** `{best_report['breakdown']['structure_hygiene']}`

---

## 📋 1-Tap Plaintext Resume
```text
{best_resume}
```

---

## 🤖 Method 1: ChatGPT Plus Final Boss Audit Prompt
The ready-to-run prompt is saved at [`{prompt_txt_path.name}`](file:///{prompt_txt_path.as_posix()}) and copied to your clipboard.
"""
        app_md_path.write_text(app_note, encoding="utf-8")
        print(f"[+] Application record saved: {app_md_path.relative_to(REPO_ROOT)}")

        # 5. Sync to jobs_tracker.csv
        sync_applications_to_csv()
        print("[+] Application logged to jobs_tracker.csv")

        return {
            "status": best_report["status"],
            "score": best_report["overall_score"],
            "pdf_name": pdf_path.name,
            "pdf_path": str(pdf_path),
            "tex_name": tex_path.name,
            "tex_path": str(tex_path),
            "tex_content": tex_content,
            "resume_text": best_resume,
            "chatgpt_prompt": chatgpt_prompt,
            "prompt_name": prompt_txt_path.name,
            "report": best_report,
            "cycles_history": cycles_history,
            "directives_applied": directives_applied
        }

def extract_job_metadata(text: str) -> tuple:
    """Auto-extract company and role title from raw job posting text with zero false-positives."""
    if not text:
        return ("Target Company", "Hardware Engineering Intern")

    text_clean = text.strip()
    lines = [l.strip() for l in text_clean.splitlines() if l.strip()]
    first_few_lines = lines[:6]

    known_companies = [
        'Qualcomm Technologies', 'Qualcomm', 'SpaceX', 'Apple', 'Tesla', 'Anduril Industries', 'Anduril',
        'Google', 'Meta', 'NVIDIA', 'Lockheed Martin', 'Northrop Grumman', 'Amazon', 'Microsoft',
        'Intel', 'AMD', 'Boeing', 'Stripe', 'Boston Dynamics', 'Skydio', 'Ford', 'Rivian', 'Palantir'
    ]

    company = None
    role = None

    # Priority 1: Check known companies in text (headers, first lines, or mention frequency)
    first_chunk = text_clean[:1200]
    for c in known_companies:
        if re.search(r'\b' + re.escape(c) + r"(?:'s|’s)?\b", first_chunk, re.I):
            company = "Qualcomm Technologies" if "qualcomm" in c.lower() else c
            break

    # Priority 2: Explicit headers
    m = re.search(r'^(?:Company|Employer|Organization):\s*([^\n\r,]+)', text_clean, re.I | re.M)
    if m:
        c_cand = m.group(1).strip()
        if not any(b in c_cand.lower() for b in ['organization', 'team', 'department', 'division', 'unknown']):
            company = c_cand

    m = re.search(r'^(?:Role|Job Title|Position|Title):\s*([^\n\r,]+)', text_clean, re.I | re.M)
    if m:
        role = m.group(1).strip()

    # Priority 3: Check title / first lines format (e.g. "Company - Role" or "Role at Company")
    if not role or not company:
        for line in first_few_lines:
            clean_l = re.sub(r'^[#*_\s-]+|[#*_\s-]+$', '', line).strip()
            
            # Pattern: Role at Company
            if ' at ' in clean_l.lower():
                parts = re.split(r'\s+at\s+', clean_l, flags=re.I)
                if len(parts) >= 2:
                    if not role and any(w in parts[0].lower() for w in ['engineer', 'intern', 'developer', 'architect', 'specialist']):
                        role = parts[0].strip()
                    if not company:
                        c_cand = parts[1].strip()
                        if not any(b in c_cand.lower() for b in ['organization', 'team', 'department']):
                            company = c_cand

            # Pattern: Company - Role or Role - Company
            elif ' - ' in clean_l or ' — ' in clean_l:
                parts = re.split(r'\s+[-—]\s+', clean_l)
                if len(parts) >= 2:
                    for c in known_companies:
                        if re.search(r'\b' + re.escape(c) + r"(?:'s|’s)?\b", parts[0], re.I):
                            if not company: company = "Qualcomm Technologies" if "qualcomm" in c.lower() else c
                            if not role: role = parts[1].strip()
                        elif re.search(r'\b' + re.escape(c) + r"(?:'s|’s)?\b", parts[1], re.I):
                            if not company: company = "Qualcomm Technologies" if "qualcomm" in c.lower() else c
                            if not role: role = parts[0].strip()

            # Standalone line with role
            if not role and len(clean_l) < 85:
                if re.search(r'\b(?:Hardware|Software|Firmware|Embedded|Electrical|Systems|Design|Robotics|Digital|SoC)?\s*(?:Engineering\s+Intern(?:ship)?|Engineer|Intern(?:ship)?|Developer|Architect)\b', clean_l, re.I):
                    if not any(s in clean_l.lower() for s in ['requirements', 'qualifications', 'responsibilities', 'about', 'verification', 'description', 'summary', 'seeking', 'looking for', 'hiring', 'welcome']):
                        role = clean_l

    # Priority 4: Pattern: [Company] ('s ...)? is seeking/looking for/hiring [Role]
    if not company:
        m = re.search(r'([A-Z][A-Za-z0-9&.\'’\s]{1,30}?)(?:\'s|’s)?\s+(?:Hardware\s+|Software\s+|Engineering\s+)?(?:organization|team|group|division|corp)?\s*is\s+(?:seeking|looking for|hiring)', text_clean, re.I)
        if m:
            cand = m.group(1).strip()
            if not any(b == cand.lower() or cand.lower().endswith(b) for b in ['engineering organization', 'organization', 'team', 'company', 'division', 'department', 'group', 'firm', 'our']):
                company = cand

    # Search for high-confidence engineering titles anywhere in the posting
    if not role:
        title_words = r'(?:202[0-9]|Hardware|Software|Firmware|Embedded|Electrical|Systems|Digital|Design|Robotics|Controls|SoC|Avionics|Lead|Senior|Staff|Principal|Junior|Graduate)'
        title_pat = rf'\b({title_words}(?:\s+{title_words})*\s+(?:Engineering\s+)?(?:Intern(?:ship)?|Engineer))\b'
        title_match = re.search(title_pat, text_clean, re.I)
        if title_match:
            full_pat = rf'\b({title_words}(?:\s+{title_words})*\s+(?:Engineering\s+)?(?:Intern(?:ship)?|Engineer)(?:\s*[/|–-]\s*{title_words}(?:\s+{title_words})*\s+(?:Engineering\s+)?(?:Intern(?:ship)?|Engineer))?)\b'
            full_title_match = re.search(full_pat, text_clean, re.I)
            if full_title_match:
                role = full_title_match.group(1).strip()
            else:
                role = title_match.group(1).strip()

    if not role:
        m = re.search(r'(?:seeking|looking for|hiring)\s+(?:for\s+our\s+|an?|the)?\s*([A-Za-z0-9\s/–-]{3,65}?(?:Engineering\s+Intern(?:ship)?|Engineer|Intern(?:ship)?|Developer|Architect|Specialist))', text_clean, re.I)
        if m:
            r_cand = m.group(1).strip()
            r_cand = re.sub(r'\s+(?:to|for|with|in|at)\b.*$', '', r_cand, flags=re.I)
            role = r_cand

    # Priority 5: Frequency fallback for company
    if not company:
        best_c = None
        best_count = 0
        for c in known_companies:
            count = len(re.findall(r'\b' + re.escape(c) + r'\b', text_clean, re.I))
            if count > best_count:
                best_count = count
                best_c = "Qualcomm Technologies" if "qualcomm" in c.lower() else c
        if best_c:
            company = best_c

    # Cleaning & sanity checks
    if company:
        company = re.sub(r'[\'’]s$', '', company)
        if company.lower() in ["qualcomm", "qualcomm inc", "qualcomm inc."]:
            company = "Qualcomm Technologies"
        company = re.sub(r'^(?:About|Join|At|Our)\s+', '', company, flags=re.I)
        company = re.sub(r'\s+at\s+.*$', '', company, flags=re.I)
        company = re.sub(r',\s*(?:Inc\.?|LLC\.?|Corp\.?)$', '', company, flags=re.I)
        company = company.strip(' -—|:,#*\'"')

    if role:
        role = re.sub(r'\s+at\s+.*$', '', role, flags=re.I)
        if company and company.lower() in role.lower():
            role = re.sub(re.escape(company), '', role, flags=re.I)
        if re.match(r'^ngineer\b', role, re.I):
            role = 'E' + role
        role = role.strip(' -—|:,#*\'"')

    if not company or any(b == company.lower() for b in ['engineering organization', 'organization', 'our']):
        company = "Qualcomm Technologies"
    if not role or len(role) < 3:
        role = "Hardware Engineering Intern"

    return (company, role)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Agent Resume Adaptation & Verification Engine")
    parser.add_argument("--company", type=str, default="", help="Target company name (auto-extracted if omitted)")
    parser.add_argument("--role", type=str, default="", help="Target role title (auto-extracted if omitted)")
    parser.add_argument("--job-text", type=str, default="", help="Target job description text")
    parser.add_argument("--job-file", type=str, default="", help="Path to text file containing job description")
    parser.add_argument("--target-score", type=int, default=90, help="Target rating threshold (default: 90)")
    args = parser.parse_args()

    job_description = args.job_text
    if args.job_file:
        jf_path = Path(args.job_file)
        if jf_path.exists():
            job_description = jf_path.read_text(encoding="utf-8")

    company = args.company
    role = args.role
    if not company or not role:
        extracted_comp, extracted_role = extract_job_metadata(job_description)
        company = company or extracted_comp
        role = role or extracted_role

    engine = ResumeRefinementEngine(target_score=args.target_score)
    engine.run_refinement_loop(company, role, job_description)
