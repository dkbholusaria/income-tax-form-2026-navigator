# Release Title: `v1.1.0 — Akamai WAF Bypass & Enhanced Real-Time Logging`

## 🚀 Overview
Welcome to **v1.1.0** of the **Income Tax Form 2026 Navigator**! This release brings a major rewrite of our backend request engine to fully support the newly launched official **Income Tax Forms 2026 Portal**.

We have successfully bypassed the strict **Akamai WAF (Web Application Firewall)** security blocks that previously resulted in `403 Forbidden` errors, restored 100% accurate JSON parsing, and implemented stateless concurrent downloading.

---

## 🌟 What's New in v1.1.0

### 🛡️ Akamai WAF Bypass via Browser Impersonation
The official backend is now protected by Akamai's anti-bot system, which blocks standard Python request handshakes. We have integrated `curl_cffi` to mimic the low-level **SSL/TLS (JA3/JA4) fingerprint** and **HTTP/2 settings** of a real Google Chrome browser. The script now effortlessly flies under Akamai's radar with zero blockages.

### ⚙️ Fixed JSON Decoder Fallback (`JSONDecodeError` Fixed)
Resolved the critical `Expecting value: line 1 column 1 (char 0)` error. By using direct browser-like requests with explicit `Accept: application/json` headers, we force the Liferay API to reliably return structured JSON data instead of falling back to default XML payloads.

### 🧵 100% Thread-Safe Concurrent Downloader
Refactored the multi-threaded PDF downloader (`download_one_form`) to utilize stateless, isolated request workers. Each thread now initiates its own connection. This guarantees thread isolation inside the `ThreadPoolExecutor`, completely eliminating connection pools colliding or leaking handles.

### 📝 Enhanced Real-Time Log Transparency
We have made the UI Activity Log fully transparent! The log box now outputs the exact full URLs and pages being visited in real time:
* **Scanning:** Shows the base portal domain and the page numbers of the Search API queried.
* **Downloading:** Logs the exact source PDF link (`https://.../documents/d/guest/...`) alongside the form number and download success confirmation.

---

## 🔧 Installation & Prerequisites

### For Standalone Executable (EXE) Users
* Simply download and run **`ITFormsDownloader.exe`** from the assets below. No installation or Python setup required!

### For Source Code Users (`.py`)
If running directly from the source code, you must install the updated dependencies via `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Current requirements:*
```text
customtkinter
curl-cffi
Pillow
playwright
cryptography
```

---

## 📦 Assets
* **`ITFormsDownloader.exe`**: Built single-file executable for Windows (64-bit).
* **Source Code (zip)**
* **Source Code (tar.gz)**
