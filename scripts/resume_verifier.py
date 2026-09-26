#!/usr/bin/env python3
"""
Resume Verifier & Hallucination Auditor Engine
Performs adversarial ground-truth authentication, ATS keyword matching,
and metric quantification auditing against candidate_profile.json and Master_Resume.md.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"
MASTER_DIR = REPO_ROOT / "resumes" / "master"

sys.path.insert(0, str(SCRIPT_DIR))
from ats_checker import ATSChecker, POWER_ACTION_VERBS, WEAK_WORDS, STANDARD_TECH_KEYWORDS

class ResumeVerifier:
    def __init__(self, profile_path: Path = None):
        self.profile_path = profile_path or (CONFIG_DIR / "candidate_profile.json")
        self.profile = self._load_profile()
        self.ground_truth = self._extract_ground_truth()
        self.ats_checker = ATSChecker()

    def _load_profile(self) -> Dict[str, Any]:
        if self.profile_path.exists():
            try:
                return json.loads(self.profile_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _extract_ground_truth(self) -> Dict[str, Any]:
        """Extract verified ground truth facts from profile and master resume."""
        companies = set()
        for exp in self.profile.get("experience", []):
            companies.add(exp.get("company", "").lower().strip())

        institutions = set()
        for edu in self.profile.get("education", []):
            institutions.add(edu.get("institution", "").lower().strip())

        # Collect all verified skills
        verified_skills = set()
        for pool, kws in self.profile.get("skill_pools", {}).items():
            for kw in kws:
                cleaned = re.sub(r'\(.*?\)', '', kw).strip().lower()
                verified_skills.add(cleaned)
                for part in re.split(r'[/,]', cleaned):
                    if part.strip():
                        verified_skills.add(part.strip())

        # Extract all numbers, metrics, and units from master bullets
        master_metrics = set()
        all_master_text = []
        for exp in self.profile.get("experience", []):
            all_master_text.extend(exp.get("bullets", []))
        for proj in self.profile.get("projects", []):
            all_master_text.extend(proj.get("bullets", []))

        # Check Master_Resume.md if exists
        master_md = MASTER_DIR / "Master_Resume.md"
        if master_md.exists():
            all_master_text.append(master_md.read_text(encoding="utf-8"))

        combined_master = " ".join(all_master_text)
        
        # Regex to find metrics: e.g., 100 Hz, 400 kHz, 20%, 30%, 4.2 m/s, $2,500, 168 MHz
        metric_pattern = r'\b(?:\d+(?:\.\d+)?|\d+k|\$[0-9,]+|\d+x|\d+\+)\s*(?:%|hz|khz|mhz|ghz|ms|µs|us|m/s|mm|layer|student engineers|requests/sec|events/sec)?\b'
        for match in re.finditer(metric_pattern, combined_master, re.IGNORECASE):
            token = match.group(0).lower().strip()
            if any(c.isdigit() for c in token) and len(token) > 1:
                master_metrics.add(token)

        return {
            "companies": companies,
            "institutions": institutions,
            "verified_skills": verified_skills,
            "master_metrics": master_metrics,
            "master_text": combined_master.lower()
        }

    def verify_hallucinations(self, resume_text: str) -> List[Dict[str, str]]:
        """Adversarially check for unverified claims, fabricated metrics, alien companies, or ungrounded skills."""
        hallucinations = []
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]

        # 1. Company Authentication
        in_experience_section = False
        for line in lines:
            line_upper = line.upper()
            if "EXPERIENCE" in line_upper:
                in_experience_section = True
                continue
            elif in_experience_section and any(sec in line_upper for sec in ["PROJECTS", "EDUCATION", "SKILLS"]):
                in_experience_section = False

            if in_experience_section:
                line_lower = line.lower()
                # If it's a heading line like "Company — Role" or "Company - Role"
                if ("—" in line or " - " in line or " | " in line) and not line.startswith(("•", "-", "*", "\\")):
                    company_match = any(known in line_lower for known in self.ground_truth["companies"])
                    if not company_match and len(line) < 100:
                        hallucinations.append({
                            "category": "Company Authentication",
                            "claim": line,
                            "reason": f"Company/role in '{line}' was not found in verified candidate profile."
                        })

        # 2. Metric & Number Authentication
        # Match currency, percentages, units, counts
        metric_regexes = [
            r'\$\d+(?:,\d+)*(?:\.\d+)?[kKmMbB]?',
            r'\b\d+(?:\.\d+)?%',
            r'\b\d+(?:\.\d+)?\s*(?:hz|khz|mhz|ghz|ms|µs|us|ns|s|m/s|mm|cm|v|mv|ma|a|rpm)\b',
            r'\b\d+(?:\.\d+)?\+?\s*(?:servers|users|clients|engineers|members|trials|benchmarks|schematics|lines|projects|layers)\b'
        ]

        for line in lines:
            if not line.startswith(("•", "-", "*", "\\item")):
                continue

            line_lower = line.lower()
            for pattern in metric_regexes:
                for match in re.finditer(pattern, line_lower, re.IGNORECASE):
                    token = match.group(0).strip()
                    token_norm = re.sub(r'\s+', ' ', token.lower())
                    if token_norm not in self.ground_truth["master_metrics"] and token_norm not in self.ground_truth["master_text"]:
                        # Exclude standard benign words like '1-page', '1st', '2nd'
                        if token_norm not in ["1st", "2nd", "100%", "4-layer"]:
                            hallucinations.append({
                                "category": "Fabricated Metric",
                                "claim": f"'{token}' in bullet: {line[:80]}...",
                                "reason": f"Claimed metric '{token}' does not exist in master ground truth."
                            })

        return hallucinations

    def check_eligibility(self, job_text: str, resume_text: str = "") -> List[Dict[str, str]]:
        """Verify graduation date timeline and employment type constraints."""
        conflicts = []
        if not job_text:
            return conflicts

        job_lower = job_text.lower()
        resume_lower = resume_text.lower() if resume_text else ""

        # Check for graduation requirements
        if re.search(r'november\s+2027\s+or\s+later', job_lower) or re.search(r'november\s+2027\s*[-–]\s*june\s+2028', job_lower) or re.search(r'2028\s+or\s+later', job_lower):
            if "december 2027" in resume_lower:
                # Candidate has selected internship co-op timeline (December 2027), which satisfies eligibility!
                pass
            else:
                conflicts.append({
                    "type": "Graduation Date Adjustment Notice",
                    "detail": "Posting requires graduation of November 2027 or later. Candidate internship track targets Expected December 2027 to fulfill eligibility."
                })

        # Check for internship notice
        if re.search(r'\b(intern|internship|co-op|coop)\b', job_lower):
            conflicts.append({
                "type": "Role Type Notice",
                "detail": "Posting is an Internship / Co-op role. Candidate core directives prioritize Full-time engineering positions."
            })

        return conflicts

    def evaluate_resume(self, resume_text: str, job_text: str = "") -> Dict[str, Any]:
        """Comprehensive audit: Authenticity (40), ATS Match (30), Bullet Quality (20), Formatting (10)."""
        # 1. Hallucination Check
        hallucinations = self.verify_hallucinations(resume_text)
        has_hallucinations = len(hallucinations) > 0
        authenticity_score = 40 if not has_hallucinations else 0

        # 2. Eligibility & Graduation Date Check
        eligibility_conflicts = self.check_eligibility(job_text, resume_text)

        # 3. ATS & Job Match Audit
        job_keywords = self.ats_checker.extract_keywords_from_job(job_text) if job_text else {}
        matched_kw_info = self.ats_checker.match_resume_keywords(resume_text, job_keywords) if job_keywords else {"match_score": 85, "matched": [], "missing": []}
        kw_match_rate = matched_kw_info.get("match_score", 85)
        ats_score = int((kw_match_rate / 100) * 30)

        # 3. Bullet Point Impact & Quantification
        bullet_audit = self.ats_checker.audit_bullets(resume_text)
        quant_rate = bullet_audit.get("quantification_ratio", 60)
        action_verb_rate = bullet_audit.get("power_verb_ratio", 75)
        bullet_score = int(((quant_rate + action_verb_rate) / 200) * 20)

        # 4. Structure & Contact Hygiene
        contact_audit = self.ats_checker.audit_contact_info(resume_text)
        section_audit = self.ats_checker.audit_sections(resume_text)
        structure_score = 10 if (contact_audit.get("score", 0) >= 75 and section_audit.get("passed", True)) else 5

        # Overall Score Calculation
        overall_score = authenticity_score + ats_score + bullet_score + structure_score
        
        # Hard cap if hallucinations exist
        if has_hallucinations:
            overall_score = min(overall_score, 50)

        # Status & Approval Logic
        if has_hallucinations:
            status = "REJECTED_HALLUCINATION"
        elif overall_score >= 90:
            status = "APPROVED"
        else:
            status = "NEEDS_REVISION"

        # Actionable feedback generation
        actionable_feedback = []
        if has_hallucinations:
            for h in hallucinations:
                actionable_feedback.append(f"CRITICAL: Remove unverified claim -> {h['claim']} ({h['reason']})")

        missing_kws = matched_kw_info.get("missing", [])
        if missing_kws:
            # Only recommend keywords the candidate actually possesses!
            valid_missing = [kw for kw in missing_kws if any(kw in sk or sk in kw for sk in self.ground_truth["verified_skills"])]
            if valid_missing:
                actionable_feedback.append(f"ATS Optimization: Integrate verified candidate skills: {', '.join(valid_missing[:6])}")

        if quant_rate < 60:
            actionable_feedback.append(f"Quantification: Only {quant_rate}% of bullets have metrics. Add verified metrics from Master Resume.")

        if bullet_audit.get("weak_words_found"):
            actionable_feedback.append(f"Action Verbs: Replace weak passive words: {', '.join(bullet_audit['weak_words_found'])}")

        return {
            "overall_score": overall_score,
            "status": status,
            "target_threshold": 90,
            "breakdown": {
                "authenticity": f"{authenticity_score}/40",
                "ats_keyword_match": f"{ats_score}/30 ({kw_match_rate}%)",
                "bullet_impact": f"{bullet_score}/20 (Quant: {quant_rate}%, Power Verbs: {action_verb_rate}%)",
                "structure_hygiene": f"{structure_score}/10"
            },
            "hallucinations_detected": hallucinations,
            "eligibility_conflicts": eligibility_conflicts,
            "missing_target_keywords": missing_kws,
            "actionable_feedback": actionable_feedback
        }

    def print_audit_report(self, report: Dict[str, Any]):
        """Format a clean visual terminal scorecard."""
        status_emoji = "✅" if report["status"] == "APPROVED" else ("🚨" if "HALLUCINATION" in report["status"] else "⚠️")
        print("\n" + "=" * 65)
        print(f" {status_emoji} RESUME AUDITOR SCORECARD: {report['overall_score']}/100 [{report['status']}]")
        print("=" * 65)
        print(f"  • Authenticity (Anti-Hallucination): {report['breakdown']['authenticity']}")
        print(f"  • ATS Keyword Match:               {report['breakdown']['ats_keyword_match']}")
        print(f"  • Bullet Impact & Metrics:          {report['breakdown']['bullet_impact']}")
        print(f"  • Structure & Contact Hygiene:      {report['breakdown']['structure_hygiene']}")
        print("-" * 65)

        if report.get("eligibility_conflicts"):
            print("⚠️ ELIGIBILITY & GRADUATION TIMELINE ALERTS:")
            for e in report["eligibility_conflicts"]:
                print(f"   [!] {e['type']}: {e['detail']}")
            print("-" * 65)

        if report["hallucinations_detected"]:
            print("🚨 HALLUCINATIONS DETECTED (MUST FIX):")
            for h in report["hallucinations_detected"]:
                print(f"   [!] {h['category']}: {h['claim']}")
                print(f"       Reason: {h['reason']}")
            print("-" * 65)

        if report["actionable_feedback"]:
            print("🔧 ACTIONABLE REVISION INSTRUCTIONS:")
            for idx, fb in enumerate(report["actionable_feedback"], 1):
                print(f"   {idx}. {fb}")
            print("=" * 65 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit resume against candidate profile and job description.")
    parser.add_argument("--resume", type=str, required=True, help="Path to resume file (txt, md, tex, or pdf)")
    parser.add_argument("--job-text", type=str, default="", help="Target job description text")
    args = parser.parse_args()

    resume_path = Path(args.resume)
    if not resume_path.exists():
        print(f"Error: Resume file '{args.resume}' not found.")
        sys.exit(1)

    if resume_path.suffix.lower() == ".pdf":
        checker = ATSChecker()
        resume_text = checker.extract_text_from_pdf(resume_path)
    else:
        resume_text = resume_path.read_text(encoding="utf-8")

    verifier = ResumeVerifier()
    report = verifier.evaluate_resume(resume_text, args.job_text)
    verifier.print_audit_report(report)
    sys.exit(0 if report["status"] == "APPROVED" else 1)
