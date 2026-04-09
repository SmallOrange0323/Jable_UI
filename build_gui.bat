@echo off
setlocal enabledelayedexpansion

echo =========================================
echo    JableTV Packaging Pro (Auto-Detector)
echo =========================================

:: --- Step 1: Detect Python Command ---
set "PY_CMD="

echo [1/5] Detecting Python...
python --version >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    set "PY_CMD=python"
    echo Found: python
) else (
    py --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_CMD=py"
        echo Found: py
    ) else (
        python3 --version >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set "PY_CMD=python3"
            echo Found: python3
        )
    )
)

if "!PY_CMD!"=="" (
    echo [ERROR] No Python found! 
    echo Please install Python and check "Add to PATH"
    pause
    exit /b
)

:: --- Step 2: Install Dependencies ---
echo [2/5] Installing dependencies using !PY_CMD!...
!PY_CMD! -m pip install pyinstaller customtkinter pillow m3u8 requests selenium beautifulsoup4 pycryptodome tqdm
if !ERRORLEVEL! NEQ 0 (
    echo [WARNING] Pip install might have issues, trying to continue...
)

:: --- Step 3: Create Icon ---
echo [3/5] Generating application icon...
!PY_CMD! -c "from PIL import Image; Image.open('kyarugasm.png').resize((256, 256)).save('app_icon.ico', format='ICO')" 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo [WARNING] Icon generation failed.
)

:: --- Step 4: Check & Download FFmpeg ---
echo [4/5] Checking for FFmpeg dependency...
!PY_CMD! get_ffmpeg.py
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] FFmpeg preparation failed.
    pause
    exit /b
)

:: --- Step 5: Build EXE ---
echo [5/5] Starting Build...
!PY_CMD! -m PyInstaller --clean gui.spec
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Build Failed!
    pause
    exit /b
)

echo.
echo =========================================
echo    BUILD SUCCESS! 
echo    File is in the 'dist' folder.
echo =========================================
pause
