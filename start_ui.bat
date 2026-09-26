@echo off
title Adaptive Resume AI Studio
echo ===================================================
echo  Starting Adaptive Resume AI Studio UI...
echo ===================================================
cd /d "%~dp0"
python scripts\web_ui.py
pause
