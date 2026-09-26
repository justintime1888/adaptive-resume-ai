#!/usr/bin/env python3
"""
Adaptive Resume AI • Web Studio Server
Provides an interactive real-time visual UI for the Dual-Agent Refinement Engine.
Runs locally at http://localhost:8765 with zero external pip dependencies.
"""

import os
import re
import sys
import json
import urllib.parse
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
WEB_DIR = REPO_ROOT / "web"
APPS_DIR = REPO_ROOT / "applications"
TAILORED_PDF_DIR = REPO_ROOT / "resumes" / "tailored" / "PDF"

sys.path.insert(0, str(SCRIPT_DIR))
from refinement_loop import ResumeRefinementEngine, extract_job_metadata
from ats_checker import ATSChecker
from chatgpt_final_audit import open_chatgpt_browser, copy_to_clipboard

PORT = 8765

class StudioRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging
        sys.stdout.write(f"[Web UI] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            index_file = WEB_DIR / "index.html"
            if index_file.exists():
                content = index_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "index.html not found")

        elif path.startswith("/pdf/"):
            filename = urllib.parse.unquote(path[5:])
            pdf_path = TAILORED_PDF_DIR / filename
            if pdf_path.exists() and pdf_path.is_file():
                content = pdf_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f"inline; filename=\"{pdf_path.name}\"")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, f"PDF '{filename}' not found")

        elif path == "/api/applications":
            apps = []
            if APPS_DIR.exists():
                for md_file in sorted(APPS_DIR.glob("*.md"), key=os.path.getmtime, reverse=True):
                    try:
                        text = md_file.read_text(encoding="utf-8")
                        company_m = re.search(r'company:\s*"([^"]+)"', text)
                        role_m = re.search(r'role:\s*"([^"]+)"', text)
                        score_m = re.search(r'audit_score:\s*"([^"]+)"', text)
                        pdf_m = re.search(r'pdf_path:\s*"resumes/tailored/PDF/([^"]+)"', text)
                        if company_m and role_m:
                            apps.append({
                                "company": company_m.group(1),
                                "role": role_m.group(1),
                                "score": score_m.group(1) if score_m else "90/100",
                                "pdf_name": pdf_m.group(1) if pdf_m else None
                            })
                    except Exception:
                        pass

            body = json.dumps(apps).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/latest-prompt":
            prompts = sorted(APPS_DIR.glob("*ChatGPT_Plus_Audit_Prompt.txt"), key=os.path.getmtime, reverse=True)
            if prompts:
                body = json.dumps({"prompt": prompts[0].read_text(encoding="utf-8"), "filename": prompts[0].name}).encode("utf-8")
            else:
                body = json.dumps({"prompt": "", "filename": ""}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/parse-job":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(post_data)
                job_text = payload.get("job_text", "")
                company, role = extract_job_metadata(job_text)
                ats = ATSChecker()
                kws = ats.extract_keywords_from_job(job_text)
                all_kws = []
                for cat_kws in kws.values():
                    all_kws.extend(cat_kws)

                body = json.dumps({
                    "company": company,
                    "role": role,
                    "keywords": all_kws[:12]
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                err_body = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)

        elif path == "/api/refine":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(post_data)
                company = payload.get("company", "").strip()
                role = payload.get("role", "").strip()
                job_text = payload.get("job_text", "").strip()
                target_score = int(payload.get("target_score", 90))
                max_iter = int(payload.get("max_iterations", 3))

                # Auto-extract if omitted or empty
                if not company or not role or any(b in company.lower() for b in ['organization', 'team', 'department']):
                    ext_company, ext_role = extract_job_metadata(job_text)
                    if not company or any(b in company.lower() for b in ['organization', 'team', 'department']):
                        company = ext_company
                    if not role:
                        role = ext_role

                grad_date = payload.get("graduation_date", "").strip()
                chatgpt_feedback = payload.get("chatgpt_feedback", "").strip()
                personal_notes = payload.get("personal_notes", "").strip()

                engine = ResumeRefinementEngine(target_score=target_score, max_iterations=max_iter)
                result = engine.run_refinement_loop(
                    company, 
                    role, 
                    job_text, 
                    grad_override=grad_date,
                    chatgpt_feedback=chatgpt_feedback,
                    personal_notes=personal_notes
                )

                body = json.dumps(result).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                err_body = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)

        elif path == "/api/open-chatgpt":
            open_chatgpt_browser()
            body = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_error(404, "Not Found")

def run_server():
    server_address = ("", PORT)
    try:
        httpd = HTTPServer(server_address, StudioRequestHandler)
    except OSError:
        webbrowser.open(f"http://localhost:{PORT}")
        return

    url = f"http://localhost:{PORT}"
    print("\n" + "=" * 65)
    print(f" 🚀 ADAPTIVE RESUME AI • STUDIO UI READY")
    print(f" 🌐 URL: {url}")
    print(f" 🛡️ Multi-Agent Actor-Critic Refinement Engine Active")
    print("=" * 65)
    print("Press Ctrl+C to stop the server.\n")

    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web studio server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
