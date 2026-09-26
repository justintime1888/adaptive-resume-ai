#!/usr/bin/env python3
"""
Method 1: ChatGPT Plus Final Boss Verifier Bridge
Bridges your locally verified resume with your ChatGPT Plus web subscription for final human-in-the-loop review.
Supports:
1. 1-Click Clipboard + Browser launch (opens ChatGPT with prompt primed on clipboard).
2. Playwright automated session (if playwright is installed).
"""

import os
import sys
import json
import webbrowser
import subprocess
import argparse
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"
APPS_DIR = REPO_ROOT / "applications"

def load_prompt_file(prompt_path: Path) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")

def copy_to_clipboard(text: str) -> bool:
    try:
        cmd = ["powershell", "-Command", "Set-Clipboard -Value @'\n" + text + "\n'@"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def open_chatgpt_browser(custom_gpt_url: Optional[str] = None):
    url = custom_gpt_url or "https://chatgpt.com"
    print(f"[*] Opening ChatGPT in your default browser: {url}")
    try:
        if sys.platform == "win32":
            subprocess.run(["cmd", "/c", "start", "", url], shell=True)
        else:
            webbrowser.open(url)
    except Exception:
        webbrowser.open(url)

def run_playwright_automation(prompt_text: str):
    """Optional Playwright automation if installed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] Playwright is not installed. To enable direct automated typing into ChatGPT, run:")
        print("    pip install playwright && playwright install chromium")
        return False

    print("[*] Launching Playwright browser instance...")
    try:
        with sync_playwright() as p:
            # Connect or launch browser
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://chatgpt.com")
            print("[*] Page loaded. You can log in if not already logged in.")
            page.wait_for_timeout(5000)
    except Exception as e:
        print(f"[!] Playwright session notice: {e}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Method 1: ChatGPT Plus Final Verification Bridge")
    parser.add_argument("--prompt-file", type=str, help="Path to generated ChatGPT prompt text file")
    parser.add_argument("--company", type=str, help="Company name to find prompt file automatically")
    parser.add_argument("--role", type=str, help="Role name to find prompt file automatically")
    parser.add_argument("--gpt-url", type=str, default="", help="Optional URL to your Custom GPT in ChatGPT Plus")
    parser.add_argument("--auto-launch", action="store_true", default=True, help="Automatically open browser tab")
    args = parser.parse_args()

    prompt_path = None
    if args.prompt_file:
        prompt_path = Path(args.prompt_file)
    elif args.company and args.role:
        clean_comp = args.company.replace(" ", "_")
        clean_role = args.role.replace(" ", "_")
        candidates = list(APPS_DIR.glob(f"*{clean_comp}*{clean_role}*ChatGPT_Plus*.txt"))
        if candidates:
            prompt_path = candidates[0]

    if not prompt_path or not prompt_path.exists():
        # Look for most recent prompt in applications
        prompts = sorted(APPS_DIR.glob("*ChatGPT_Plus_Audit_Prompt.txt"), key=os.path.getmtime, reverse=True)
        if prompts:
            prompt_path = prompts[0]
            print(f"[*] Using most recent prompt file: {prompt_path.name}")
        else:
            print("[!] No ChatGPT Plus prompt file found. Run refinement_loop.py first.")
            sys.exit(1)

    prompt_text = load_prompt_file(prompt_path)
    print("\n" + "=" * 65)
    print(" 🤖 METHOD 1: CHATGPT PLUS FINAL VERIFICATION BRIDGE")
    print("=" * 65)
    print(f"📄 Prompt Source: {prompt_path.name} ({len(prompt_text.split())} words)")
    
    # 1. Copy to clipboard
    copied = copy_to_clipboard(prompt_text)
    if copied:
        print("✅ [COPIED] Verification prompt is primed on your clipboard.")
    else:
        print("[!] Note: Could not auto-copy to clipboard. Manually copy from the prompt file.")

    # 2. Open ChatGPT Web
    if args.auto_launch:
        open_chatgpt_browser(args.gpt_url if args.gpt_url else None)
        print("👉 In ChatGPT: Simply press Ctrl + V and hit Enter to run final audit!")
    
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
