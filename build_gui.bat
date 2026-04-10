@echo off
cd /d "%~dp0"

echo =========================================
echo    JableTV Packaging Pro (Auto-Detector)
echo =========================================

:: --- Step 1: Detect Python ---
echo [1/5] Detecting Python...
set "PY_CMD="

python --version >nul 2>&1
if not errorlevel 1 set "PY_CMD=python"

if "%PY_CMD%"=="" (
    py --version >nul 2>&1
    if not errorlevel 1 set "PY_CMD=py"
)

if "%PY_CMD%"=="" (
    python3 --version >nul 2>&1
    if not errorlevel 1 set "PY_CMD=python3"
)

if "%PY_CMD%"=="" (
    echo [ERROR] No Python found!
    echo Please install Python and check "Add to PATH"
    pause
    exit /b 1
)
echo Found: %PY_CMD%

:: --- Step 2: Install Dependencies ---
echo [2/5] Installing dependencies using %PY_CMD%...
%PY_CMD% -m pip install pyinstaller customtkinter pillow m3u8 requests selenium beautifulsoup4 pycryptodome tqdm
if errorlevel 1 echo [WARNING] Pip install might have issues, trying to continue...

:: --- Step 3: Create Icon ---
echo [3/5] Generating application icon...
%PY_CMD% -c "from PIL import Image; Image.open('kyarugasm.png').resize((256, 256)).save('app_icon.ico', format='ICO')" 2>nul
if errorlevel 1 echo [WARNING] Icon generation failed.

:: --- Step 4: Check & Download FFmpeg ---
echo [4/5] Checking for FFmpeg dependency...
%PY_CMD% get_ffmpeg.py
if errorlevel 1 (
    echo [ERROR] FFmpeg preparation failed.
    pause
    exit /b 1
)

:: --- Step 5: Build EXE ---
echo [5/5] Starting Build...
%PY_CMD% -m PyInstaller --clean gui.spec
if errorlevel 1 (
    echo [ERROR] Build Failed!
    pause
    exit /b 1
)

echo.
echo =========================================
echo    BUILD SUCCESS!
echo    File is in the 'dist' folder.
echo =========================================
pause
