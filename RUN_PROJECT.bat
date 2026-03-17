@echo off
chcp 65001 > nul
color 0A

echo.
echo ═══════════════════════════════════════════════════════════════
echo    THE RENOVATION ROADMAP - Complete Project Runner
echo    Malek Karoui (3751935) - CS 4403 Data Mining
echo ═══════════════════════════════════════════════════════════════
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check dependencies
echo [2/4] Checking dependencies...
pip show pandas >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo    CHOOSE WHAT TO RUN:
echo ═══════════════════════════════════════════════════════════════
echo.
echo    [1] Run Full Analysis Pipeline (python main.py)
echo    [2] Launch Interactive Dashboard (streamlit)
echo    [3] Run Both (Pipeline then Dashboard)
echo    [4] Open Results Folder
echo    [5] View GitHub Repository
echo    [6] Open Final Report PDF
echo    [7] Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto run_pipeline
if "%choice%"=="2" goto run_dashboard
if "%choice%"=="3" goto run_both
if "%choice%"=="4" goto open_results
if "%choice%"=="5" goto open_github
if "%choice%"=="6" goto open_report
if "%choice%"=="7" goto end

echo Invalid choice. Exiting...
goto end

:run_pipeline
echo.
echo ═══════════════════════════════════════════════════════════════
echo    RUNNING ANALYSIS PIPELINE
echo ═══════════════════════════════════════════════════════════════
echo.
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Pipeline failed!
    pause
    exit /b 1
)
echo.
echo ═══════════════════════════════════════════════════════════════
echo    PIPELINE COMPLETE! 
echo ═══════════════════════════════════════════════════════════════
echo.
echo Results saved to:
echo   - outputs\figures\      (20 visualizations)
echo   - data\                 (processed datasets)
echo.
set /p open_folder="Open results folder? (y/n): "
if /i "%open_folder%"=="y" start outputs\figures
echo.
pause
goto end

:run_dashboard
echo.
echo ═══════════════════════════════════════════════════════════════
echo    LAUNCHING INTERACTIVE DASHBOARD
echo ═══════════════════════════════════════════════════════════════
echo.
echo Dashboard will open in your browser at http://localhost:8501
echo Press Ctrl+C in this window to stop the dashboard server.
echo.
timeout /t 3
streamlit run src\dashboard.py
goto end

:run_both
echo.
echo ═══════════════════════════════════════════════════════════════
echo    STEP 1/2: RUNNING ANALYSIS PIPELINE
echo ═══════════════════════════════════════════════════════════════
echo.
python main.py
if errorlevel 1 (
    echo [ERROR] Pipeline failed! Skipping dashboard...
    pause
    goto end
)
echo.
echo ═══════════════════════════════════════════════════════════════
echo    STEP 2/2: LAUNCHING DASHBOARD
echo ═══════════════════════════════════════════════════════════════
echo.
echo Pipeline complete! Now opening interactive dashboard...
timeout /t 3
start streamlit run src\dashboard.py
echo.
echo Dashboard starting in background...
echo Press any key to exit (dashboard will remain open)
pause >nul
goto end

:open_results
echo Opening results folder...
start outputs\figures
goto menu

:open_github
echo Opening GitHub repository...
start https://github.com/MalekKaroui/renovation-roadmap
goto menu

:open_report
if exist "final_report.pdf" (
    echo Opening final report...
    start final_report.pdf
) else (
    echo [ERROR] final_report.pdf not found!
    echo Compile it from final_report.tex first.
    pause
)
goto menu

:menu
echo.
echo ═══════════════════════════════════════════════════════════════
echo    WHAT NEXT?
echo ═══════════════════════════════════════════════════════════════
echo.
echo    [1] Run Full Analysis Pipeline
echo    [2] Launch Interactive Dashboard
echo    [3] Run Both
echo    [4] Open Results Folder
echo    [5] View GitHub Repository
echo    [6] Open Final Report PDF
echo    [7] Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto run_pipeline
if "%choice%"=="2" goto run_dashboard
if "%choice%"=="3" goto run_both
if "%choice%"=="4" goto open_results
if "%choice%"=="5" goto open_github
if "%choice%"=="6" goto open_report
if "%choice%"=="7" goto end

echo Invalid choice.
pause
goto menu

:end
echo.
echo ═══════════════════════════════════════════════════════════════
echo    Thank you for using The Renovation Roadmap!
echo ═══════════════════════════════════════════════════════════════
echo.
timeout /t 2
exit