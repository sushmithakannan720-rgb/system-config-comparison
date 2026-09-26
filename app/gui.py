"""gui.py — CustomTkinter user interface.

Layout:
    ┌─────────┬────────────────────────────────────────────┐
    │ sidebar │  page area (one of):                       │
    │  Dashboard    System Details    Compare    About      │
    └─────────┴────────────────────────────────────────────┘

The GUI only *shows* things; all logic lives in the sibling modules
(system_info, comparison, storage, report), which keeps the code easy
to test and explain.
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter.filedialog as filedialog
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from . import comparison, report, storage, system_info
from .utils import (APP_TITLE, APP_VERSION, PROJECT_ROOT, REPORTS_DIR, bar,
                    bytes_to_str, ensure_dir, format_field, get_logger,
                    get_path)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

FONT = ("Segoe UI",)


# ================================================================== app class

class SystemConfigApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1150x720")
        self.minsize(980, 620)

        # state
        self.last_scan = None            # most recent scan of this machine
        self.config_a = None             # loaded/captured configuration A
        self.config_b = None             # loaded/captured configuration B
        self.rows = None                 # comparison result rows
        self.summary = None              # comparison summary
        self._scanning = False           # True while a background scan runs
        self._scan_queue = queue.Queue()  # worker thread -> UI thread handoff
        self._pending_on_done = None
        self._nav_buttons = {}

        self.logger = get_logger()

        # layout: sidebar + page area
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_pages()
        self.show_page("dashboard")

    # ================================================================ sidebar

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, corner_radius=0, width=210)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        title = ctk.CTkLabel(
            sidebar, text="⚙ Config\nComparator",
            font=(FONT, 19, "bold"), justify="center",
        )
        title.pack(pady=(24, 4))
        ctk.CTkLabel(sidebar, text=APP_TITLE, font=(FONT, 10),
                     text_color="gray").pack(pady=(0, 20))

        nav_items = [
            ("dashboard", "🏠  Dashboard"),
            ("details", "🖥  System Details"),
            ("compare", "📊  Compare Systems"),
            ("about", "ℹ  About Project"),
        ]
        for key, text in nav_items:
            btn = ctk.CTkButton(
                sidebar, text=text, anchor="w", height=40,
                font=(FONT, 13), corner_radius=10,
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=14, pady=5)
            self._nav_buttons[key] = btn

        # light / dark / system appearance toggle
        self.appearance_mode = "System"
        self._appearance_btn = ctk.CTkButton(
            sidebar, text="☀  Light mode", height=34,
            font=(FONT, 11), corner_radius=10, command=self._toggle_appearance,
        )
        self._appearance_btn.pack(padx=14, pady=(24, 12))

        ctk.CTkLabel(sidebar, text=f"v{APP_VERSION} • works offline",
                     font=(FONT, 10), text_color="gray").pack(pady=(0, 10))

    def _toggle_appearance(self):
        cycle = ["System", "Light", "Dark"]
        self.appearance_mode = cycle[(cycle.index(self.appearance_mode) + 1) % 3]
        ctk.set_appearance_mode(self.appearance_mode)
        icon = {"System": "⚙", "Light": "☀", "Dark": "🌙"}[self.appearance_mode]
        self._appearance_btn.configure(text=f"{icon}  {self.appearance_mode} mode")

    # ================================================================= pages

    def _build_pages(self):
        area = ctk.CTkFrame(self, fg_color="transparent")
        area.grid(row=0, column=1, sticky="nsew")
        area.grid_rowconfigure(0, weight=1)
        area.grid_columnconfigure(0, weight=1)

        self.pages = {}
        builders = {
            "dashboard": self._page_dashboard,
            "details": self._page_details,
            "compare": self._page_compare,
            "about": self._page_about,
        }
        for key, builder in builders.items():
            frame = ctk.CTkFrame(area, fg_color="transparent")
            frame.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = frame
            builder(frame)

    def show_page(self, name):
        self.pages[name].tkraise()
        for key, btn in self._nav_buttons.items():
            if key == name:
                btn.configure(fg_color=("gray75", "gray25"), text_color="black"
                              if self.appearance_mode == "Light" else "white")
            else:
                btn.configure(fg_color="transparent")

    def _card(self, parent, title):
        """A titled card container. Returns the inner content frame."""
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.pack(fill="x", padx=20, pady=10)
        if title:
            ctk.CTkLabel(card, text=title, font=(FONT, 14, "bold"),
                         anchor="w").pack(fill="x", padx=16, pady=(12, 0))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=10)
        return inner

    # ------------------------------------------------------------ dashboard

    def _page_dashboard(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(scroll, text="System Configuration Comparison Tool",
                     font=(FONT, 24, "bold")).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(
            scroll,
            text="Scan this computer, save its configuration as a JSON file, "
                 "then compare it with another system and see every difference "
                 "clearly explained.",
            font=(FONT, 12), text_color="gray", justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        inner = self._card(scroll, "Quick Actions")
        inner.grid_columnconfigure((0, 1), weight=1, uniform="btns")
        buttons = [
            ("🔍  Scan Current System", self.scan_system, 0, 0),
            ("📋  View System Details", self.view_details, 0, 1),
            ("⚖  Compare Systems", lambda: self.show_page("compare"), 1, 0),
            ("📄  Generate Report", self.generate_report_from_dashboard, 1, 1),
            ("ℹ  About Project", lambda: self.show_page("about"), 2, 0),
        ]
        for text, command, r, c in buttons:
            ctk.CTkButton(inner, text=text, height=44, font=(FONT, 13),
                          command=command).grid(row=r, column=c, padx=6, pady=6,
                                                sticky="ew")

        # last scan summary card
        self.dashboard_card = self._card(scroll, "Last Scan")
        self.dashboard_summary_label = ctk.CTkLabel(
            self.dashboard_card,
            text="No scan yet. Click “Scan Current System” to collect the "
                 "configuration of this computer.",
            font=(FONT, 12), justify="left", anchor="w",
        )
        self.dashboard_summary_label.pack(fill="x")

        ctk.CTkLabel(
            scroll,
            text="🔒  Privacy: all scans, files and reports stay on this computer. "
                 "The app does not use the internet.",
            font=(FONT, 11), text_color="gray",
        ).pack(anchor="w", padx=20, pady=(4, 16))

    # ----------------------------------------------------------- details page

    def _page_details(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(scroll, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(14, 0))
        ctk.CTkLabel(head, text="System Details", font=(FONT, 20, "bold")
                     ).pack(side="left")
        ctk.CTkButton(head, text="🔄  Re-scan", height=32,
                      font=(FONT, 11), command=self.scan_system
                      ).pack(side="right")

        self.details_labels = {}   # (section, key) -> CTkLabel
        self.details_bars = {}     # "memory"/"storage" -> (bar, percent label)
        self._build_details_sections(scroll)
        self.details_placeholder = ctk.CTkLabel(
            scroll, text="Scan the system to see its details here.",
            font=(FONT, 12), text_color="gray",
        )
        self.details_placeholder.pack(pady=8)

    def _build_details_sections(self, scroll):
        sections = [
            ("SYSTEM", [
                ("operating_system", "Operating System"),
                ("version", "Version"),
                ("build", "Build"),
                ("architecture", "Architecture"),
                ("machine", "Machine Type"),
                ("hostname", "Hostname"),
            ], "system"),
            ("CPU", [
                ("name", "Processor"),
                ("cores", "Physical Cores"),
                ("logical_processors", "Logical Processors"),
                ("usage_percent", "CPU Usage"),
            ], "cpu"),
            ("MEMORY", [
                ("total", "Total RAM"),
                ("used", "Used RAM"),
                ("available", "Available RAM"),
                ("usage_percent", "RAM Usage"),
            ], "memory"),
            ("STORAGE", [
                ("total", "Total Storage"),
                ("used", "Used Storage"),
                ("free", "Free Storage"),
                ("usage_percent", "Storage Usage"),
            ], "storage"),
            ("NETWORK", [
                ("hostname", "Hostname"),
                ("ip_address", "IP Address"),
            ], "network"),
        ]
        for title, fields, section in sections:
            inner = self._card(scroll, title)
            for key, label in fields:
                row = ctk.CTkFrame(inner, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=label, font=(FONT, 12), width=170,
                             anchor="w").pack(side="left")
                value = ctk.CTkLabel(row, text="Not available",
                                     font=(FONT, 12), anchor="w")
                value.pack(side="left", fill="x", expand=True)
                self.details_labels[(section, key)] = value

            if section in ("memory", "storage"):
                bar_frame = ctk.CTkFrame(inner, fg_color="transparent")
                bar_frame.pack(fill="x", pady=(6, 2))
                pbar = ctk.CTkProgressBar(bar_frame, height=10)
                pbar.pack(side="left", fill="x", expand=True, padx=(0, 8))
                pbar.set(0)
                plabel = ctk.CTkLabel(bar_frame, text="0.0%", font=(FONT, 11),
                                      width=52)
                plabel.pack(side="right")
                self.details_bars[section] = (pbar, plabel)

    def _refresh_details(self, config):
        if config is None:
            self.details_placeholder.pack(pady=8)
            return
        self.details_placeholder.pack_forget()
        for (section, key), label in self.details_labels.items():
            label.configure(text=format_field(config, section, key))
        for section, (pbar, plabel) in self.details_bars.items():
            try:
                pct = float(get_path(config, (section, "usage_percent")) or 0)
            except (TypeError, ValueError):
                pct = 0.0
            pbar.set(max(0.0, min(1.0, pct / 100.0)))
            plabel.configure(text=f"{pct:.1f}%")

    # ------------------------------------------------------------- compare page

    def _page_compare(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(scroll, text="Compare Systems", font=(FONT, 20, "bold")
                     ).pack(anchor="w", padx=20, pady=(14, 4))

        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x", padx=20)
        top.grid_columnconfigure((0, 2), weight=1, uniform="slots")
        top.grid_columnconfigure(1, weight=0)

        self.slot_card_a = self._build_slot(top, "A", 0)
        vs = ctk.CTkLabel(top, text="vs", font=(FONT, 16, "bold"),
                          text_color="gray")
        vs.grid(row=0, column=1, padx=10, pady=10)
        self.slot_card_b = self._build_slot(top, "B", 2)

        actions = ctk.CTkFrame(scroll, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=8)
        ctk.CTkButton(actions, text="⚖  Compare Systems", height=42,
                      font=(FONT, 13, "bold"), command=self.compare
                      ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(actions, text="📄  Generate Report", height=42,
                      font=(FONT, 12), command=self.generate_report
                      ).pack(side="left")
        self.compare_status = ctk.CTkLabel(actions, text="", font=(FONT, 12),
                                           text_color="gray")
        self.compare_status.pack(side="right", padx=8)

        # results container (rebuilt after every comparison)
        self.results_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.results_frame.pack(fill="x", padx=12, pady=(4, 20))
        self._render_results_placeholder()

    def _build_slot(self, parent, letter, column):
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if letter == "A" else 0, 10))
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(head, text=f"System {letter}", font=(FONT, 14, "bold")
                     ).pack(side="left")

        info_name = f"slot_label_{letter}"
        setattr(self, info_name, ctk.CTkLabel(
            card, text=f"System {letter} — not loaded", font=(FONT, 11),
            text_color="gray", wraplength=300, justify="left", anchor="w",
        ))
        getattr(self, info_name).pack(fill="x", padx=14, pady=(4, 6))

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkButton(btns, text=f"📂 Load System {letter}", height=32,
                      font=(FONT, 11),
                      command=lambda l=letter: self.load_config(l)
                      ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="🔍 Scan", height=32, font=(FONT, 11),
                      command=lambda l=letter: self.scan_into(l)
                      ).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Last scan", height=32, font=(FONT, 11),
                      command=lambda l=letter: self.use_last_scan(l)
                      ).pack(side="left", padx=5)
        return card

    def refresh_slot_labels(self):
        for letter, cfg in (("A", self.config_a), ("B", self.config_b)):
            label = getattr(self, f"slot_label_{letter}")
            if cfg is None:
                label.configure(text=f"System {letter} — not loaded",
                                text_color="gray")
                continue
            name = storage.config_name(cfg)
            os_name = format_field(cfg, "system", "operating_system")
            version = format_field(cfg, "system", "version")
            ram = format_field(cfg, "memory", "total")
            label.configure(
                text=f"{name}  •  {os_name} {version}  •  RAM {ram}  •  "
                     f"Storage {format_field(cfg, 'storage', 'total')}",
                text_color=("gray15", "gray85"),
            )

    # ------------------------------------------------------------- actions

    def scan_system(self, on_done=None):
        """Scan this computer on a BACKGROUND THREAD and remember the result.

        Scanning can take a couple of seconds (CPU usage is measured over
        0.5 s and the CPU name is queried from the OS). Running it off the
        UI thread keeps the interface fully responsive while it works.
        `on_done(config)` is called on the UI thread once the scan finishes.

        Threading model: the worker thread only puts its result into a
        thread-safe queue (it never touches Tcl/Tk). The UI thread polls
        that queue every 100 ms and applies the result — this is the safe
        cross-thread pattern for tkinter on every platform.
        """
        if self._scanning:
            return  # a scan is already in progress
        self._scanning = True
        self._pending_on_done = on_done
        self.logger.info("System scan started")
        self.dashboard_summary_label.configure(
            text="Scanning… this takes a second or two. The window stays "
                 "responsive.")
        self.update_idletasks()

        def worker():
            try:
                config = system_info.get_system_config()
                error = None
            except Exception as exc:  # noqa: BLE001 - reported on UI thread
                config, error = None, exc
            self._scan_queue.put((config, error))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self._poll_scan)  # schedule the poller on the UI thread

    def _poll_scan(self):
        """UI-thread side of the scan: check the queue, repeat until done."""
        if not self._scanning:
            return
        try:
            config, error = self._scan_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_scan)
            return
        on_done = self._pending_on_done
        self._pending_on_done = None
        self._scan_done(config, error, on_done)

    def _scan_done(self, config, error, on_done):
        self._scanning = False
        if error is not None:
            self.logger.error("System scan failed: %s", error)
            messagebox.showerror(APP_TITLE, f"Scan failed:\n{error}")
            self.dashboard_summary_label.configure(
                text="Scan failed. Details are in logs/app.log.")
            return

        self.last_scan = config
        host = get_path(config, ("system", "hostname")) or "unknown"
        os_name = format_field(config, "system", "operating_system")
        self.logger.info("System scan complete (%s)", host)
        self.dashboard_summary_label.configure(
            text=(f"Last scan: {host}  •  {os_name} "
                  f"{format_field(config, 'system', 'version')}\n"
                  f"CPU usage {format_field(config, 'cpu', 'usage_percent')}"
                  f"   RAM used {format_field(config, 'memory', 'usage_percent')}"
                  f"   Storage used {format_field(config, 'storage', 'usage_percent')}\n"
                  f"Captured at {get_path(config, ('meta', 'captured_at')) or '?'}"),
        )
        self._refresh_details(config)
        if on_done is not None:
            on_done(config)

    def view_details(self):
        if self.last_scan is None:
            self.scan_system(on_done=lambda _cfg: self.show_page("details"))
        else:
            self.show_page("details")

    def scan_into(self, letter):
        self.scan_system(on_done=lambda cfg: self._assign(letter, cfg))

    def use_last_scan(self, letter):
        if self.last_scan is None:
            messagebox.showinfo(APP_TITLE, "No scan yet — click “Scan Current System” first.")
            return
        self._assign(letter, self.last_scan)

    def load_config(self, letter):
        path = filedialog.askopenfilename(
            title=f"Load configuration for System {letter}",
            initialdir=PROJECT_ROOT,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            config = storage.load_config(path)
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))
            return
        self._assign(letter, config)

    def _assign(self, letter, config):
        setattr(self, f"config_{letter.lower()}", config)
        self.refresh_slot_labels()

    # ------------------------------------------------------------ comparison

    def compare(self):
        if self.config_a is None or self.config_b is None:
            messagebox.showinfo(
                APP_TITLE,
                "System A and System B are both required.\n\n"
                "Use “Load (JSON)”, “Scan as A/B” or “Use last scan” for each slot.",
            )
            return
        self.rows = comparison.compare_configs(self.config_a, self.config_b)
        self.summary = comparison.summarize(self.rows)
        self.logger.info(
            "Comparison done: %d different, %d same, %d not available",
            self.summary["different"], self.summary["same"],
            self.summary["missing"],
        )
        self.compare_status.configure(
            text=f"{self.summary['different']} different • "
                 f"{self.summary['same']} same • {self.summary['missing']} not available"
        )
        self._render_results()

    def _render_results_placeholder(self):
        for child in self.results_frame.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self.results_frame,
            text="Comparison results will appear here.",
            font=(FONT, 12), text_color="gray",
        ).pack(pady=24)

    def _render_results(self):
        for child in self.results_frame.winfo_children():
            child.destroy()

        # ---- comparison table (custom frame table, theme-aware)
        table_card = self._card(self.results_frame, "Comparison Table")
        header = ctk.CTkFrame(table_card, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))
        for col, width in (("Parameter", 190), ("System A", 260),
                           ("System B", 260), ("Status", 110)):
            ctk.CTkLabel(header, text=col, font=(FONT, 11, "bold"), width=width,
                         anchor="w").pack(side="left")

        status_colors = {
            "SAME": ("#d4edda", "#155724"),
            "DIFFERENT": ("#fff3cd", "#856404"),
            "MISSING": ("#f8d7da", "#721c24"),
        }
        for row in self.rows:
            r = ctk.CTkFrame(table_card, fg_color="transparent")
            r.pack(fill="x")
            ctk.CTkLabel(r, text=row["name"], font=(FONT, 11), width=190,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=row["value_a"], font=(FONT, 11), width=260,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=row["value_b"], font=(FONT, 11), width=260,
                         anchor="w").pack(side="left")
            bg, fg = status_colors.get(row["status"], ("#f1f3f5", "#6c757d"))
            ctk.CTkLabel(r, text=row["status"], font=(FONT, 10, "bold"),
                         fg_color=bg, text_color=fg, width=110,
                         corner_radius=6).pack(side="left")

        # ---- difference analysis
        diff_card = self._card(self.results_frame, "Difference Analysis")
        diffs = [row for row in self.rows if row["status"] != "SAME"]
        if diffs:
            text = "\n".join(f"• {row['name']}: {row['note']}" for row in diffs)
        else:
            text = "No differences detected — the two systems are identical " \
                   "for all compared parameters."
        ctk.CTkLabel(diff_card, text=text, font=(FONT, 12), justify="left",
                     anchor="w").pack(fill="x")

        # ---- summary
        sum_card = self._card(self.results_frame, "Comparison Summary")
        ctk.CTkLabel(sum_card, text="\n".join(self.summary["lines"]),
                     font=("Consolas", 12), justify="left",
                     anchor="w").pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(sum_card,
                     text=f"\nTotal differences: {self.summary['total_differences']}",
                     font=(FONT, 13, "bold"), anchor="e").pack(
            side="left", fill="y", padx=(12, 0))

        # ---- simple visualization
        viz_card = self._card(self.results_frame, "Visualization (RAM & Storage)")
        ram_a = get_path(self.config_a, ("memory", "total")) or 0
        ram_b = get_path(self.config_b, ("memory", "total")) or 0
        st_a = get_path(self.config_a, ("storage", "total")) or 0
        st_b = get_path(self.config_b, ("storage", "total")) or 0
        viz_lines = ["RAM:"]
        viz_lines.append(f"  System A {bar(ram_a, max(ram_a, ram_b))} "
                         f"{bytes_to_str(ram_a)}")
        viz_lines.append(f"  System B {bar(ram_b, max(ram_a, ram_b))} "
                         f"{bytes_to_str(ram_b)}")
        viz_lines.append("")
        viz_lines.append("Storage:")
        viz_lines.append(f"  System A {bar(st_a, max(st_a, st_b))} "
                         f"{bytes_to_str(st_a)}")
        viz_lines.append(f"  System B {bar(st_b, max(st_a, st_b))} "
                         f"{bytes_to_str(st_b)}")
        ctk.CTkLabel(viz_card, text="\n".join(viz_lines), font=("Consolas", 12),
                     justify="left", anchor="w").pack(fill="x")

    # --------------------------------------------------------------- report

    def generate_report(self):
        if self.rows is None:
            if self.config_a is not None and self.config_b is not None:
                self.compare()
            if self.rows is None:
                messagebox.showinfo(APP_TITLE, "Load both systems and compare first.")
                return
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            title="Save comparison report",
            initialdir=REPORTS_DIR,
            initialfile=f"system_comparison_{stamp}.html",
            defaultextension=".html",
            filetypes=[("HTML report", "*.html"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            written = report.generate_html_report(
                self.config_a, self.config_b, self.rows, self.summary, path)
        except OSError as exc:
            self.logger.error("Report save failed: %s", exc)
            messagebox.showerror(APP_TITLE, f"Could not save report:\n{exc}")
            return
        self.logger.info("Report saved to %s", written)
        messagebox.showinfo(APP_TITLE, f"Report saved to:\n{written}")
        report.open_report(written)

    def generate_report_from_dashboard(self):
        if self.rows is None and (self.config_a is None or self.config_b is None):
            messagebox.showinfo(
                APP_TITLE,
                "Generate Report works after a comparison.\n"
                "Go to “Compare Systems”, load both systems, then compare.",
            )
            return
        self.show_page("compare")
        self.generate_report()

    # ----------------------------------------------------------------- about

    def _page_about(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(scroll, text="About This Project", font=(FONT, 20, "bold")
                     ).pack(anchor="w", padx=20, pady=(14, 6))

        about = self._card(scroll, None)
        lines = [
            ("Project:", APP_TITLE),
            ("Version:", APP_VERSION),
            ("Purpose:", "To retrieve and compare system configuration "
                         "information through a Python-based GUI application."),
            ("Technology:", "Python 3, CustomTkinter (Tkinter), psutil, "
                            "platform, json, socket"),
            ("Project Type:", "Academic project developed for LPU EDU-Revolution, "
                              "based on the project example provided on the LPU portal."),
        ]
        for label, text in lines:
            row = ctk.CTkFrame(about, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=(FONT, 12, "bold"), width=120,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=text, font=(FONT, 12), anchor="w",
                         wraplength=700, justify="left").pack(side="left",
                                                              fill="x", expand=True)

        privacy = self._card(scroll, "Privacy & Security")
        ctk.CTkLabel(
            privacy,
            text="• The app only reads information about the computer it runs on.\n"
                 "• Configuration files and reports are saved locally (JSON / HTML).\n"
                 "• No personal data is collected, no account is required, and no "
                 "information is ever sent to any external server.\n"
                 "• After installing its Python packages, the app works fully offline.",
            font=(FONT, 12), justify="left", anchor="w",
        ).pack(fill="x")

        note = self._card(scroll, "Note")
        ctk.CTkLabel(
            note,
            text="This project is an academic proof of concept (TRL 3). It does not "
                 "claim any official association with Smart India Hackathon or with "
                 "any government organization; the SIH entry is referenced only as "
                 "the example listed on the LPU EDU-Revolution projects page.",
            font=(FONT, 11), text_color="gray", justify="left", anchor="w",
        ).pack(fill="x", padx=4, pady=(0, 16))


def run():
    """Entry point used by main.py."""
    logger = get_logger()

    def _exception_hook(exc_type, exc, tb):
        """Catch ANY unexpected error: log it, tell the user, keep running."""
        logger.error("Uncaught exception:", exc_info=(exc_type, exc, tb))
        try:
            messagebox.showerror(
                APP_TITLE,
                f"Unexpected error:\n{exc}\n\nDetails were logged to "
                "logs/app.log — the application keeps running.",
            )
        except Exception:  # noqa: BLE001 - last-resort safety net
            pass

    sys.excepthook = _exception_hook
    ensure_dir(REPORTS_DIR)
    logger.info("Starting %s v%s on %s", APP_TITLE, APP_VERSION,
                os.name)
    app = SystemConfigApp()
    app.mainloop()


if __name__ == "__main__":
    run()
