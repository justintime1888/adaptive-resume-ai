@echo off
title Adaptive Resume AI • Setup
cd /d "%~dp0"
echo ===================================================
echo  Adaptive Resume AI • Automated 1-Click Setup
echo ===================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
pause
