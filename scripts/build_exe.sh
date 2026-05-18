#!/bin/bash
# ============================================================
#  Build Script — IT Forms Downloader 2026 (Linux / WSL)
#  Creates a standalone executable binary using PyInstaller
# ============================================================

set -e

# Automatically move to the project root folder (one level up from scripts/)
cd "$(dirname "$0")/.."

# Core Paths
VENV_DIR=".venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PYINSTALLER_BIN="$VENV_DIR/bin/pyinstaller"

echo "===================================================="
echo "  Building IT Forms Downloader 2026 (WSL Linux) ..."
echo "===================================================="
echo ""

# 1. Ensure virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment ($VENV_DIR) not found. Please run the setup first."
    exit 1
fi

# 2. Ensure pyinstaller is installed in the virtual environment
if [ ! -f "$PYINSTALLER_BIN" ]; then
    echo "PyInstaller not found in virtual environment. Installing now..."
    "$VENV_DIR/bin/pip" install pyinstaller
fi

# 3. Generate icon if it doesn't exist
if [ ! -f "assets/app_icon.ico" ]; then
    echo "Generating app icon ..."
    "$PYTHON_BIN" assets/create_icon.py
fi

# 4. Find customtkinter path for bundling
CTK_PATH=$("$PYTHON_BIN" -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))")

echo "CustomTkinter path: $CTK_PATH"
echo ""

# 5. Build with PyInstaller
# Note: On Linux, the --add-data separator is a COLON (:) instead of a semicolon (;)
"$PYINSTALLER_BIN" \
    --noconfirm \
    --onefile \
    --windowed \
    --name "ITFormsDownloader" \
    --icon "assets/app_icon.ico" \
    --add-data "$CTK_PATH:customtkinter/" \
    --hidden-import "customtkinter" \
    --hidden-import "curl_cffi" \
    --hidden-import "PIL" \
    --hidden-import "PIL._tkinter_finder" \
    it_forms_pro.py

echo ""
if [ -f "dist/ITFormsDownloader" ]; then
    echo "===================================================="
    echo "  BUILD SUCCESSFUL!"
    echo "  Binary location:  dist/ITFormsDownloader"
    echo "  Size: $(du -sh dist/ITFormsDownloader | cut -f1)"
    echo "===================================================="
else
    echo "  BUILD FAILED — check errors above"
    exit 1
fi
echo ""
