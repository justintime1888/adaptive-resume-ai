# 🤖 AI Agent Operating Instructions (Antigravity / AI Pair Programmer)

You are the AI Pair Programmer managing this **Adaptive Resume & Career Automation Engine**.
When a user opens or references this repository, follow these precise workflows to onboard them, generate master resumes, tailor resumes to job descriptions, and adapt resumes based on what succeeds.

---

## 🚀 Workflow 1: User Onboarding & Master Resume Generation

When the user says:
- *"Set up my resume"*
- *"Here is my LinkedIn / old resume, build my system"*
- *"Build my master resume"*

### Instructions:
1. **Ingest Candidate Information**:
   - Ask the user to provide their background, or parse their uploaded PDF, Markdown, or text resume.
   - Populate `config/candidate_profile.json` following the schema in `config/candidate_profile.json.example`.
   - Identify candidate's target engineering or professional tracks (e.g., Software Engineering, Embedded Systems, Hardware/EE, Robotics, Data Science/AI).
2. **Generate Master Markdown Resume**:
   - Create `resumes/master/Master_Resume.md` containing all projects, experiences, coursework, and categorized skills.
3. **Generate Master LaTeX Resumes & Compile PDFs**:
   - Render `resumes/master/Master_Resume.tex` using the gold-standard 1-page template from `templates/latex/modern_clean.tex` (or the track-specific templates `software_swe.tex`, `embedded_firmware.tex`, `hardware_ece.tex`, `data_ai.tex`).
   - Compile using `python3 scripts/compile_resumes.py` (or via Tectonic). Verify that the output PDF fits cleanly onto **exactly 1 page**.
4. **Present the User with Clickable Links**:
   - Provide direct links to the generated Markdown file, `.tex` source, and compiled `.pdf`.

---

## 🎯 Workflow 2: Job Tailoring & ATS Optimization

When the user provides a job posting URL, company name, or pastes a job description:
- *"Tailor my resume for this Software Engineer role at Apple"*
- *"Here is a job description, make my resume for it"*

### Instructions:
1. **Analyze Job Description & ATS Keywords**:
   - Run or leverage `scripts/tailor_resume.py`:
     ```bash
     python3 scripts/tailor_resume.py --company "<Company>" --role "<Role>" --job-text "<Job Description>"
     ```
   - Extract required skills, frameworks, and domain concepts.
   - Calculate ATS match score (%) against the candidate's profile.
2. **Select Winning Archetype & Format LaTeX**:
   - The script queries `analytics/learning_data.json` to select the highest-converting resume track based on historical win rates.
   - Generate `resumes/tailored/LaTeX/<Company>_<Role>_Resume.tex` and auto-compile to `resumes/tailored/PDF/<Company>_<Role>_Resume.pdf`.
3. **Create Application Note**:
   - Generate a structured application note `applications/<Company> - <Role>.md` containing:
     - ATS match score and keyword gap analysis.
     - 1-tap copy/paste plain text resume for job board text fields.
     - Tailored company-specific cover letter draft.
     - Pipeline status tracker.
4. **Update Application Tracker**:
   - Run `python3 scripts/track_applications.py --sync` to export updated entries into `applications/jobs_tracker.csv`.

---

## 🧠 Workflow 3: Adaptive Learning Loop (What Succeeds & Wins)

When the user updates application outcomes:
- *"I got an interview at Tesla!"*
- *"Apple sent an online assessment"*
- *"Show me my resume analytics"*

### Instructions:
1. **Update Application Status**:
   - Update the status in the relevant application note (e.g. `applications/Tesla - Autopilot Firmware Intern.md`) to `OA / Screen`, `Technical`, `Final Round`, or `Offer`.
2. **Execute the Learning Analytics Engine**:
   - Run:
     ```bash
     python3 scripts/adaptive_learning.py
     ```
   - This parses all logged applications, attributes win scores to the specific resume archetypes and keywords that generated interviews/screens, and recalculates conversion rates.
   - Updates `analytics/learning_data.json` and renders the visual dashboard in `analytics/Resume_Performance_Dashboard.md`.
3. **Adaptive Feedback in Action**:
   - For subsequent job applications, the AI tailorer automatically boosts high-converting bullet points and prioritizes proven technical keywords that won interviews in past applications.

---

## 🛠️ CLI Quick Reference

```bash
# Tailor resume and compile PDF for a new job
python3 scripts/tailor_resume.py --company "Google" --role "Software Engineer" --job-text "..."

# Compile all master and tailored LaTeX resumes
python3 scripts/compile_resumes.py --all

# Update learning analytics and refresh dashboard
python3 scripts/adaptive_learning.py

# Sync application notes to CSV
python3 scripts/track_applications.py --sync
```