#!/usr/bin/env python3
"""
Income Tax Forms 2026 — Professional Downloader
=================================================
Modern GUI for discovering and downloading all Income Tax forms
from incometaxindia.gov.in.

Backend  : requests (plain HTTP — no browser engine needed)
Frontend : customtkinter (modern themed widgets)
Packaging: PyInstaller-ready (single EXE)

(c) 2026 DAKSM AND CO LLP
"""

__version__ = "1.0.0"
__app_name__ = "Income Tax Form 2026 Navigator"
__author__   = "CA. Deepak Bholusaria"

import csv
import json
import os
import re
import sys
import platform
import subprocess
import threading
import queue
import webbrowser
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import customtkinter as ctk

# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════
BASE_URL      = "https://www.incometaxindia.gov.in"
SEARCH_API    = f"{BASE_URL}/o/search/v1.0/search"
CATEGORY_ID   = "16258183"
BLUEPRINT_ERC = "FORMS_BP_ERC"
API_PAGE_SIZE = 20
MAX_RETRIES   = 3
DL_TIMEOUT    = 30          # seconds
CONCURRENCY   = 6

DEFAULT_PATH  = (
    r"D:\IncomeTaxForms2026"
    if platform.system() == "Windows"
    else str(Path.home() / "IncomeTaxForms2026")
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
    "Gecko/20100101 Firefox/125.0"
)

# Colours (light)
CLR_PRIMARY   = "#1a73e8"
CLR_SUCCESS   = "#0d904f"
CLR_ERROR     = "#d93025"
CLR_MUTED     = "#5f6368"
CLR_BG_CARD   = "#ffffff"
CLR_BG_ALT    = "#f1f3f4"
CLR_HEADER_BG = "#1a237e"
CLR_HEADER_FG = "#ffffff"
CLR_ACCENT    = "#e8f0fe"


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def _extract_field(content_fields: list, name: str):
    for cf in content_fields:
        if cf.get("name") == name:
            return cf.get("contentFieldValue", {})
    return None


def clean_filename(form_no: str, title: str, max_len: int = 60) -> str:
    num = form_no.replace("Form No.", "").replace(":", "").strip()
    num = re.sub(r"[^\w.-]", "_", num).strip("_")
    short = title[:max_len].strip()
    short = re.sub(r"[^\w\s-]", "", short)
    short = re.sub(r"\s+", "_", short).strip("_")
    return f"Form_{num}_{short}.pdf" if short else f"Form_{num}.pdf"


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ══════════════════════════════════════════════════════════════
# BACKEND  (pure requests — no browser engine)
# ══════════════════════════════════════════════════════════════
def create_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US",
    })
    return s


def scan_forms(cb) -> list[dict]:
    """Discover all forms via the Liferay Search API."""
    cb("log", "Connecting to incometaxindia.gov.in …")
    session = create_session()
    forms = []
    page_num = 1

    while True:
        params = {
            "nestedFields": "embedded",
            "page": page_num,
            "pageSize": API_PAGE_SIZE,
            "restrictFields": "embedded.actions,embedded.creator",
        }
        body = {
            "attributes": {
                "search.empty.search": True,
                "search.experiences.blueprint.external.reference.code": BLUEPRINT_ERC,
                "search.experiences.category_id": CATEGORY_ID,
            }
        }
        try:
            resp = session.post(SEARCH_API, params=params, json=body, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            cb("log", f"ERROR on page {page_num}: {exc}")
            break

        items     = data.get("items", [])
        total     = data.get("totalCount", 0)
        last_page = data.get("lastPage", 1)

        if page_num == 1:
            cb("log", f"Server reports {total} form(s) across {last_page} page(s)")

        for item in items:
            title_raw = item.get("title", "")
            emb       = item.get("embedded", {})
            fields    = emb.get("contentFields", [])

            fn  = _extract_field(fields, "formNumber")
            num = fn.get("data", "") if fn else ""

            desc = _extract_field(fields, "formDescription")
            description = desc.get("data", "") if desc else ""

            pdf = _extract_field(fields, "formPDF")
            content_url = ""
            if pdf and "document" in pdf:
                content_url = pdf["document"].get("contentUrl", "")
            detail_url = (
                (BASE_URL + content_url)
                if content_url.startswith("/") else content_url
            )

            forms.append({
                "form_no":    title_raw or f"Form No. : {num}",
                "title":      description,
                "detail_url": detail_url,
            })

        cb("log", f"  Page {page_num}/{last_page} — {len(items)} items")
        cb("progress_pulse", None)

        if page_num >= last_page:
            break
        page_num += 1

    session.close()
    cb("log", f"Scan complete — {len(forms)} form(s) discovered")
    return forms


def download_one_form(form: dict, save_dir: Path, session: requests.Session):
    """Download a single PDF. Returns a result dict."""
    fno  = form["form_no"]
    desc = form["title"]
    url  = form["detail_url"]

    if not url:
        return dict(form_no=fno, title=desc, status="SKIPPED",
                    saved_as="", detail_url="", note="No PDF URL")

    fname = clean_filename(fno, desc)
    fpath = save_dir / fname

    status, note = "FAILED", ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(url, timeout=DL_TIMEOUT)
            if r.status_code == 200 and len(r.content) > 500:
                fpath.write_bytes(r.content)
                status = "OK"
                note = f"{len(r.content):,} bytes"
                break
            note = f"HTTP {r.status_code} (attempt {attempt})"
        except Exception as exc:
            note = f"{exc} (attempt {attempt})"

    return dict(form_no=fno, title=desc, status=status,
                saved_as=fname if status == "OK" else "",
                detail_url=url, note=note)


def download_forms(forms: list[dict], save_dir: str, cb) -> list[dict]:
    """Download PDFs for all supplied forms using a thread pool."""
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    total = len(forms)
    cb("log", f"Downloading {total} form(s) to {save_path} …")

    session = create_session()
    results = []
    completed = 0

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {
            pool.submit(download_one_form, f, save_path, session): f
            for f in forms
        }
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            tag = "OK " if res["status"] == "OK" else "FAIL"
            cb("log", f"  [{completed}/{total}] {tag}  {res['form_no']}")
            cb("progress", (completed, total))

    session.close()

    # Sort results to match input order
    order = {f["form_no"]: i for i, f in enumerate(forms)}
    results.sort(key=lambda r: order.get(r["form_no"], 999))

    # Save download_log.csv
    log_path = save_path / "download_log.csv"
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["form_no", "title", "status",
                           "saved_as", "detail_url", "note"],
        )
        w.writeheader()
        w.writerows(results)

    ok   = sum(1 for r in results if r["status"] == "OK")
    fail = sum(1 for r in results if r["status"] == "FAILED")
    skip = sum(1 for r in results if r["status"] == "SKIPPED")
    cb("log", f"Download complete — OK: {ok} | Failed: {fail} | Skipped: {skip}")
    cb("log", f"Log saved → {log_path}")
    return results


# ══════════════════════════════════════════════════════════════
# GUI — CUSTOM TREEVIEW (checkbox‑enabled)
# ══════════════════════════════════════════════════════════════
import tkinter as tk
from tkinter import ttk


class CheckTreeview(ttk.Treeview):
    """A ttk.Treeview with a togglable ✓ first column."""

    def __init__(self, master, on_toggle=None, **kw):
        super().__init__(master, **kw)
        self._on_toggle = on_toggle
        self.bind("<ButtonRelease-1>", self._click)

        style = ttk.Style()
        style.configure(
            "Check.Treeview",
            rowheight=26,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Check.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#e8eaed",
            foreground="#202124",
        )
        style.map("Check.Treeview", background=[("selected", "#d2e3fc")])
        self.configure(style="Check.Treeview")

        self.tag_configure("checked",     background="#e8f0fe")
        self.tag_configure("unchecked",   background="#ffffff")
        self.tag_configure("alt",         background="#f1f3f4")
        self.tag_configure("checked_alt", background="#d2e3fc")

    def _click(self, event):
        iid = self.identify_row(event.y)
        if iid and self._on_toggle:
            self._on_toggle(iid)


# ══════════════════════════════════════════════════════════════
# GUI — MAIN APPLICATION
# ══════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{__app_name__} — by {__author__}")
        self.geometry("1180x820")
        self.minsize(960, 680)

        # ── State ─────────────────────────────────────────
        self.forms: list[dict]   = []
        self.selected: set[int]  = set()
        self.visible_map: dict   = {}    # tree iid → forms index
        self.is_busy             = False
        self.msg_queue           = queue.Queue()

        # ── Build (status bar FIRST so it claims bottom space) ──
        self._build_status_bar()
        self._build_header()
        self._build_config_panel()
        self._build_toolbar()
        self._build_filter_bar()
        self._build_tree()
        self._build_action_bar()
        self._build_progress()
        self._build_log()

        self._poll_queue()

    # ──────────────────────────────────────────────────────
    # HEADER
    # ──────────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=CLR_HEADER_BG, corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="  \U0001F3DB  Income Tax Form 2026 Navigator",
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=CLR_HEADER_FG,
        ).pack(side="left", padx=16)

        ctk.CTkLabel(
            hdr, text="by CA. Deepak Bholusaria ",
            font=ctk.CTkFont("Segoe UI", 11, slant="italic"),
            text_color="#90caf9",
        ).pack(side="left", padx=(4, 0))

        ctk.CTkLabel(
            hdr, text=f"v{__version__}",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color="#90caf9",
        ).pack(side="left", padx=(0, 20))

        # Appearance toggle
        self.appearance_var = ctk.StringVar(value="System")
        ctk.CTkSegmentedButton(
            hdr, values=["Light", "Dark", "System"],
            variable=self.appearance_var,
            command=self._change_appearance,
            font=ctk.CTkFont(size=11),
            width=180,
        ).pack(side="right", padx=16, pady=12)

    def _change_appearance(self, mode):
        ctk.set_appearance_mode(mode)

    # ──────────────────────────────────────────────────────
    # CONFIGURATION PANEL
    # ──────────────────────────────────────────────────────
    def _build_config_panel(self):
        frame = ctk.CTkFrame(self, corner_radius=8)
        frame.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            frame, text="Save Location",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(8, 2))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 8))

        self.path_var = ctk.StringVar(value=DEFAULT_PATH)
        ctk.CTkEntry(
            row, textvariable=self.path_var,
            font=ctk.CTkFont(size=12),
            height=34,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            row, text="Browse", width=90, height=34,
            command=self._browse_path,
            fg_color="#5f6368", hover_color="#3c4043",
        ).pack(side="left")

    # ──────────────────────────────────────────────────────
    # TOOLBAR  (Scan / Rescan)
    # ──────────────────────────────────────────────────────
    def _build_toolbar(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=4)

        self.btn_scan = ctk.CTkButton(
            frame, text="\U0001F50D  Scan Forms", width=150, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=CLR_PRIMARY, hover_color="#1565c0",
            command=self._on_scan,
        )
        self.btn_scan.pack(side="left")

        self.btn_rescan = ctk.CTkButton(
            frame, text="\U0001F504  Rescan", width=110, height=36,
            font=ctk.CTkFont(size=12),
            fg_color="#5f6368", hover_color="#3c4043",
            command=self._on_scan, state="disabled",
        )
        self.btn_rescan.pack(side="left", padx=(8, 0))

        self.lbl_found = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CLR_MUTED,
        )
        self.lbl_found.pack(side="right", padx=8)

    # ──────────────────────────────────────────────────────
    # FILTER BAR
    # ──────────────────────────────────────────────────────
    def _build_filter_bar(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=2)

        ctk.CTkLabel(frame, text="Filter:", font=ctk.CTkFont(size=12)).pack(
            side="left"
        )

        self.filter_var = ctk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(
            frame, textvariable=self.filter_var,
            width=220, height=30, placeholder_text="Type to search …",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(6, 16))

        self.btn_sel_all = ctk.CTkButton(
            frame, text="✓  Select All", width=110, height=30,
            font=ctk.CTkFont(size=11),
            fg_color=CLR_SUCCESS, hover_color="#0b7a43",
            command=self._select_all, state="disabled",
        )
        self.btn_sel_all.pack(side="left", padx=(0, 6))

        self.btn_desel = ctk.CTkButton(
            frame, text="✗  Deselect All", width=120, height=30,
            font=ctk.CTkFont(size=11),
            fg_color="#d93025", hover_color="#b71c1c",
            text_color="#ffffff",
            command=self._deselect_all, state="disabled",
        )
        self.btn_desel.pack(side="left")

        self.lbl_sel = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=12),
            text_color=CLR_MUTED,
        )
        self.lbl_sel.pack(side="right", padx=8)

    # ──────────────────────────────────────────────────────
    # TREEVIEW
    # ──────────────────────────────────────────────────────
    def _build_tree(self):
        container = ctk.CTkFrame(self, corner_radius=8)
        container.pack(fill="both", expand=True, padx=12, pady=4)

        columns = ("sel", "form_no", "title")
        self.tree = CheckTreeview(
            container, columns=columns, show="headings",
            selectmode="none", height=14,
            on_toggle=self._on_tree_toggle,
        )
        self.tree.heading("sel",     text=" Sel", anchor="center")
        self.tree.heading("form_no", text=" Form No.", anchor="w")
        self.tree.heading("title",   text=" Title / Description", anchor="w")

        self.tree.column("sel",     width=50,  minwidth=50,  stretch=False, anchor="center")
        self.tree.column("form_no", width=130, minwidth=100, stretch=False, anchor="w")
        self.tree.column("title",   width=800, minwidth=200, stretch=True,  anchor="w")

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        vsb.pack(side="right", fill="y", pady=6, padx=(0, 6))

    # ──────────────────────────────────────────────────────
    # ACTION BAR  (Download / Export / Open Folder)
    # ──────────────────────────────────────────────────────
    def _build_action_bar(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=4)

        self.btn_download = ctk.CTkButton(
            frame, text="\u2B07  Download Selected", width=180, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=CLR_SUCCESS, hover_color="#0b7a43",
            command=self._on_download, state="disabled",
        )
        self.btn_download.pack(side="left")

        self.btn_export = ctk.CTkButton(
            frame, text="\U0001F4CA  Export CSV", width=130, height=36,
            font=ctk.CTkFont(size=12),
            fg_color="#fb8c00", hover_color="#ef6c00",
            command=self._on_export, state="disabled",
        )
        self.btn_export.pack(side="left", padx=(8, 0))

        self.btn_open = ctk.CTkButton(
            frame, text="\U0001F4C2  Open Folder", width=130, height=36,
            font=ctk.CTkFont(size=12),
            fg_color="#5f6368", hover_color="#3c4043",
            command=self._on_open_folder,
        )
        self.btn_open.pack(side="left", padx=(8, 0))

    # ──────────────────────────────────────────────────────
    # PROGRESS BAR
    # ──────────────────────────────────────────────────────
    def _build_progress(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=2)

        self.progress_bar = ctk.CTkProgressBar(
            frame, height=24, corner_radius=8,
            progress_color=CLR_PRIMARY,
            border_width=1,
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.progress_bar.set(0)

        self.lbl_progress = ctk.CTkLabel(
            frame, text="", width=140,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CLR_MUTED,
        )
        self.lbl_progress.pack(side="left")

    # ──────────────────────────────────────────────────────
    # ACTIVITY LOG
    # ──────────────────────────────────────────────────────
    def _build_log(self):
        lbl = ctk.CTkLabel(
            self, text="Activity Log",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        lbl.pack(fill="x", padx=16, pady=(6, 0))

        self.log_box = ctk.CTkTextbox(
            self, height=150,
            font=ctk.CTkFont("Consolas" if platform.system() == "Windows" else "monospace", 11),
            corner_radius=8,
            state="disabled",
            wrap="word",
        )
        self.log_box.pack(fill="x", padx=12, pady=(2, 4))

        # Log text tags
        self.log_box._textbox.tag_configure("ok",   foreground=CLR_SUCCESS)
        self.log_box._textbox.tag_configure("fail", foreground=CLR_ERROR)
        self.log_box._textbox.tag_configure("info", foreground=CLR_PRIMARY)
        self.log_box._textbox.tag_configure("ts",   foreground=CLR_MUTED)

    # ──────────────────────────────────────────────────────
    # STATUS BAR
    # ──────────────────────────────────────────────────────
    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color="#e8eaed")
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            bar, text="  Ready",
            font=ctk.CTkFont(size=11),
            text_color=CLR_MUTED, anchor="w",
        )
        self.lbl_status.pack(side="left", padx=8)

        ctk.CTkLabel(
            bar, text="© 2026 CA. Deepak Bholusaria | AI Learrning Guru",
            font=ctk.CTkFont(size=10),
            text_color="#9e9e9e", anchor="e",
        ).pack(side="right", padx=8)

    # ══════════════════════════════════════════════════════
    # MESSAGE QUEUE  (thread‑safe GUI updates)
    # ══════════════════════════════════════════════════════
    def _enqueue(self, msg_type: str, data=None):
        self.msg_queue.put((msg_type, data))

    def _poll_queue(self):
        try:
            while True:
                mtype, data = self.msg_queue.get_nowait()
                if mtype == "log":
                    self._log(data)
                elif mtype == "progress":
                    done, total = data
                    pct = done / total if total else 0
                    self.progress_bar.set(pct)
                    self.lbl_progress.configure(
                        text=f"{done} / {total}  ({pct*100:.0f}%)"
                    )
                elif mtype == "progress_pulse":
                    pass  # could animate indeterminate
                elif mtype == "scan_done":
                    self._on_scan_done(data)
                elif mtype == "download_done":
                    self._on_download_done(data)
                elif mtype == "error":
                    self._log(f"ERROR: {data}")
                    self._set_busy(False)
        except queue.Empty:
            pass
        self.after(80, self._poll_queue)

    # ══════════════════════════════════════════════════════
    # LOGGING
    # ══════════════════════════════════════════════════════
    def _log(self, msg: str):
        self.log_box.configure(state="normal")
        tb = self.log_box._textbox

        tb.insert("end", f"[{ts()}] ", "ts")

        tag = "info"
        if " OK " in msg:
            tag = "ok"
        elif "FAIL" in msg or "ERROR" in msg or "error" in msg.lower():
            tag = "fail"

        tb.insert("end", msg + "\n", tag)
        tb.see("end")
        self.log_box.configure(state="disabled")

    # ══════════════════════════════════════════════════════
    # BUSY STATE
    # ══════════════════════════════════════════════════════
    def _set_busy(self, busy: bool):
        self.is_busy = busy
        s = "disabled" if busy else "normal"
        self.btn_scan.configure(state=s)
        self.btn_rescan.configure(state=s if self.forms else "disabled")
        self.btn_download.configure(state=s if self.selected else "disabled")
        self.btn_export.configure(state=s if self.forms else "disabled")
        self.btn_sel_all.configure(state=s if self.forms else "disabled")
        self.btn_desel.configure(state=s if self.forms else "disabled")
        self.lbl_status.configure(
            text="  ⏳ Working …" if busy else "  Ready"
        )

    # ══════════════════════════════════════════════════════
    # PATH BROWSER
    # ══════════════════════════════════════════════════════
    def _browse_path(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(
            initialdir=self.path_var.get(), title="Choose save folder"
        )
        if d:
            self.path_var.set(d)

    # ══════════════════════════════════════════════════════
    # SCAN
    # ══════════════════════════════════════════════════════
    def _on_scan(self):
        self._set_busy(True)
        self.progress_bar.set(0)
        self.lbl_progress.configure(text="")
        self._log("Starting scan …")

        def worker():
            try:
                forms = scan_forms(self._enqueue)
                self._enqueue("scan_done", forms)
            except Exception as exc:
                self._enqueue("error", str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_done(self, forms):
        self.forms = forms
        self.selected = set(range(len(forms)))
        self._populate_tree()
        self.lbl_found.configure(text=f"{len(forms)} form(s) found")
        self._set_busy(False)
        self.btn_rescan.configure(state="normal")

    # ══════════════════════════════════════════════════════
    # TREEVIEW POPULATION
    # ══════════════════════════════════════════════════════
    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.visible_map.clear()
        filt = self.filter_var.get().lower().strip()

        row_idx = 0
        for i, form in enumerate(self.forms):
            text = f"{form['form_no']} {form['title']}".lower()
            if filt and filt not in text:
                continue

            is_sel = i in self.selected
            is_alt = row_idx % 2 == 1
            if is_sel:
                tag = "checked_alt" if is_alt else "checked"
            else:
                tag = "alt" if is_alt else "unchecked"
            iid = self.tree.insert(
                "", "end",
                values=("✓" if is_sel else "", form["form_no"], form["title"]),
                tags=(tag,),
            )
            self.visible_map[iid] = i
            row_idx += 1

        self._update_selection_label()

    def _apply_filter(self):
        if self.forms:
            self._populate_tree()

    # ══════════════════════════════════════════════════════
    # TOGGLE / SELECT / DESELECT
    # ══════════════════════════════════════════════════════
    def _on_tree_toggle(self, iid):
        idx = self.visible_map.get(iid)
        if idx is None:
            return
        if idx in self.selected:
            self.selected.discard(idx)
            self.tree.set(iid, "sel", "")
            self.tree.item(iid, tags=("unchecked",))
        else:
            self.selected.add(idx)
            self.tree.set(iid, "sel", "✓")
            self.tree.item(iid, tags=("checked",))
        self._update_selection_label()

    def _select_all(self):
        self.selected = set(range(len(self.forms)))
        self._populate_tree()

    def _deselect_all(self):
        self.selected.clear()
        self._populate_tree()

    def _update_selection_label(self):
        sel = len(self.selected)
        tot = len(self.forms)
        self.lbl_sel.configure(text=f"{sel} of {tot} selected")
        self.btn_download.configure(
            state="normal" if sel and not self.is_busy else "disabled"
        )

    # ══════════════════════════════════════════════════════
    # DOWNLOAD
    # ══════════════════════════════════════════════════════
    def _on_download(self):
        if not self.selected:
            return
        self._set_busy(True)
        self.progress_bar.set(0)
        self.lbl_progress.configure(text="")

        sel_forms = [self.forms[i] for i in sorted(self.selected)]
        save_dir  = self.path_var.get()

        def worker():
            try:
                results = download_forms(sel_forms, save_dir, self._enqueue)
                self._enqueue("download_done", results)
            except Exception as exc:
                self._enqueue("error", str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_download_done(self, results):
        self._set_busy(False)
        ok = sum(1 for r in results if r["status"] == "OK")
        self.lbl_status.configure(text=f"  ✅  {ok} PDF(s) downloaded successfully")

    # ══════════════════════════════════════════════════════
    # EXPORT CSV
    # ══════════════════════════════════════════════════════
    def _on_export(self):
        if not self.forms:
            return
        from tkinter import filedialog
        save_dir = self.path_var.get()
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        chosen = filedialog.asksaveasfilename(
            initialdir=save_dir,
            initialfile="discovered_forms.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export forms list",
        )
        if not chosen:
            return

        with open(chosen, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["form_no", "title", "detail_url"])
            w.writeheader()
            w.writerows(self.forms)

        self._log(f"Exported {len(self.forms)} form(s) → {chosen}")

    # ══════════════════════════════════════════════════════
    # OPEN FOLDER
    # ══════════════════════════════════════════════════════
    def _on_open_folder(self):
        folder = self.path_var.get()
        Path(folder).mkdir(parents=True, exist_ok=True)
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as exc:
            self._log(f"Could not open folder: {exc}")


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════
def main():
    # DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
