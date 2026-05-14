import math
import os
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageTk
import yt_dlp

# ── Palette (matches web app) ─────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG      = "#07070f"
SURF    = "#0e0e1c"
SURF2   = "#13132a"
BORDER  = "#1d1d38"
VIOLET  = "#7c3aed"
VIOLET2 = "#6d28d9"
VIOLET3 = "#4c1d95"
TEXT    = "#e2e8f0"
DIM     = "#64748b"
MUTE    = "#2d2d52"
GREEN   = "#22c55e"
RED     = "#ef4444"
AMBER   = "#f59e0b"

PLATFORMS = [
    ("YouTube",   "#FF4444"),
    ("TikTok",    "#00d4d4"),
    ("Facebook",  "#4090f7"),
    ("Instagram", "#e1306c"),
    ("Twitter/X", "#1d9bf0"),
    ("Khác",      "#a78bfa"),
]
PCOLORS = dict(PLATFORMS)

DOWNLOAD_DIR = Path.home() / "Downloads" / "VidGet"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── PIL helpers ───────────────────────────────────────────────────────────────

def _hex(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i]) * t) for i in range(3))

def make_hero_bg(w: int, h: int) -> ImageTk.PhotoImage:
    img = Image.new("RGB", (w, h))
    c1, c2 = _hex("#07070f"), _hex("#0e0c2e")
    for y in range(h):
        img.paste(Image.new("RGB", (w, 1), _lerp(c1, c2, y/h)), (0, y))

    # violet glow orb top-centre
    orb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od  = ImageDraw.Draw(orb)
    od.ellipse([w//2-260, -140, w//2+260, 180], fill=(124, 58, 237, 38))
    orb = orb.filter(ImageFilter.GaussianBlur(70))
    img.paste(orb, (0, 0), orb)

    # blue orb right
    orb2 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od2  = ImageDraw.Draw(orb2)
    od2.ellipse([w-300, -80, w+80, 200], fill=(56, 100, 220, 28))
    orb2 = orb2.filter(ImageFilter.GaussianBlur(60))
    img.paste(orb2, (0, 0), orb2)

    return ImageTk.PhotoImage(img)

def make_glow_btn(w: int, h: int, hex_color: str) -> ImageTk.PhotoImage:
    pad = 28
    img = Image.new("RGBA", (w + pad*2, h + pad*2), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    r, g, b = _hex(hex_color)
    d.rounded_rectangle([pad, pad, w+pad, h+pad], radius=12, fill=(r, g, b, 140))
    img = img.filter(ImageFilter.GaussianBlur(18))
    return ImageTk.PhotoImage(img)

def make_icon(size: int = 48) -> ImageTk.PhotoImage:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    # Outer glow
    d.ellipse([0, 0, size-1, size-1], fill=(124, 58, 237, 50))
    # Inner circle
    p = 6
    d.ellipse([p, p, size-1-p, size-1-p], fill=(124, 58, 237, 255))
    # V mark
    cx, cy = size//2, size//2
    arm = size * 0.22
    d.line([(cx - arm, cy - arm*0.6), (cx, cy + arm*0.7)], fill="white", width=round(size*0.1))
    d.line([(cx + arm, cy - arm*0.6), (cx, cy + arm*0.7)], fill="white", width=round(size*0.1))
    img = img.filter(ImageFilter.SMOOTH)
    return ImageTk.PhotoImage(img)

def _dim_color(hex_color: str, factor: float = 0.18) -> str:
    r, g, b = _hex(hex_color)
    return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"


# ── Download task ─────────────────────────────────────────────────────────────

class DownloadTask:
    def __init__(self, url: str, platform: str):
        self.url      = url
        self.platform = platform
        self.title    = "Đang lấy thông tin..."
        self.status   = "pending"
        self.cancel   = threading.Event()


# ── Download row ──────────────────────────────────────────────────────────────

class DownloadRow(ctk.CTkFrame):
    def __init__(self, parent, task: DownloadTask, app, **kw):
        super().__init__(parent, fg_color=SURF, corner_radius=14,
                         border_width=1, border_color=BORDER, **kw)
        self.task  = task
        self.app   = app
        self.color = PCOLORS.get(task.platform, "#a78bfa")
        self._build()

    def _build(self):
        # Left accent stripe
        tk.Frame(self, width=4, bg=self.color).pack(side="left", fill="y")

        # Platform badge
        ctk.CTkLabel(
            self,
            text=self.task.platform[:2].upper(),
            width=40, height=40, corner_radius=10,
            fg_color=_dim_color(self.color, 0.2),
            text_color=self.color,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        ).pack(side="left", padx=(10, 0), pady=14)

        # Right buttons (packed before center to not get squeezed)
        self._btns = ctk.CTkFrame(self, fg_color="transparent")
        self._btns.pack(side="right", padx=(0, 14), pady=14)

        self.stop_btn = ctk.CTkButton(
            self._btns, text="■  Stop",
            width=86, height=30, corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#3b0a0a", hover_color="#7f1d1d", text_color="#fca5a5",
            command=self._stop,
        )
        self.stop_btn.pack()

        self.open_btn = ctk.CTkButton(
            self._btns, text="📁  Mở thư mục",
            width=114, height=30, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="#0c2340", hover_color="#1e3a5f", text_color="#93c5fd",
            command=self._open_folder,
        )

        self.retry_btn = ctk.CTkButton(
            self._btns, text="↺  Thử lại",
            width=86, height=30, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="#2d1a00", hover_color="#451a03", text_color="#fcd34d",
            command=self._retry,
        )

        # Center: title + status + progress
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(side="left", fill="both", expand=True, padx=(10, 8), pady=12)

        self.title_lbl = ctk.CTkLabel(
            mid, text=self.task.title, anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT,
        )
        self.title_lbl.pack(fill="x")

        self.sub_lbl = ctk.CTkLabel(
            mid, text="Đang chuẩn bị...", anchor="w",
            font=ctk.CTkFont(size=11), text_color=DIM,
        )
        self.sub_lbl.pack(fill="x", pady=(2, 5))

        self.progress = ctk.CTkProgressBar(
            mid, height=4, corner_radius=2,
            fg_color=SURF2, progress_color=self.color,
        )
        self.progress.set(0)
        self.progress.pack(fill="x")

    def update_title(self, title: str):
        short = (title[:72] + "…") if len(title) > 72 else title
        self.title_lbl.configure(text=short)

    def update_progress(self, pct: float, speed: str = ""):
        self.progress.set(pct / 100)
        label = f"{pct:.0f}%"
        if speed:
            label += f"  ·  {speed}"
        self.sub_lbl.configure(text=label, text_color=DIM)

    def mark_success(self):
        self.progress.set(1.0)
        self.progress.configure(progress_color=GREEN)
        self.sub_lbl.configure(text="✓  Hoàn thành", text_color=GREEN)
        self.stop_btn.pack_forget()
        self.open_btn.pack()

    def mark_failed(self, msg: str = ""):
        self.progress.configure(progress_color=RED)
        self.sub_lbl.configure(text=f"✗  {msg or 'Tải thất bại'}"[:80], text_color=RED)
        self.stop_btn.pack_forget()
        self.retry_btn.pack()

    def _stop(self):
        self.task.cancel.set()
        self.sub_lbl.configure(text="Đã hủy", text_color=DIM)
        self.stop_btn.pack_forget()

    def _open_folder(self):
        os.startfile(str(DOWNLOAD_DIR))

    def _retry(self):
        self.task.cancel.clear()
        self.task.status = "pending"
        self.progress.set(0)
        self.progress.configure(progress_color=self.color)
        self.sub_lbl.configure(text="Đang chuẩn bị...", text_color=DIM)
        self.retry_btn.pack_forget()
        self.stop_btn.pack()
        threading.Thread(
            target=self.app._run_download, args=(self.task, self), daemon=True
        ).start()


# ── App window ────────────────────────────────────────────────────────────────

class VidGetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VidGet")
        self.geometry("1000x760")
        self.minsize(780, 560)
        self.configure(fg_color=BG)
        self.current_platform = "YouTube"
        self._tab_btns: dict[str, ctk.CTkButton] = {}
        self._hero_photo = None
        self._glow_photo = None
        self._icon_photo = None
        self._build_ui()
        self.bind("<Configure>", self._on_resize)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_hero()
        self._build_usp()
        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(fill="x")
        self._build_tabs()
        self._build_input()
        self._build_list()

    # Hero (gradient canvas + logo + title + tagline)
    def _build_hero(self):
        self._hero_canvas = tk.Canvas(self, height=168, highlightthickness=0, bd=0)
        self._hero_canvas.pack(fill="x")
        self.after(60, self._render_hero)

    def _render_hero(self, _event=None):
        cv = self._hero_canvas
        w  = cv.winfo_width()
        h  = cv.winfo_height()
        if w < 2:
            self.after(80, self._render_hero)
            return

        cv.delete("all")

        # Gradient background
        self._hero_photo = make_hero_bg(w, h)
        cv.create_image(0, 0, anchor="nw", image=self._hero_photo)

        # ── Logo icon ──
        self._icon_photo = make_icon(52)
        cv.create_image(36, h//2, anchor="center", image=self._icon_photo)

        # ── Title: "VidGet" ──
        cv.create_text(68, h//2 - 20, text="Vid", anchor="w",
            fill=TEXT, font=("Segoe UI", 28, "bold"))
        # Measure "Vid" text width (approx)
        vid_w = 52
        cv.create_text(68 + vid_w, h//2 - 20, text="Get", anchor="w",
            fill=VIOLET, font=("Segoe UI", 28, "bold"))

        # ── Tagline ──
        cv.create_text(68, h//2 + 10, anchor="w",
            text="Tải video từ mọi nền tảng · Nhanh · Miễn phí · Không giới hạn",
            fill=DIM, font=("Segoe UI", 11))

        # ── Badge "Free · No signup" ──
        badge_x, badge_y = w - 24, h//2
        cv.create_text(badge_x, badge_y - 8, anchor="e",
            text="✦  Miễn phí · Không đăng ký · Không quảng cáo",
            fill="#4c1d95", font=("Segoe UI", 10, "bold"))
        cv.create_text(badge_x, badge_y + 12, anchor="e",
            text=f"📁  {DOWNLOAD_DIR}",
            fill=MUTE, font=("Segoe UI", 9))

    # USP row
    def _build_usp(self):
        usp_data = [
            ("⚡", "Tốc độ tối đa",     "Không giới hạn băng thông,\nkhông hàng chờ."),
            ("🛡", "Riêng tư & An toàn", "Link không lưu lại.\nDữ liệu là của bạn."),
            ("🌐", "500+ Nền tảng",      "YouTube, TikTok, Facebook,\nInstagram và hàng trăm site khác."),
        ]

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(14, 12))
        row.grid_columnconfigure((0, 1, 2), weight=1, uniform="usp")

        for i, (icon, title, desc) in enumerate(usp_data):
            card = ctk.CTkFrame(
                row, fg_color=SURF, corner_radius=14,
                border_width=1, border_color=BORDER,
            )
            card.grid(row=0, column=i, padx=5, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=18, pady=14, anchor="w")

            ctk.CTkLabel(inner, text=icon,
                font=ctk.CTkFont(size=22), text_color=TEXT
            ).pack(anchor="w")

            ctk.CTkLabel(inner, text=title,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=TEXT,
            ).pack(anchor="w", pady=(4, 0))

            ctk.CTkLabel(inner, text=desc,
                font=ctk.CTkFont(size=11), text_color=DIM,
                justify="left", anchor="w",
            ).pack(anchor="w", pady=(3, 0))

    # Platform tabs
    def _build_tabs(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(14, 0))

        ctk.CTkLabel(row, text="PLATFORM",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=MUTE,
        ).pack(side="left", padx=(0, 12))

        for name, color in PLATFORMS:
            btn = ctk.CTkButton(
                row, text=name, width=90, height=30, corner_radius=15,
                font=ctk.CTkFont(size=12),
                fg_color=SURF2, hover_color=BORDER,
                text_color=DIM, border_width=1, border_color=BORDER,
                command=lambda p=name: self._select_platform(p),
            )
            btn.pack(side="left", padx=3)
            self._tab_btns[name] = btn

        self._select_platform("YouTube")

    # URL input with glowing button
    def _build_input(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="x", padx=24, pady=(12, 0))

        card = ctk.CTkFrame(wrap, fg_color=SURF, corner_radius=16,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x")

        self.url_entry = ctk.CTkEntry(
            card,
            placeholder_text="  Dán link video vào đây…",
            height=54, border_width=0, fg_color="transparent",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=TEXT, placeholder_text_color=MUTE,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=7)
        self.url_entry.bind("<Return>", lambda _: self._on_download())

        # Glow button wrapper
        btn_wrap = ctk.CTkFrame(card, fg_color="transparent")
        btn_wrap.pack(side="right", padx=8, pady=7)

        BW, BH = 152, 42
        self._glow_canvas = tk.Canvas(btn_wrap, width=BW+34, height=BH+34,
                                      bg=SURF, highlightthickness=0)
        self._glow_canvas.pack()

        self._glow_photo = make_glow_btn(BW, BH, VIOLET)
        self._glow_canvas.create_image((BW+34)//2, (BH+34)//2,
                                       image=self._glow_photo)

        self.dl_btn = ctk.CTkButton(
            self._glow_canvas, text="⬇  Tải xuống",
            width=BW, height=BH, corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=VIOLET, hover_color=VIOLET2, text_color="white",
            command=self._on_download,
        )
        self._glow_canvas.create_window((BW+34)//2, (BH+34)//2, window=self.dl_btn)

    # Scrollable list
    def _build_list(self):
        # Column header
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=22)
        hdr.pack(fill="x", padx=28, pady=(10, 2))
        hdr.pack_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)
        kw = dict(font=ctk.CTkFont(size=10, weight="bold"), text_color=MUTE)
        ctk.CTkLabel(hdr, text="NỀN TẢNG", width=58, anchor="w", **kw
            ).grid(row=0, column=0, padx=(10, 0))
        ctk.CTkLabel(hdr, text="TÊN VIDEO", anchor="w", **kw
            ).grid(row=0, column=1, padx=12, sticky="ew")
        ctk.CTkLabel(hdr, text="TIẾN ĐỘ", width=80, anchor="w", **kw
            ).grid(row=0, column=2)
        ctk.CTkLabel(hdr, text="THAO TÁC", width=118, anchor="center", **kw
            ).grid(row=0, column=3, padx=(0, 14))

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=SURF2,
            scrollbar_button_hover_color=BORDER,
        )
        self.scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Empty state
        self._empty = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._empty.pack(expand=True, pady=50)

        ctk.CTkLabel(self._empty, text="⬇",
            font=ctk.CTkFont(size=40), text_color=MUTE).pack()
        ctk.CTkLabel(self._empty,
            text="Chưa có video nào",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=DIM).pack(pady=(8, 2))
        ctk.CTkLabel(self._empty,
            text="Dán link vào ô bên trên và nhấn Tải xuống để bắt đầu",
            font=ctk.CTkFont(size=11), text_color=MUTE).pack()

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_resize(self, event):
        if event.widget is self:
            self.after_cancel(getattr(self, "_resize_job", None) or "x")
            self._resize_job = self.after(120, self._render_hero)

    def _select_platform(self, platform: str):
        self.current_platform = platform
        for name, color in PLATFORMS:
            btn = self._tab_btns[name]
            if name == platform:
                btn.configure(text_color=color, border_color=color,
                              fg_color=_dim_color(color, 0.18))
            else:
                btn.configure(text_color=DIM, border_color=BORDER, fg_color=SURF2)

    def _on_download(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        self.url_entry.delete(0, "end")
        self._empty.pack_forget()

        task = DownloadTask(url, self.current_platform)
        row  = DownloadRow(self.scroll, task, self)
        row.pack(fill="x", pady=(0, 10))

        threading.Thread(
            target=self._run_download, args=(task, row), daemon=True
        ).start()

    # ── Download worker ───────────────────────────────────────────────────────

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
