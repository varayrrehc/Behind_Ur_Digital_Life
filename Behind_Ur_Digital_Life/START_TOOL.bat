@echo off
title Behind Ur Digital Life - Cyber Tool
echo.
echo ============================================================
echo   BEHIND UR DIGITAL LIFE - Starting...
echo ============================================================
cd /d "C:\Users\VARA PRASAD\OneDrive\Desktop\SecureMailScope\Behind_Ur_Digital_Life"
echo.
echo [+] Opening browser...
start "" "http://127.0.0.1:8000"
echo [+] Starting server... (Keep this window open)
echo [+] Press CTRL+C to stop the tool.
echo.
python app.py
pause
