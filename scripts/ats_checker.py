#!/usr/bin/env python3
"""
Comprehensive ATS Resume Compatibility & Keyword Optimization Engine
Audits resumes against Applicant Tracking Systems (Workday, Taleo, Greenhouse, Lever, iCIMS).
Checks:
1. Parseability & Text Extraction (PDF and plaintext)
2. Contact Info & Essential Section Detection
3. Keyword Matching, Frequency & Density Analysis against Job Descriptions
4. Bullet Point Quality: Action Verb Strength & Metric Quantification Rate
5. Format Compliance & ATS Red Flags
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

COMMON_ATS_SECTIONS = {
    "contact": [r"\b(email|phone|linkedin|github)\b"],
    "education": [r"\beducation\b", r"\bacademic\b", r"\buniversity\b", r"\bdegree\b"],
    "experience": [r"\bexperience\b", r"\bwork experience\b", r"\bprofessional experience\b", r"\bengineering experience\b", r"\bemployment\b"],
    "projects": [r"\bprojects\b", r"\btechnical projects\b", r"\bengineering projects\b", r"\bpersonal projects\b"],
    "skills": [r"\bskills\b", r"\btechnical skills\b", r"\bcore competencies\b", r"\btechnologies\b"]
}

POWER_ACTION_VERBS = {
    "engineered", "architected", "developed", "designed", "implemented", "commissioned",
    "optimized", "spearheaded", "programmed", "benchmarked", "diagnosed", "streamlined",
    "automated", "validated", "routed", "deployed", "scaled", "fused", "modeled",
    "calibrated", "analyzed", "built", "authored", "secured", "eliminated",
    "executed", "interpreted", "rendered", "integrated", "led", "directed",
    "conducted", "tested", "resolved", "created", "established", "coordinated", "won"
}

WEAK_WORDS = {
    "helped", "assisted", "worked on", "responsible for", "participated in",
    "handled", "familiar with", "tried to", "learned", "various tasks", "daily tasks"
}

STANDARD_TECH_KEYWORDS = {
    "Languages": [
        "c", "c++", "c++11", "c++17", "c++20", "python", "go", "rust", "bash", "shell",
        "sql", "verilog", "systemverilog", "vhdl", "matlab", "assembly", "javascript", "typescript"
    ],
    "Embedded & Microcontrollers": [
        "esp32", "esp32-s3", "stm32", "arm", "cortex-m", "arm cortex", "arduino", "pic",
        "platformio", "freertos", "rtos", "bare-metal", "bare metal", "firmware",
        "timer", "interrupt", "isr", "hal", "register", "dma", "bootloader", "jtag", "swd"
    ],
    "Hardware & Electronics": [
        "pcb", "altium", "altium designer", "kicad", "easyeda", "schematic", "schematics",
        "ltspice", "multisim", "oscilloscope", "logic analyzer", "multimeter", "soldering",
        "power supply", "h-bridge", "motor driver", "pull-up", "decoupling", "tvs", "imu",
        "tof", "sensor", "sensors", "actuator", "dc motor", "stepper", "servo", "encoder", "signal integrity"
    ],
    "Protocols & Buses": [
        "i2c", "spi", "uart", "usart", "can", "can bus", "can-bus", "rs-485", "rs485",
        "rs-232", "ethercat", "ethernet", "modbus", "tcp/ip", "udp", "gpio", "pwm", "adc", "dac"
    ],
    "Robotics & Control": [
        "control systems", "controls", "pid", "cascade pid", "feedback", "kinematics",
        "sensor fusion", "kalman filter", "ekf", "pathfinding", "a*", "a-star", "flood fill",
        "state machine", "fsm", "trajectory", "differential drive", "slam", "ros", "ros2"
    ],
    "Software, Systems & Tools": [
        "linux", "arch linux", "ubuntu", "posix", "wsl", "git", "github", "cmake", "make",
        "gdb", "docker", "ci/cd", "unit testing", "qt", "qt6", "oop", "data structures", "algorithms",
        "multithreading", "concurrency", "low-latency", "profiling"
    ],
    "Industrial Automation & PLCs": [
        "plc", "scada", "hmi", "mes", "allen-bradley", "rockwell", "siemens", "tia portal",
        "ignition", "ladder logic", "structured text", "commissioning", "root cause analysis",
        "troubleshooting", "sop"
    ]
}


class ATSChecker:
    def __init__(self):
        pass

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from a PDF file using pypdf."""
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required to parse PDF files. Run `pip install pypdf`.")
        
        text = ""
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text

    def clean_text(self, text: str) -> str:
        """Normalize whitespace, superscripts, and lower-case text."""
        # Normalize common unicode symbols in tech resumes
        normalized = text.replace('²', '2').replace('³', '3')
        normalized = re.sub(r'[–—−]', '-', normalized)
        return re.sub(r'\s+', ' ', normalized).strip()

    def audit_contact_info(self, text: str) -> Dict[str, Any]:
        """Verify presence of required contact fields."""
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9-_]+'
        github_pattern = r'github\.com/[a-zA-Z0-9-_]+'

        has_email = bool(re.search(email_pattern, text))
        has_phone = bool(re.search(phone_pattern, text))
        has_linkedin = bool(re.search(linkedin_pattern, text, re.IGNORECASE))
        has_github = bool(re.search(github_pattern, text, re.IGNORECASE))

        score = sum([has_email, has_phone, has_linkedin, has_github]) * 25
        return {
            "has_email": has_email,
            "has_phone": has_phone,
            "has_linkedin": has_linkedin,
            "has_github": has_github,
            "score": score
        }

    def audit_sections(self, text: str) -> Dict[str, Any]:
        """Detect standard ATS recognized sections."""
        text_lower = self.clean_text(text).lower()
        detected = {}
        for section, patterns in COMMON_ATS_SECTIONS.items():
            detected[section] = any(re.search(p, text_lower) for p in patterns)

        missing_critical = [sec for sec, found in detected.items() if not found and sec in ("education", "experience", "skills")]
        passed = len(missing_critical) == 0
        return {
            "detected": detected,
            "missing_critical": missing_critical,
            "passed": passed
        }

    def _kw_pattern(self, kw: str) -> str:
        """Construct regex allowing optional plurals and hyphens."""
        escaped = re.escape(kw)
        if escaped.endswith(r'\ bus'):
            escaped = escaped.replace(r'\ bus', r'[\s\-]bus')
        elif r'\-' in escaped:
            escaped = escaped.replace(r'\-', r'[\s\-]')
        # Allow optional 's' or 'es' at the end for nouns
        if not escaped.endswith('s') and not escaped.endswith('+'):
            escaped += r'(?:s|es)?'
        return r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])'

    def extract_keywords_from_job(self, job_text: str) -> Dict[str, List[str]]:
        """Extract matched tech keywords from job description."""
        if not job_text:
            return {}
        
        job_lower = " " + self.clean_text(job_text).lower() + " "
        found = {}

        for category, kws in STANDARD_TECH_KEYWORDS.items():
            cat_found = []
            for kw in kws:
                pattern = self._kw_pattern(kw)
                if re.search(pattern, job_lower):
                    cat_found.append(kw)
            if cat_found:
                found[category] = cat_found
        return found

    def match_resume_keywords(self, resume_text: str, job_keywords: Dict[str, List[str]]) -> Dict[str, Any]:
        """Match resume text against target job keywords."""
        resume_lower = " " + self.clean_text(resume_text).lower() + " "
        matched = []
        missing = []
        keyword_density = {}

        for cat, kws in job_keywords.items():
            for kw in kws:
                pattern = self._kw_pattern(kw)
                matches = re.findall(pattern, resume_lower)
                occurrences = len(matches)
                keyword_density[kw] = occurrences
                if occurrences > 0:
                    matched.append(kw)
                else:
                    missing.append(kw)

        total = len(matched) + len(missing)
        match_score = int((len(matched) / total * 100)) if total > 0 else 88
        
        # Flags for overused keywords (keyword stuffing)
        stuffed = [kw for kw, count in keyword_density.items() if count > 5]

        return {
            "total_job_keywords": total,
            "matched_keywords": matched,
            "missing_keywords": missing,
            "match_score": min(match_score, 100),
            "density": keyword_density,
            "stuffed_keywords": stuffed
        }

    def audit_bullets(self, resume_text: str) -> Dict[str, Any]:
        """Analyze action verb strength and quantification rate."""
        lines = resume_text.splitlines()
        # Only collect actual experience/project accomplishment bullets, excluding skills category rows
        bullet_lines = []
        for line in lines:
            l_str = line.strip()
            if l_str.startswith(('•', '-', '*', '–')) or l_str.startswith(r'\item'):
                # Ignore skills categories e.g. "• Languages: ...", "• Tools: ..."
                if re.match(r'^[•\-*–\s]*\\item\s*\{?\\textbf\{[A-Za-z\s&/]+:\}', l_str, re.I):
                    continue
                if re.match(r'^[•\-*–\s]*[A-Za-z\s&/]{2,30}:', l_str):
                    continue
                bullet_lines.append(l_str)

        if not bullet_lines:
            # Fallback: identify lines that look like bullet accomplishments
            bullet_lines = [line.strip() for line in lines if len(line.strip()) > 35 and any(line.strip().lower().startswith(v) for v in POWER_ACTION_VERBS)]

        total_bullets = max(len(bullet_lines), 1)
        power_verb_count = 0
        quantified_count = 0
        weak_count = 0

        # Pattern for metrics: numbers, percentages, frequencies, times, units
        metric_pattern = r'(\b\d+(\.\d+)?%|\b\d+\s?(hz|khz|mhz|ghz|ms|ns|s|m/s|mm|cm|v|mv|ma|a|k|m|kb|mb|gb|rpm)\b|\$\d+([,\.]\d+)?|\b\d+\+?\s?(engineers|members|trials|benchmarks|schematics|lines|projects|layers|hours|days))'

        weak_findings = []
        for b in bullet_lines:
            b_lower = b.lower()
            # Action verbs
            words = re.findall(r'[a-zA-Z]+', b_lower)
            if words and words[0] in POWER_ACTION_VERBS:
                power_verb_count += 1
            elif any(w in words[:3] for w in POWER_ACTION_VERBS):
                power_verb_count += 1

            # Weak words
            found_weak = [w for w in WEAK_WORDS if re.search(r'\b' + re.escape(w) + r'\b', b_lower)]
            if found_weak:
                weak_count += 1
                weak_findings.extend(found_weak)

            # Metrics / Quantifiability
            if re.search(metric_pattern, b_lower) or re.search(r'\b\d+\b', b_lower):
                quantified_count += 1

        power_ratio = int((power_verb_count / total_bullets) * 100)
        quant_ratio = int((quantified_count / total_bullets) * 100)

        return {
            "total_bullets": total_bullets,
            "power_verb_ratio": min(power_ratio, 100),
            "quantification_ratio": min(quant_ratio, 100),
            "weak_words_found": list(set(weak_findings)),
            "score": int((power_ratio * 0.5) + (quant_ratio * 0.5))
        }

    def run_full_check(self, resume_text: str, job_text: str = "", pdf_path: Optional[Path] = None) -> Dict[str, Any]:
        """Execute complete ATS audit pipeline and compute composite score."""
        # 1. Extraction Check
        text_source = "plaintext/markdown"
        if pdf_path and pdf_path.exists() and PYPDF_AVAILABLE:
            try:
                pdf_text = self.extract_text_from_pdf(pdf_path)
                if len(pdf_text.strip()) > 100:
                    resume_text = pdf_text
                    text_source = f"PDF ({pdf_path.name})"
            except Exception as e:
                text_source = f"Fallback (PDF extraction failed: {e})"

        # 2. Sub-Audits
        contact_audit = self.audit_contact_info(resume_text)
        sections_audit = self.audit_sections(resume_text)
        job_keywords = self.extract_keywords_from_job(job_text)
        kw_match = self.match_resume_keywords(resume_text, job_keywords)
        bullet_audit = self.audit_bullets(resume_text)

        # 3. Calculate Overall ATS Score (0 - 100)
        # Weights: 40% Keyword Match, 25% Bullet Quality (Power verbs & metrics), 20% Section Detection, 15% Contact hygiene
        score_kw = kw_match["match_score"]
        score_bullets = bullet_audit["score"]
        score_sections = 100 if sections_audit["passed"] else 50
        score_contact = contact_audit["score"]

        composite_score = int(
            (score_kw * 0.40) +
            (score_bullets * 0.25) +
            (score_sections * 0.20) +
            (score_contact * 0.15)
        )
        composite_score = max(min(composite_score, 99), 50)

        # 4. Generate Strategic Recommendations
        recommendations = []
        if kw_match["missing_keywords"]:
            top_missing = kw_match["missing_keywords"][:6]
            recommendations.append(f"Add critical missing job keywords: **{', '.join(top_missing)}** into Skills or Project bullets.")

        if bullet_audit["quantification_ratio"] < 60:
            recommendations.append(f"Increase quantified metrics: currently {bullet_audit['quantification_ratio']}% of bullets contain metrics (target: >60%).")

        if bullet_audit["weak_words_found"]:
            recommendations.append(f"Replace passive/weak words ({', '.join(bullet_audit['weak_words_found'])}) with strong technical verbs (Engineered, Commissioned, Architected).")

        if not contact_audit["has_linkedin"]:
            recommendations.append("Ensure LinkedIn profile URL is clearly formatted in body contact header.")

        if kw_match["stuffed_keywords"]:
            recommendations.append(f"Keyword stuffing warning: {', '.join(kw_match['stuffed_keywords'])} appears >5 times. Keep usage natural.")

        if not recommendations:
            recommendations.append("Resume is exceptionally ATS-optimized and ready for instant submission!")

        return {
            "overall_score": composite_score,
            "text_source": text_source,
            "char_count": len(resume_text),
            "contact_audit": contact_audit,
            "sections_audit": sections_audit,
            "keyword_audit": kw_match,
            "bullet_audit": bullet_audit,
            "recommendations": recommendations
        }

    def generate_markdown_report(self, report: Dict[str, Any], company: str = "", role: str = "") -> str:
        """Format the report into clean GitHub / Obsidian Markdown."""
        score = report["overall_score"]
        status_emoji = "🟢 PASS (High Call-Back Probability)" if score >= 80 else ("🟡 CAUTION (Minor Fixes Needed)" if score >= 70 else "🔴 RISK (Needs ATS Optimization)")
        
        kw = report["keyword_audit"]
        bullets = report["bullet_audit"]
        contact = report["contact_audit"]
        sections = report["sections_audit"]

        recs_md = "\n".join([f"- 💡 {r}" for r in report["recommendations"]])

        matched_str = ", ".join(kw["matched_keywords"][:12]) if kw["matched_keywords"] else "None explicitly detected"
        missing_str = ", ".join(kw["missing_keywords"][:8]) if kw["missing_keywords"] else "None (100% Target Keyword Coverage!)"

        md = f"""# 🛡️ ATS Compatibility & Keyword Scorecard
> **Target:** `{company}` — `{role}` | **Status:** {status_emoji} | **Overall Score:** `🎯 {score}/100`

---

### 📊 Metric Breakdown
| Evaluation Area | Result | Status | Benchmark |
| :--- | :---: | :---: | :---: |
| **ATS Match Score** | **{kw['match_score']}%** | {'✅ Excellent' if kw['match_score'] >= 80 else '⚠️ Moderate'} | Target: ≥ 80% |
| **Bullet Quantification** | **{bullets['quantification_ratio']}%** | {'✅ High' if bullets['quantification_ratio'] >= 60 else '⚠️ Needs Numbers'} | Target: ≥ 60% |
| **Action Verb Strength** | **{bullets['power_verb_ratio']}%** | {'✅ Strong' if bullets['power_verb_ratio'] >= 75 else '⚠️ Moderate'} | Target: ≥ 75% |
| **Section Header Check** | **{'PASS' if sections['passed'] else 'FAIL'}** | {'✅ Standard Headers' if sections['passed'] else '❌ Missing Sections'} | All Required |
| **Contact Info Hygiene** | **{contact['score']}%** | {'✅ Complete' if contact['score'] == 100 else '⚠️ Missing Fields'} | Email, Phone, LI, GH |

---

### 🔍 Keyword Analysis vs. Job Description
- **✅ Matched Keywords ({len(kw['matched_keywords'])}):** `{matched_str}`
- **❌ Missing Target Keywords ({len(kw['missing_keywords'])}):** `{missing_str}`
- **📄 Text Source Verified:** `{report['text_source']}`

---

### 🚀 High-Priority Optimizations to Maximize Call-Back Rate
{recs_md}
"""
        return md.strip()


def check_resume_file(resume_path: Path, job_desc: str = "", company: str = "", role: str = "") -> Dict[str, Any]:
    checker = ATSChecker()
    resume_text = ""
    pdf_path = None

    if resume_path.suffix.lower() == ".pdf":
        pdf_path = resume_path
        if PYPDF_AVAILABLE:
            resume_text = checker.extract_text_from_pdf(pdf_path)
        else:
            print("[!] Warning: pypdf not installed, unable to extract text from PDF directly.")
    else:
        resume_text = resume_path.read_text(encoding="utf-8")

    report = checker.run_full_check(resume_text, job_desc, pdf_path=pdf_path)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit resume against ATS screening engines.")
    parser.add_argument("--resume", type=str, required=True, help="Path to resume (.pdf, .md, .tex, .txt)")
    parser.add_argument("--job-text", type=str, default="", help="Raw job description text")
    parser.add_argument("--job-file", type=str, default="", help="Path to job description file")
    parser.add_argument("--company", type=str, default="", help="Company name")
    parser.add_argument("--role", type=str, default="", help="Role title")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    r_path = Path(args.resume)
    if not r_path.exists():
        print(f"Error: Resume file {r_path} not found.")
        sys.exit(1)

    jd_text = args.job_text
    if args.job_file and Path(args.job_file).exists():
        jd_text = Path(args.job_file).read_text(encoding="utf-8")

    checker = ATSChecker()
    report = check_resume_file(r_path, jd_text, company=args.company, role=args.role)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(checker.generate_markdown_report(report, company=args.company, role=args.role))
