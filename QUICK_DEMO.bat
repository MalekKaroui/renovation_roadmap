@echo off
chcp 65001 > nul
color 0B

echo.
echo ═══════════════════════════════════════════════════════════════
echo    THE RENOVATION ROADMAP - LIVE DEMO MODE
echo ═══════════════════════════════════════════════════════════════
echo.
echo This will:
echo   1. Run the analysis pipeline (shows live output)
echo   2. Launch the interactive dashboard
echo   3. Open the results folder
echo.
echo Press any key to start the demo...
pause >nul

REM Activate venv
call venv\Scripts\activate.bat

echo.
echo ═══════════════════════════════════════════════════════════════
echo    RUNNING ANALYSIS PIPELINE (This takes ~30 seconds)
echo ═══════════════════════════════════════════════════════════════
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Something went wrong!
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo    PIPELINE COMPLETE! Opening dashboard...
echo ═══════════════════════════════════════════════════════════════
echo.
timeout /t 2

REM Open dashboard
start streamlit run src\dashboard.py

REM Wait for dashboard to start
timeout /t 5

REM Open results folder in background
start outputs\figures

echo.
echo ═══════════════════════════════════════════════════════════════
echo    DEMO READY!
echo ═══════════════════════════════════════════════════════════════
echo.
echo Dashboard is running at: http://localhost:8501
echo Results folder is open in File Explorer
echo.
echo Press any key to stop the dashboard...
pause >nul

REM Kill streamlit (optional)
taskkill /F /IM streamlit.exe 2>nul
echo Dashboard stopped.
timeout /t 2