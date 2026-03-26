@echo off
chcp 65001 > nul
color 0A
setlocal

cd /d "%~dp0"

echo.
echo ═══════════════════════════════════════════════════════════════
echo    THE RENOVATION ROADMAP - Project Runner
echo    Malek Karoui (3751935) - CS 4403 Data Mining
echo ═══════════════════════════════════════════════════════════════
echo.

REM -----------------------------------------------------------------
REM Check that the virtual environment exists
REM -----------------------------------------------------------------
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Please create it first with: python -m venv venv
    pause
    exit /b 1
)

REM -----------------------------------------------------------------
REM Activate environment
REM -----------------------------------------------------------------
echo [1/2] Activating virtual environment...
call venv\Scripts\activate.bat

REM -----------------------------------------------------------------
REM Check dependencies
REM -----------------------------------------------------------------
echo [2/2] Checking dependencies...
pip show pandas >nul 2>&1
if errorlevel 1 (
    echo Required packages not found. Installing from requirements.txt...
    pip install -r requirements.txt
)

:menu
echo.
echo ═══════════════════════════════════════════════════════════════
echo    CHOOSE WHAT TO RUN
echo ═══════════════════════════════════════════════════════════════
echo.
echo    [1] Run Full Analysis Pipeline
echo    [2] Launch Interactive Dashboard
echo    [3] Run Both (Pipeline, then Dashboard)
echo    [4] Open Results Folder
echo    [5] Open GitHub Repository
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

echo.
echo Invalid choice. Please try again.
pause
goto menu

:run_pipeline
echo.
echo ═══════════════════════════════════════════════════════════════
echo    RUNNING ANALYSIS PIPELINE
echo ═══════════════════════════════════════════════════════════════
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] The pipeline did not complete successfully.
    pause
    goto menu
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo    PIPELINE COMPLETE
echo ═══════════════════════════════════════════════════════════════
echo.
echo Results saved to:
echo   - outputs\figures\   (visualizations)
echo   - data\              (processed results)
echo.

set /p open_folder="Open results folder now? (y/n): "
if /i "%open_folder%"=="y" start "" "outputs\figures"

pause
goto menu

:run_dashboard
echo.
echo ═══════════════════════════════════════════════════════════════
echo    LAUNCHING INTERACTIVE DASHBOARD
echo ═══════════════════════════════════════════════════════════════
echo.
echo The dashboard will open in your browser at:
echo   http://localhost:8501
echo.
echo Press Ctrl+C in this window to stop the dashboard.
echo.
timeout /t 2 >nul
streamlit run src\dashboard.py
goto menu

:run_both
echo.
echo ═══════════════════════════════════════════════════════════════
echo    STEP 1/2: RUNNING ANALYSIS PIPELINE
echo ═══════════════════════════════════════════════════════════════
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] The pipeline failed, so the dashboard was not launched.
    pause
    goto menu
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo    STEP 2/2: LAUNCHING DASHBOARD
echo ═══════════════════════════════════════════════════════════════
echo.
echo Pipeline finished successfully.
echo Starting the dashboard in a new window...
echo.
timeout /t 2 >nul

start "" cmd /k "call venv\Scripts\activate.bat && streamlit run src\dashboard.py"

echo Dashboard launched in a separate window.
echo Press any key to return to the menu.
pause >nul
goto menu

:open_results
echo.
echo Opening results folder...
start "" "outputs\figures"
goto menu

:open_github
echo.
echo Opening GitHub repository...
start "" "https://github.com/MalekKaroui/renovation_roadmap"
goto menu

:open_report
echo.
if exist "final_report.pdf" (
    echo Opening final report...
    start "" "final_report.pdf"
) else (
    echo [ERROR] final_report.pdf was not found.
    echo Compile final_report.tex first.
    pause
)
goto menu

:end
echo.
echo ═══════════════════════════════════════════════════════════════
echo    Thank you for using The Renovation Roadmap
echo ═══════════════════════════════════════════════════════════════
echo.
timeout /t 2 >nul
exit