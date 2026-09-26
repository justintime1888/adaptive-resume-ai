#!/usr/bin/env python3
"""
Cross-Platform LaTeX & Tectonic Resume Compiler
Compiles master and tailored .tex files into clean single-page PDFs.
Supports native Tectonic, WSL Tectonic fallback, and pdflatex.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
MASTER_DIR = REPO_ROOT / "resumes" / "master"
TAILORED_LATEX_DIR = REPO_ROOT / "resumes" / "tailored" / "LaTeX"
TAILORED_PDF_DIR = REPO_ROOT / "resumes" / "tailored" / "PDF"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def compile_single_tex(tex_path: Path, output_pdf_dir: Path = None) -> bool:
    if not tex_path.exists():
        print(f"[!] File not found: {tex_path}")
        return False

    work_dir = tex_path.parent
    tex_filename = tex_path.name
    target_pdf_name = tex_path.stem + ".pdf"

    # Try 1: Native tectonic
    try:
        cmd = ["tectonic", tex_filename]
        res = subprocess.run(cmd, cwd=work_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            _post_compile(work_dir / target_pdf_name, output_pdf_dir)
            return True
    except Exception:
        pass

    # Try 2: WSL tectonic (if running on Windows)
    if sys.platform == "win32":
        try:
            win_path = str(work_dir).replace('\\', '/')
            if len(win_path) >= 2 and win_path[1] == ':':
                drive = win_path[0].lower()
                wsl_dir = f"/mnt/{drive}{win_path[2:]}"
            else:
                wsl_dir = win_path
            res = subprocess.run(["wsl", "bash", "-c", f"cd '{wsl_dir}' && tectonic '{tex_filename}'"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                _post_compile(work_dir / target_pdf_name, output_pdf_dir)
                return True
        except Exception:
            pass

    # Try 3: pdflatex
    try:
        res = subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename],
                             cwd=work_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            _post_compile(work_dir / target_pdf_name, output_pdf_dir)
            return True
    except Exception:
        pass

    print(f"[!] Failed to compile {tex_filename}. Ensure Tectonic or pdflatex is installed.")
    return False

def _post_compile(generated_pdf: Path, output_pdf_dir: Path = None):
    if output_pdf_dir and generated_pdf.exists() and output_pdf_dir != generated_pdf.parent:
        output_pdf_dir.mkdir(parents=True, exist_ok=True)
        dest = output_pdf_dir / generated_pdf.name
        import shutil
        shutil.copy2(generated_pdf, dest)

def compile_all():
    print("=== Compiling All LaTeX Resumes ===")
    count = 0
    # Master resumes
    for tex in MASTER_DIR.glob("*.tex"):
        print(f"[*] Compiling Master: {tex.name}...")
        if compile_single_tex(tex, MASTER_DIR):
            print(f"    -> [✓] Success: {tex.stem}.pdf")
            count += 1

    # Tailored resumes
    for tex in TAILORED_LATEX_DIR.glob("*.tex"):
        print(f"[*] Compiling Tailored: {tex.name}...")
        if compile_single_tex(tex, TAILORED_PDF_DIR):
            print(f"    -> [✓] Success: {tex.stem}.pdf")
            count += 1
            
    print(f"=== Finished compiling {count} resumes! ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile LaTeX resumes to PDF.")
    parser.add_argument("file", nargs="?", help="Specific .tex file to compile")
    parser.add_argument("--all", action="store_true", help="Compile all master and tailored resumes")
    args = parser.parse_args()

    if args.all or not args.file:
        compile_all()
    else:
        target = Path(args.file)
        out_dir = TAILORED_PDF_DIR if target.parent == TAILORED_LATEX_DIR else None
        if compile_single_tex(target, out_dir):
            print(f"[+] Compiled successfully: {target.stem}.pdf")