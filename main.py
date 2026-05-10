import customtkinter as ctk
import threading
import yt_dlp
import os
from pathlib import Path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DOWNLOAD_DIR = Path.home() / "Downloads" / "VidGet"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

PLATFORMS = ["YouTube", "TikTok", "Facebook", "Instagram", "Twitter/X", "Khác"]

PLATFORM_COLORS = {
    "YouTube":   "#FF0000",
    "TikTok":    "#2D2D2D",
    "Facebook":  "#1877F2",
    "Instagram": "#C13584",
    "Twitter/X": "#1DA1F2",
    "Khác":      "#6B7280",
}


class DownloadTask:
    def __init__(self, url: str, platform: str):
        self.url = url
        self.platform = platform
        self.title = "Đang lấy thông tin..."
        self.status = "pending"


class DownloadRow(ctk.CTkFrame):
    def __init__(self, parent, task: DownloadTask, app, **kw):
        super().__init__(parent, corner_radius=8, **kw)
        self.task = task
        self.app = app
        self.configure(fg_color=("gray87", "gray22"))
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)

        # Platform badge
        color = PLATFORM_COLORS.get(self.task.platform, "#6B7280")
        ctk.CTkLabel(
            self, text=self.task.platform[:3],
            width=44, height=26, corner_radius=6,
            fg_color=color, text_color="white",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=0, padx=(10, 0), pady=10)

        # Video title
        self.title_lbl = ctk.CTkLabel(
            self, text=self.task.title,
            anchor="w", justify="left",
            font=ctk.CTkFont(size=13),
        )
        self.title_lbl.grid(row=0, column=1, padx=8, pady=10, sticky="ew")

        # Progress / status indicator
        self.status_lbl = ctk.CTkLabel(
            self, text="⏳  Chờ...",
            width=170, anchor="center",
            font=ctk.CTkFont(size=12),
            text_color="gray55",
        )
        self.status_lbl.grid(row=0, column=2, padx=6, pady=10)

        # Open folder button
        self.open_btn = ctk.CTkButton(
            self, text="📁", width=38, height=30,
            state="disabled", fg_color="gray35", hover_color="gray45",
            font=ctk.CTkFont(size=14),
            command=self._open_folder,
        )
        self.open_btn.grid(row=0, column=3, padx=2, pady=10)

        # Retry button
        self.retry_btn = ctk.CTkButton(
            self, text="↺", width=38, height=30,
            state="disabled", fg_color="gray35", hover_color="gray45",
            font=ctk.CTkFont(size=17, weight="bold"),
            command=self._retry,
        )
        self.retry_btn.grid(row=0, column=4, padx=(2, 10), pady=10)

    # ── State transitions (always called from main thread via after()) ──

    def update_title(self, title: str):
        short = title[:68] + "…" if len(title) > 68 else title
        self.title_lbl.configure(text=short)

    def update_progress(self, pct: float, speed: str = ""):
        text = f"⬇  {pct:.0f}%"
        if speed:
            text += f"   {speed}"
        self.status_lbl.configure(text=text, text_color=("gray25", "gray80"))

    def mark_success(self):
        self.status_lbl.configure(text="✅  Hoàn thành", text_color="#22C55E")
        self.open_btn.configure(
            state="normal", fg_color="#2563EB", hover_color="#1D4ED8"
        )

    def mark_failed(self):
        self.status_lbl.configure(text="❌  Thất bại", text_color="#EF4444")
        self.retry_btn.configure(
            state="normal", fg_color="#EA580C", hover_color="#C2410C"
        )

    # ── Button callbacks ──

    def _open_folder(self):
        os.startfile(str(DOWNLOAD_DIR))

    def _retry(self):
        self.task.status = "pending"
        self.status_lbl.configure(text="⏳  Chờ...", text_color="gray55")
        self.retry_btn.configure(state="disabled", fg_color="gray35")
        threading.Thread(
            target=self.app._run_download,
            args=(self.task, self),
            daemon=True,
        ).start()


class VidGetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VidGet")
        self.geometry("920x660")
        self.minsize(720, 500)
        self.current_platform = "YouTube"
        self._tab_btns: dict[str, ctk.CTkButton] = {}
        self._build_ui()

    # ─────────────────────────── UI construction ───────────────────────────

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=22, pady=(18, 4))
        ctk.CTkLabel(
            hdr, text="VidGet",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            hdr, text="Video Downloader",
            font=ctk.CTkFont(size=12), text_color="gray55",
        ).pack(side="left", padx=10, pady=7)

        # Platform tabs
        tabs = ctk.CTkFrame(self, fg_color="transparent")
        tabs.pack(fill="x", padx=22, pady=(0, 8))
        for p in PLATFORMS:
            active = p == self.current_platform
            btn = ctk.CTkButton(
                tabs, text=p,
                width=90, height=32, corner_radius=16,
                font=ctk.CTkFont(size=12),
                fg_color=PLATFORM_COLORS[p] if active else "gray30",
                hover_color="gray45",
                command=lambda pl=p: self._select_platform(pl),
            )
            btn.pack(side="left", padx=3)
            self._tab_btns[p] = btn

        # URL input card
        card = ctk.CTkFrame(self, corner_radius=12)
        card.pack(fill="x", padx=22, pady=6)

        self.url_entry = ctk.CTkEntry(
            card,
            placeholder_text="Dán link video vào đây…",
            height=46, border_width=0, fg_color="transparent",
            font=ctk.CTkFont(size=14),
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(14, 8), pady=8)
        self.url_entry.bind("<Return>", lambda _: self._on_download())

        ctk.CTkButton(
            card, text="Tải xuống  ⬇",
            height=40, width=144,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            command=self._on_download,
        ).pack(side="right", padx=10, pady=8)

        # Column headers (aligned with row grid)
        col_hdr = ctk.CTkFrame(self, fg_color="transparent", height=24)
        col_hdr.pack(fill="x", padx=22, pady=(8, 2))
        col_hdr.grid_propagate(False)
        col_hdr.grid_columnconfigure(1, weight=1)

        lbl_kw = dict(font=ctk.CTkFont(size=11, weight="bold"), text_color="gray50")
        ctk.CTkLabel(col_hdr, text="Nền tảng", width=54, anchor="w",  **lbl_kw).grid(row=0, column=0, padx=(10, 0))
        ctk.CTkLabel(col_hdr, text="Tên video",        anchor="w",  **lbl_kw).grid(row=0, column=1, padx=8, sticky="ew")
        ctk.CTkLabel(col_hdr, text="Tiến độ", width=170, anchor="center", **lbl_kw).grid(row=0, column=2, padx=6)
        ctk.CTkLabel(col_hdr, text="Thao tác", width=92, anchor="center", **lbl_kw).grid(row=0, column=3, padx=2, columnspan=2)

        # Scrollable download list
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.scroll.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        self._empty_lbl = ctk.CTkLabel(
            self.scroll,
            text="Chưa có video nào.\nDán link rồi nhấn 'Tải xuống' để bắt đầu.",
            font=ctk.CTkFont(size=13), text_color="gray55", justify="center",
        )
        self._empty_lbl.pack(expand=True, pady=70)

    # ─────────────────────────── Event handlers ────────────────────────────

    def _select_platform(self, platform: str):
        self.current_platform = platform
        for p, btn in self._tab_btns.items():
            btn.configure(
                fg_color=PLATFORM_COLORS[p] if p == platform else "gray30"
            )

    def _on_download(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        self.url_entry.delete(0, "end")
        self._empty_lbl.pack_forget()

        task = DownloadTask(url, self.current_platform)
        row = DownloadRow(self.scroll, task, self)
        row.pack(fill="x", padx=4, pady=3)

        threading.Thread(
            target=self._run_download, args=(task, row), daemon=True
        ).start()

    # ─────────────────────────── Download logic ────────────────────────────

    def _run_download(self, task: DownloadTask, row: DownloadRow):
        def hook(d: dict):
            if d["status"] != "downloading":
                return
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            done = d.get("downloaded_bytes", 0)
            pct = done / total * 100 if total else 0
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
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(task.url, download=True)
                task.title = info.get("title", task.url)
                task.status = "done"
                self.after(0, row.update_title, task.title)
                self.after(0, row.mark_success)
        except Exception:
            task.status = "failed"
            self.after(0, row.mark_failed)


if __name__ == "__main__":
    app = VidGetApp()
    app.mainloop()
