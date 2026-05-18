# IT Forms Downloader 2026

Professional desktop application for downloading Income Tax Forms from
[incometaxindia.gov.in](https://www.incometaxindia.gov.in).

**© 2026 DAKSM AND CO LLP**

---

## Features

| Feature              | Description                                              |
|----------------------|----------------------------------------------------------|
| Save-path selector   | Default `D:\IncomeTaxForms2026`, with Browse button      |
| Scan / Rescan        | Fetches all 190 forms via Liferay API                    |
| Select / Deselect    | Click rows to toggle; Select All / Deselect All buttons  |
| Live filter          | Instant search across form numbers and titles            |
| Download PDFs        | Parallel downloads with progress bar                     |
| Export CSV           | Save discovered forms list as CSV                        |
| Open Folder          | Opens the save directory in Explorer                     |
| Activity Log         | Timestamped, colour-coded log                            |
| Dark / Light mode    | System-aware appearance toggle                           |

---

## Quick Start (run from source)

```bash
pip install customtkinter requests Pillow
python it_forms_pro.py
```

---

## Build Standalone EXE

### Prerequisites

```bash
pip install pyinstaller customtkinter requests Pillow
```

### Option A — Python build script (recommended)

```bash
python build_exe.py
```

### Option B — Batch file (Windows only)

```bash
build_exe.bat
```

Output: `dist\ITFormsDownloader.exe` (~15–20 MB)

---

## Create Windows Installer

1. Build the EXE first (see above)
2. Install [Inno Setup 6](https://jrsoftware.org/isinfo.php)
3. Open `installer.iss` in Inno Setup Compiler → Build
4. Find the installer at: `Output\ITFormsDownloader_Setup_1.0.0.exe`

The installer creates:
- Start Menu shortcut
- Desktop shortcut (optional)
- Standard Windows uninstaller

---

## File Structure

```
ITFormsDownloader/
├── it_forms_pro.py      ← Main application (GUI + backend)
├── create_icon.py       ← Generates app_icon.ico
├── app_icon.ico         ← Application icon
├── app_icon.png         ← Icon in PNG format
├── build_exe.py         ← Cross-platform PyInstaller build script
├── build_exe.bat        ← Windows batch build script
├── installer.iss        ← Inno Setup installer script
└── README.md            ← This file
```

---

## Technical Notes

- **Backend**: Uses plain HTTP `requests` (no browser engine needed).  
  The app calls the same Liferay Search API that the website's JavaScript uses.
- **Frontend**: `customtkinter` for modern themed widgets.
- **Packaging**: PyInstaller bundles everything into a single EXE.
- **No Playwright needed**: The earlier version required Playwright + Firefox.  
  This version uses direct HTTP which makes the EXE compact (~15 MB vs ~150 MB).
