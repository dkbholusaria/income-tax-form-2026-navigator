# IT Forms Downloader 2026

Professional desktop application for discovering and downloading Income Tax Forms from the newly launched official [incometaxindia.gov.in](https://www.incometaxindia.gov.in) portal.

**© 2026 DAKSM AND CO LLP**

---

## Features

| Feature              | Description                                              |
|----------------------|----------------------------------------------------------|
| Save-path selector   | Default `D:\IncomeTaxForms2026`, with Browse button      |
| Scan / Rescan        | Fetches all 190 forms via Liferay Search API             |
| Select / Deselect    | Click rows to toggle; Select All / Deselect All buttons  |
| Live filter          | Instant search across form numbers and titles            |
| Download PDFs        | Parallel, stateless, thread-safe downloads with progress |
| Export CSV           | Save discovered forms list as CSV                        |
| Open Folder          | Opens the save directory in Explorer                     |
| Activity Log         | Transparent, real-time URL and status logger             |
| Dark / Light mode    | System-aware appearance toggle                           |

---

## Quick Start (run from source)

1. Clone or download this repository.
2. Install the necessary dependencies listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```
3. Run the application:
```bash
python it_forms_pro.py
```

---

## Build Standalone EXE

### Prerequisites

Ensure you have PyInstaller and all dependencies installed:
```bash
pip install pyinstaller -r requirements.txt
```

### Option A — Python build script (recommended)
Processes app icons automatically and compiles cross-platform:
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

1. Build the standalone EXE first (see above).
2. Install [Inno Setup 6](https://jrsoftware.org/isinfo.php).
3. Open `installer.iss` in the Inno Setup Compiler.
4. Click **Build** (or run `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss` in CMD).
5. Find the completed installer package at: `Output\ITFormsDownloader_Setup_1.1.0.exe`

The installer sets up:
- A desktop shortcut and a Start Menu folder.
- A standard Windows Uninstaller program.

---

## File Structure

```text
ITFormsDownloader/
├── assets/              ← Application icons & creation helper
│   ├── app_icon.ico
│   ├── app_icon.png
│   └── create_icon.py
├── docs/                ← Documentation & Release logs
│   └── release_notes_v1.1.0.md
├── dist/                ← Contains compiled ITFormsDownloader.exe
├── it_forms_pro.py      ← Main application GUI and backend code
├── requirements.txt     ← Project dependency specifications
├── build_exe.py         ← Cross-platform PyInstaller compiler script
├── build_exe.bat        ← Windows compiler batch script
├── installer.iss        ← Inno Setup installer script
├── LICENSE              ← Application License terms
└── README.md            ← This file (documentation)
```

---

## Technical Notes

* **Stateless WAF Bypass Backend:** Uses standard, stateless HTTP requests via `curl_cffi` to mimic Google Chrome's low-level TLS/SSL and HTTP/2 handshakes (`impersonate="chrome124"`). This completely bypasses the official portal's strict Akamai anti-bot firewall without needing heavy browser engines.
* **Format Enforcement:** Sets explicit browser headers (`Accept: application/json`) to ensure the server always outputs structured JSON rather than falling back to XML.
* **Concurrency Thread Safety:** Download threads inside the `ThreadPoolExecutor` perform isolated stateless fetches. This keeps parallel downloading fast, safe, and free from network collisions.
* **No Playwright / Selenium required:** Bypassing firewalls directly at the connection level keeps the compiled standalone executable exceptionally light (~15 MB).
