import os
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
import yt_dlp

# ── Theme ─────────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG        = "#07070f"
SURFACE   = "#0e0e1c"
SURFACE2  = "#13132a"
BORDER    = "#1d1d38"
VIOLET    = "#7c3aed"
VIOLET_H  = "#6d28d9"
TEXT      = "#e2e8f0"
TEXT_DIM  = "#64748b"
TEXT_MUTE = "#2d2d52"
GREEN     = "#22c55e"
RED       = "#ef4444"
AMBER     = "#f59e0b"

DOWNLOAD_DIR = Path.home() / "Downloads" / "VidGet"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

PLATFORMS = [
    ("YouTube",   "#FF4444"),
    ("TikTok",    "#00d4d4"),
    ("Facebook",  "#4090f7"),
    ("Instagram", "#e1306c"),
    ("Twitter/X", "#1d9bf0"),
    ("Khác",      "#a78bfa"),
]
PLATFORM_COLORS = dict(PLATFORMS)

# Darker tint of each platform color for badge bg
def _dim(hex_color: str, factor: float = 0.15) -> str:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"


# ── Data ──────────────────────────────────────────────────────────────────────

class DownloadTask:
    def __init__(self, url: str, platform: str):
        self.url      = url
        self.platform = platform
        self.title    = "Đang lấy thông tin..."
        self.status   = "pending"
        self.cancel   = threading.Event()


# ── Download Row ──────────────────────────────────────────────────────────────

class DownloadRow(ctk.CTkFrame):
    def __init__(self, parent, task: DownloadTask, app, **kw):
        super().__init__(
            parent,
            fg_color=SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            **kw,
        )
        self.task  = task
        self.app   = app
        self.color = PLATFORM_COLORS.get(task.platform, "#a78bfa")
        self._build()

    def _build(self):
        # ── Left accent stripe (raw tk for fill="y") ──
        stripe = tk.Frame(self, width=4, bg=self.color)
        stripe.pack(side="left", fill="y")

        # ── Platform badge ──
        badge_bg = _dim(self.color, 0.18)
        ctk.CTkLabel(
            self,
            text=self.task.platform[:2].upper(),
            width=40, height=40,
            corner_radius=10,
            fg_color=badge_bg,
            text_color=self.color,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        ).pack(side="left", padx=(10, 0), pady=14)

        # ── Right buttons (packed before center so they don't get squeezed) ──
        self._btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._btn_frame.pack(side="right", padx=(0, 14), pady=14)

        self.stop_btn = ctk.CTkButton(
            self._btn_frame, text="■  Stop",
            width=82, height=30, corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#3b0a0a", hover_color="#7f1d1d",
            text_color="#fca5a5",
            command=self._stop,
        )
        self.stop_btn.pack()

        self.open_btn = ctk.CTkButton(
            self._btn_frame, text="📁  Mở thư mục",
            width=110, height=30, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="#0c2340", hover_color="#1e3a5f",
            text_color="#93c5fd",
            command=self._open_folder,
        )

        self.retry_btn = ctk.CTkButton(
            self._btn_frame, text="↺  Thử lại",
            width=82, height=30, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="#2d1a00", hover_color="#451a03",
            text_color="#fcd34d",
            command=self._retry,
        )

        # ── Center: title + status + progress ──
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(side="left", fill="both", expand=True, padx=(10, 8), pady=12)

        self.title_lbl = ctk.CTkLabel(
            mid,
            text=self.task.title,
            anchor="w", justify="left",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT,
        )
        self.title_lbl.pack(fill="x")

        self.sub_lbl = ctk.CTkLabel(
            mid,
            text="Đang chuẩn bị...",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM,
        )
        self.sub_lbl.pack(fill="x", pady=(2, 5))

        self.progress = ctk.CTkProgressBar(
            mid,
            height=4,
            corner_radius=2,
            fg_color=SURFACE2,
            progress_color=self.color,
        )
        self.progress.set(0)
        self.progress.pack(fill="x")

    # ── State updates (called via app.after() from worker thread) ──

    def update_title(self, title: str):
        short = (title[:70] + "…") if len(title) > 70 else title
        self.title_lbl.configure(text=short)

    def update_progress(self, pct: float, speed: str = ""):
        self.progress.set(pct / 100)
        label = f"{pct:.0f}%"
        if speed:
            label += f"  ·  {speed}"
        self.sub_lbl.configure(text=label, text_color=TEXT_DIM)

    def mark_success(self):
        self.progress.set(1.0)
        self.progress.configure(progress_color=GREEN)
        self.sub_lbl.configure(text="✓  Hoàn thành", text_color=GREEN)
        self.stop_btn.pack_forget()
        self.open_btn.pack()

    def mark_failed(self, msg: str = ""):
        self.progress.configure(progress_color=RED)
        text = f"✗  {msg}" if msg else "✗  Tải thất bại"
        self.sub_lbl.configure(text=text[:80], text_color=RED)
        self.stop_btn.pack_forget()
        self.retry_btn.pack()

    # ── Button actions ──

    def _stop(self):
        self.task.cancel.set()
        self.sub_lbl.configure(text="Đã hủy", text_color=TEXT_DIM)
        self.stop_btn.pack_forget()

    def _open_folder(self):
        os.startfile(str(DOWNLOAD_DIR))

    def _retry(self):
        self.task.cancel.clear()
        self.task.status = "pending"
        self.progress.set(0)
        self.progress.configure(progress_color=self.color)
        self.sub_lbl.configure(text="Đang chuẩn bị...", text_color=TEXT_DIM)
        self.retry_btn.pack_forget()
        self.stop_btn.pack()
        threading.Thread(
            target=self.app._run_download,
            args=(self.task, self),
            daemon=True,
        ).start()


# ── Main App ──────────────────────────────────────────────────────────────────

class VidGetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VidGet")
        self.geometry("980x700")
        self.minsize(760, 520)
        self.configure(fg_color=BG)
        self.current_platform = "YouTube"
        self._tab_btns: dict[str, ctk.CTkButton] = {}
        self._build_ui()

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(24, 0))

        # Logo
        logo = ctk.CTkFrame(hdr, fg_color="transparent")
        logo.pack(side="left")
        ctk.CTkLabel(logo, text="Vid",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=TEXT).pack(side="left")
        ctk.CTkLabel(logo, text="Get",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=VIOLET).pack(side="left")

        # Separator dot + subtitle
        ctk.CTkLabel(hdr, text="  ·  Video Downloader",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM).pack(side="left", pady=8)

        # Save location pill
        ctk.CTkLabel(hdr,
            text=f"📁  ~/Downloads/VidGet",
            font=ctk.CTkFont(size=11),
            fg_color=SURFACE2, corner_radius=8,
            text_color=TEXT_DIM,
            padx=10, pady=5,
        ).pack(side="right")

        # ── Thin divider ────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(fill="x", pady=(18, 0))

        # ── Platform selector ────────────────────────────────────────────────
        tabs_row = ctk.CTkFrame(self, fg_color="transparent")
        tabs_row.pack(fill="x", padx=28, pady=(16, 0))

        ctk.CTkLabel(tabs_row, text="PLATFORM",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_MUTE).pack(side="left", padx=(0, 12))

        for name, color in PLATFORMS:
            btn = ctk.CTkButton(
                tabs_row, text=name,
                width=88, height=30, corner_radius=15,
                font=ctk.CTkFont(size=12),
                fg_color=SURFACE2, hover_color=BORDER,
                text_color=TEXT_DIM,
                border_width=1, border_color=BORDER,
                command=lambda p=name: self._select_platform(p),
            )
            btn.pack(side="left", padx=3)
            self._tab_btns[name] = btn

        self._select_platform("YouTube")

        # ── URL input card ───────────────────────────────────────────────────
        input_card = ctk.CTkFrame(
            self, fg_color=SURFACE, corner_radius=16,
            border_width=1, border_color=BORDER,
        )
        input_card.pack(fill="x", padx=28, pady=(14, 0))

        self.url_entry = ctk.CTkEntry(
            input_card,
            placeholder_text="  Dán link video vào đây…",
            height=52, border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=TEXT,
            placeholder_text_color=TEXT_MUTE,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=7)
        self.url_entry.bind("<Return>", lambda _: self._on_download())

        ctk.CTkButton(
            input_card, text="⬇  Tải xuống",
            height=42, width=150,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=VIOLET, hover_color=VIOLET_H,
            text_color="white",
            command=self._on_download,
        ).pack(side="right", padx=8, pady=7)

        # ── Scrollable list ──────────────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=SURFACE2,
            scrollbar_button_hover_color=BORDER,
        )
        self.scroll.pack(fill="both", expand=True, padx=28, pady=(16, 22))

        # Empty state
        self._empty = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._empty.pack(expand=True, pady=70)
        ctk.CTkLabel(self._empty, text="⬇",
            font=ctk.CTkFont(size=40), text_color=TEXT_MUTE).pack()
        ctk.CTkLabel(self._empty,
            text="Dán link và nhấn Tải xuống để bắt đầu",
            font=ctk.CTkFont(size=13), text_color=TEXT_DIM).pack(pady=(8, 0))

    # ── Platform selection ──────────────────────────────────────────────────

    def _select_platform(self, platform: str):
        self.current_platform = platform
        for name, color in PLATFORMS:
            btn = self._tab_btns[name]
            if name == platform:
                btn.configure(
                    text_color=color,
                    border_color=color,
                    fg_color=_dim(color, 0.18),
                )
            else:
                btn.configure(
                    text_color=TEXT_DIM,
                    border_color=BORDER,
                    fg_color=SURFACE2,
                )

    # ── Download trigger ────────────────────────────────────────────────────

    def _on_download(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        self.url_entry.delete(0, "end")
        self._empty.pack_forget()

        task = DownloadTask(url, self.current_platform)
        row = DownloadRow(self.scroll, task, self)
        row.pack(fill="x", pady=(0, 10))

        threading.Thread(
            target=self._run_download, args=(task, row), daemon=True
        ).start()

    # ── Worker ─────────────────────────────────────────────────────────────

    def _run_download(self, task: DownloadTask, row: DownloadRow):
        def hook(d: dict):
            if task.cancel.is_set():
                raise Exception("Cancelled")
            if d["status"] != "downloading":
                return
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            done  = d.get("downloaded_bytes", 0)
            pct   = done / total * 100 if total else 0
            speed = d.get("_speed_str", "")
            if task.title == "Đang lấy thông tin...":
                stem = Path(d.get("filename", "")).stem
                if stem:
                    task.title = stem
                    self.after(0, row.update_title, stem)
            self.after(0, row.update_progress, pct, speed)

        opts = {
            "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 5,
            "extractor_args": {
                "youtube": {"player_client": ["ios", "android", "tv_embedded"]},
            },
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(task.url, download=True)
                task.title  = info.get("title", task.url)
                task.status = "done"
                self.after(0, row.update_title, task.title)
                self.after(0, row.mark_success)
        except Exception as e:
            err = str(e)
            if "Cancelled" in err:
                return
            task.status = "failed"
            if "Sign in" in err or "bot" in err.lower() or "429" in err:
                err = "YouTube đang chặn server. Thử link khác."
            elif "unavailable" in err.lower() or "private" in err.lower():
                err = "Video không khả dụng hoặc bị giới hạn."
            self.after(0, row.mark_failed, err[:72])


if __name__ == "__main__":
    app = VidGetApp()
    app.mainloop()
