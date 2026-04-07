#!/usr/bin/env python3
"""
Build Script — IT Forms Downloader 2026
========================================
Cross-platform Python build script using PyInstaller.

Usage:
  pip install pyinstaller customtkinter requests Pillow
  python build_exe.py

Output:
  dist/ITFormsDownloader.exe  (Windows)
  dist/ITFormsDownloader      (Linux/macOS)
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    root = Path(__file__).parent.resolve()
    os.chdir(root)

    # 1. Generate icon if missing
    icon_path = root / "app_icon.ico"
    if not icon_path.exists():
        print("Generating app icon …")
        subprocess.run([sys.executable, "create_icon.py"], check=True)

    # 2. Find customtkinter installation path
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent

    # 3. Build PyInstaller command
    sep = ";" if sys.platform == "win32" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "ITFormsDownloader",
        "--icon", str(icon_path),
        f"--add-data={ctk_path}{sep}customtkinter/",
        "--hidden-import=customtkinter",
        "--hidden-import=requests",
        "--hidden-import=PIL",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=darkdetect",
        "--collect-all=customtkinter",
        "it_forms_pro.py",
    ]

    print("\n" + "=" * 56)
    print("  Building IT Forms Downloader 2026 …")
    print("=" * 56 + "\n")
    print("Command:", " ".join(cmd[:6]), "…\n")

    result = subprocess.run(cmd)

    # 4. Report result
    exe_ext = ".exe" if sys.platform == "win32" else ""
    exe_path = root / "dist" / f"ITFormsDownloader{exe_ext}"

    print("\n" + "=" * 56)
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  BUILD SUCCESSFUL!")
        print(f"  EXE: {exe_path}")
        print(f"  Size: {size_mb:.1f} MB")
    else:
        print("  BUILD FAILED — check errors above")
    print("=" * 56)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
