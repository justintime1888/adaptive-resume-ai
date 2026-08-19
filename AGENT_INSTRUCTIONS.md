# 🤖 AI Agent Operating Instructions (Antigravity / AI Pair Programmer)

You are the AI Pair Programmer managing this **Adaptive Resume, Interview Prep & Career Automation Engine**.
When a user opens or references this repository, follow these precise workflows to onboard them, generate master resumes, tailor resumes to job descriptions, auto-generate STAR interview dossiers (.docx), and adapt resumes based on what succeeds.

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
2. **Generate Master Markdown Resume**:
   - Create `resumes/master/Master_Resume.md` containing all projects, experiences, coursework, and categorized skills.
3. **Generate Master LaTeX Resumes & Compile PDFs**:
   - Render `resumes/master/Master_Resume.tex` using the gold-standard 1-page template from `templates/latex/modern_clean.tex` (or track-specific templates).
   - Compile using `python3 scripts/compile_resumes.py` (or via Tectonic). Verify that the output PDF fits cleanly onto **exactly 1 page**.

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
2. **Select Winning Archetype & Format LaTeX**:
   - Query `analytics/learning_data.json` to select the highest-converting resume track based on historical win rates.
   - Generate `resumes/tailored/LaTeX/<Company>_<Role>_Resume.tex` and auto-compile to `resumes/tailored/PDF/<Company>_<Role>_Resume.pdf`.
3. **Create Application Note & Sync**:
   - Generate `applications/<Company> - <Role>.md` with 1-tap copy/paste plaintext resume and tailored cover letter draft.
   - Auto-sync to `applications/jobs_tracker.csv` and Google Sheets.

---

## 🎤 Workflow 3: Interview Prep Dossier Generation (.docx & STAR Stories)

When the user has an upcoming interview, OA, or recruiter screen:
- *"I got an interview at Tesla! Make my interview prep"*
- *"Generate interview prep for my Apple screen"*

### Instructions:
1. **Run the Interview Prep Generator**:
   ```bash
   python3 scripts/generate_interview_prep.py --company "<Company>" --role "<Role>" --job-text "<Job Description>"
   ```
2. **Generated Dossier Includes**:
   - **Executive 2-Minute Pitch**: Tailored "Tell me about yourself" elevator pitch.
   - **STAR Story Bank**: Situation, Task, Action, and Quantified Results for core projects and experiences formatted in a polished table.
   - **Difficult Technical Questions & Deep Answers**: Real-time systems, memory management, bus debugging, concurrency, and architecture trade-offs.
   - **Behavioral Curveballs**: "Greatest weakness", technical disagreements, and handling failure.
   - **Reverse Questions**: High-impact questions to ask the hiring manager and principal engineers.
3. **Output File**: Saved directly to `interview_prep/<Company>_<Role>_Interview_Prep.docx`.

---

## 📬 Workflow 4: Email Scraper & Feedback Learning Loop

When the user wants to scan application status updates from Gmail or check what succeeds:
- *"Check my application emails"*
- *"Show me what resumes and keywords are winning"*

### Instructions:
1. **Run the Email Status Scraper**:
   ```bash
   python3 scripts/sync_gmail_tracker.py
   ```
   - Automatically detects rejections, OAs, and interview invitations from Gmail.
   - **Auto-generates the `.docx` Interview Prep packet** the moment an interview invite or OA is detected!
2. **Run Adaptive Learning Analytics**:
   ```bash
   python3 scripts/adaptive_learning.py
   ```
   - Attributes win scores to the resume archetypes and keywords that generated interviews/screens.
   - Renders `analytics/Resume_Performance_Dashboard.md`.
3. **Live Sync to Google Sheets & Discord**:
   - `python3 scripts/sync_google_sheets.py` pushes updated rows to Google Sheets.
   - `scripts/discord_alerts.py` dispatches embeds with attached PDFs and interview dossiers.

---

## 🛠️ CLI Quick Reference

```bash
# Tailor resume and compile PDF for a new job
python3 scripts/tailor_resume.py --company "Tesla" --role "Firmware Engineer" --job-text "..."

# Generate STAR Interview Prep Dossier (.docx)
python3 scripts/generate_interview_prep.py --company "Tesla" --role "Firmware Engineer"

# Scan Gmail for status updates & auto-trigger interview prep
python3 scripts/sync_gmail_tracker.py

# Sync to Google Sheets
python3 scripts/sync_google_sheets.py

# Recalculate learning analytics & refresh dashboard
python3 scripts/adaptive_learning.py
```