@echo off
REM ============================================================
REM  Build Script — IT Forms Downloader 2026
REM  Creates a single-file EXE using PyInstaller
REM ============================================================
REM
REM  Prerequisites (run once):
REM    pip install pyinstaller customtkinter requests Pillow
REM
REM  Usage:
REM    1. Open a Command Prompt in THIS folder
REM    2. Run:  build_exe.bat
REM    3. Find the EXE in:  dist\ITFormsDownloader.exe
REM ============================================================

echo.
echo ====================================================
echo   Building IT Forms Downloader 2026 ...
echo ====================================================
echo.

REM Generate icon if it doesn't exist
if not exist "app_icon.ico" (
    echo Generating app icon ...
    python create_icon.py
)

REM Find customtkinter path for bundling
for /f "delims=" %%i in ('python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"') do set CTK_PATH=%%i

echo CustomTkinter path: %CTK_PATH%
echo.

REM Build with PyInstaller
pyinstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "ITFormsDownloader" ^
    --icon "app_icon.ico" ^
    --add-data "%CTK_PATH%;customtkinter/" ^
    --hidden-import "customtkinter" ^
    --hidden-import "requests" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._tkinter_finder" ^
    it_forms_pro.py

echo.
if exist "dist\ITFormsDownloader.exe" (
    echo ====================================================
    echo   BUILD SUCCESSFUL!
    echo   EXE location:  dist\ITFormsDownloader.exe
    echo   Size:
    for %%A in ("dist\ITFormsDownloader.exe") do echo     %%~zA bytes
    echo ====================================================
) else (
    echo   BUILD FAILED — check errors above
)
echo.
pause
