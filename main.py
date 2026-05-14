import math
import os
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageTk
import yt_dlp

# ── Palette — Apple dark + violet accent ──────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG      = "#08080f"   # near-black canvas
SURF    = "#111120"   # card surface
SURF2   = "#18182c"   # input / inner surface
BORDER  = "#22223a"   # ultra-subtle border
SEP     = "#1a1a2e"   # divider
VIOLET  = "#7c3aed"
V_LIGHT = "#9d6ff7"   # lighter violet for hover / text
V_DIM   = "#3b1a78"   # dark violet tint for bg
TEXT    = "#f0f0f8"   # primary label
LABEL2  = "#8e8ea8"   # secondary label
LABEL3  = "#44445a"   # tertiary / muted
GREEN   = "#30d158"   # Apple green
RED     = "#ff453a"   # Apple red
AMBER   = "#ffd60a"   # Apple yellow

PLATFORMS = [
    ("YouTube",   "#ff3b30"),
    ("TikTok",    "#30d6c8"),
    ("Facebook",  "#0a84ff"),
    ("Instagram", "#ff2d55"),
    ("Twitter/X", "#0a84ff"),
    ("Khác",      "#bf5af2"),
]
PCOLORS = dict(PLATFORMS)

DOWNLOAD_DIR = Path.home() / "Downloads" / "VidGet"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── PIL utilities ─────────────────────────────────────────────────────────────

def _hex(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def _dim(hex_color: str, f: float = 0.18) -> str:
    r, g, b = _hex(hex_color)
    return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"


def make_hero_bg(w: int, h: int) -> ImageTk.PhotoImage:
    """Very subtle gradient — Apple-style near-invisible depth."""
    img = Image.new("RGB", (w, h))
    c1, c2 = _hex("#08080f"), _hex("#0c0b1e")
    for y in range(h):
        img.paste(Image.new("RGB", (w, 1), _lerp(c1, c2, y / h)), (0, y))

    # Single soft violet orb, centred
    orb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d   = ImageDraw.Draw(orb)
    d.ellipse([w//2 - 220, -60, w//2 + 220, h + 20], fill=(108, 50, 210, 35))
    orb = orb.filter(ImageFilter.GaussianBlur(80))
    img.paste(orb, mask=orb.split()[3])
    return ImageTk.PhotoImage(img)


def make_app_icon(size: int = 72) -> ImageTk.PhotoImage:
    """iOS-style rounded-square app icon with gradient fill and V mark."""
    pad = 8
    total = size + pad * 2

    # Gradient fill (violet → indigo)
    base = Image.new("RGB", (size, size))
    d    = ImageDraw.Draw(base)
    c1, c2 = _hex("#9b59f5"), _hex("#5b2bd6")
    for y in range(size):
        base.paste(Image.new("RGB", (size, 1), _lerp(c1, c2, y / size)), (0, y))

    # iOS corner radius mask
    r    = size // 4
    mask = Image.new("L", (size, size), 0)
    md   = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=255)

    # Compose icon with transparent bg
    icon = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    base_rgba = base.convert("RGBA")
    icon.paste(base_rgba, (pad, pad), mask)

    # Soft outer glow
    glow = icon.filter(ImageFilter.GaussianBlur(pad))
    gl, gg, gb, ga = glow.split()
    ga   = ga.point(lambda x: int(x * 0.55))
    glow = Image.merge("RGBA", (gl, gg, gb, ga))
    final = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    final.paste(glow, mask=glow.split()[3])
    final.paste(icon, mask=icon.split()[3])

    # V lettermark — clean thick strokes
    fd  = ImageDraw.Draw(final)
    cx  = total // 2
    cy  = total // 2 + size // 16
    arm = size * 0.21
    lw  = max(4, size // 9)
    pts_l = [(cx - arm, cy - arm * 0.75), (cx, cy + arm * 0.65)]
    pts_r = [(cx + arm, cy - arm * 0.75), (cx, cy + arm * 0.65)]
    fd.line(pts_l, fill=(255, 255, 255, 245), width=lw)
    fd.line(pts_r, fill=(255, 255, 255, 245), width=lw)

    return ImageTk.PhotoImage(final)


def make_btn_glow(w: int, h: int) -> ImageTk.PhotoImage:
    """Soft violet aura under the primary button — Apple-like subtle glow."""
    pad = 24
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, w + pad, h + pad], radius=14, fill=(124, 58, 237, 120))
    img = img.filter(ImageFilter.GaussianBlur(20))
    return ImageTk.PhotoImage(img)


# ── Download task ─────────────────────────────────────────────────────────────

class DownloadTask:
    def __init__(self, url: str, platform: str):
        self.url      = url
        self.platform = platform
        self.title    = "Đang lấy thông tin..."
        self.status   = "pending"
        self.cancel   = threading.Event()


# ── Download row (Apple card style) ──────────────────────────────────────────

class DownloadRow(ctk.CTkFrame):
    def __init__(self, parent, task: DownloadTask, app, **kw):
        super().__init__(
            parent,
            fg_color=SURF,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
            **kw,
        )
        self.task  = task
        self.app   = app
        self.color = PCOLORS.get(task.platform, "#bf5af2")
        self._build()

    def _build(self):
        # Left accent
        tk.Frame(self, width=3, bg=self.color).pack(side="left", fill="y")

        # Badge
        ctk.CTkLabel(
            self,
            text=self.task.platform[:2].upper(),
            width=42, height=42,
            corner_radius=12,
            fg_color=_dim(self.color, 0.22),
            text_color=self.color,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        ).pack(side="left", padx=(12, 0), pady=14)

        # Action buttons (right-side, packed before center)
        self._btns = ctk.CTkFrame(self, fg_color="transparent")
        self._btns.pack(side="right", padx=(0, 14), pady=14)

        self.stop_btn = ctk.CTkButton(
            self._btns, text="Stop",
            width=72, height=28, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="#2d0a0a", hover_color="#5a1010", text_color="#ff6b6b",
            border_width=1, border_color="#5a1010",
            command=self._stop,
        )
        self.stop_btn.pack()

        self.open_btn = ctk.CTkButton(
            self._btns, text="Mở thư mục",
            width=96, height=28, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="#0a1f35", hover_color="#0d2a47", text_color="#5ac8fa",
            border_width=1, border_color="#0d2a47",
            command=self._open_folder,
        )

        self.retry_btn = ctk.CTkButton(
            self._btns, text="Thử lại",
            width=72, height=28, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="#261500", hover_color="#3d2000", text_color=AMBER,
            border_width=1, border_color="#3d2000",
            command=self._retry,
        )

        # Center content
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(side="left", fill="both", expand=True, padx=(12, 8), pady=13)

        self.title_lbl = ctk.CTkLabel(
            mid, text=self.task.title, anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT,
        )
        self.title_lbl.pack(fill="x")

        self.sub_lbl = ctk.CTkLabel(
            mid, text="Đang chuẩn bị…", anchor="w",
            font=ctk.CTkFont(size=11),
            text_color=LABEL2,
        )
        self.sub_lbl.pack(fill="x", pady=(2, 6))

        self.bar = ctk.CTkProgressBar(
            mid, height=3, corner_radius=2,
            fg_color=SURF2, progress_color=self.color,
        )
        self.bar.set(0)
        self.bar.pack(fill="x")

    # ── Updates ──────────────────────────────────────────────────────────────

    def update_title(self, title: str):
        self.title_lbl.configure(text=(title[:70] + "…") if len(title) > 70 else title)

    def update_progress(self, pct: float, speed: str = ""):
        self.bar.set(pct / 100)
        txt = f"{pct:.0f}%"
        if speed:
            txt += f"  ·  {speed}"
        self.sub_lbl.configure(text=txt, text_color=LABEL2)

    def mark_success(self):
        self.bar.set(1.0)
        self.bar.configure(progress_color=GREEN)
        self.sub_lbl.configure(text="Hoàn thành", text_color=GREEN)
        self.stop_btn.pack_forget()
        self.open_btn.pack()

    def mark_failed(self, msg: str = ""):
        self.bar.configure(progress_color=RED)
        self.sub_lbl.configure(text=msg or "Tải thất bại", text_color=RED)
        self.stop_btn.pack_forget()
        self.retry_btn.pack()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _stop(self):
        self.task.cancel.set()
        self.sub_lbl.configure(text="Đã hủy", text_color=LABEL3)
        self.stop_btn.pack_forget()

    def _open_folder(self):
        os.startfile(str(DOWNLOAD_DIR))

    def _retry(self):
        self.task.cancel.clear()
        self.task.status = "pending"
        self.bar.set(0)
        self.bar.configure(progress_color=self.color)
        self.sub_lbl.configure(text="Đang chuẩn bị…", text_color=LABEL2)
        self.retry_btn.pack_forget()
        self.stop_btn.pack()
        threading.Thread(
            target=self.app._run_download, args=(self.task, self), daemon=True
        ).start()


# ── Main window ───────────────────────────────────────────────────────────────

class VidGetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VidGet")
        self.geometry("960x740")
        self.minsize(760, 560)
        self.configure(fg_color=BG)
        self.current_platform = "YouTube"
        self._tab_btns: dict[str, ctk.CTkButton] = {}
        self._hero_photo = None
        self._icon_photo = None
        self._glow_photo = None
        self._build_ui()
        self.bind("<Configure>", self._on_resize)

    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_hero()
        self._build_tabs()
        self._build_input()
        self._build_list()   # expands to fill space
        self._build_usp()    # pinned at bottom

    # ── Hero ─────────────────────────────────────────────────────────────────

    def _build_hero(self):
        self._hero_cv = tk.Canvas(self, height=186, highlightthickness=0, bd=0)
        self._hero_cv.pack(fill="x")
        self.after(60, self._render_hero)

    def _render_hero(self, _=None):
        cv = self._hero_cv
        w  = cv.winfo_width()
        h  = cv.winfo_height()
        if w < 4:
            self.after(80, self._render_hero)
            return

        cv.delete("all")

        # Gradient background
        self._hero_photo = make_hero_bg(w, h)
        cv.create_image(0, 0, anchor="nw", image=self._hero_photo)

        cx = w // 2

        # App icon — centred
        self._icon_photo = make_app_icon(64)
        icon_y = 58
        cv.create_image(cx, icon_y, anchor="center", image=self._icon_photo)

        # App name — single centred text, two-colour trick via two anchored texts
        # Measure approx: "Vid" in Segoe UI 30 bold ≈ 56px wide
        half_title = 56
        cv.create_text(cx - 1, icon_y + 54, text="Vid",
            anchor="e", fill=TEXT,   font=("Segoe UI", 28, "bold"))
        cv.create_text(cx + 1, icon_y + 54, text="Get",
            anchor="w", fill=V_LIGHT, font=("Segoe UI", 28, "bold"))

        # Tagline
        cv.create_text(cx, icon_y + 84,
            text="Tải video từ mọi nền tảng · Nhanh · Miễn phí · Không giới hạn",
            fill=LABEL2, font=("Segoe UI", 11), anchor="center")

        # Thin horizontal rule at bottom of hero
        cv.create_line(0, h - 1, w, h - 1, fill=SEP)

    # ── Platform tabs (Apple segmented feel) ─────────────────────────────────

    def _build_tabs(self):
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="x", padx=26, pady=(16, 0))

        ctk.CTkLabel(outer, text="PLATFORM",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=LABEL3).pack(side="left", padx=(0, 14))

        for name, color in PLATFORMS:
            btn = ctk.CTkButton(
                outer, text=name,
                width=86, height=28, corner_radius=14,
                font=ctk.CTkFont(size=11),
                fg_color=SURF2, hover_color=BORDER,
                text_color=LABEL2,
                border_width=1, border_color=BORDER,
                command=lambda p=name: self._select_platform(p),
            )
            btn.pack(side="left", padx=2)
            self._tab_btns[name] = btn

        self._select_platform("YouTube")

    # ── URL input + glow download button ─────────────────────────────────────

    def _build_input(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="x", padx=26, pady=(12, 0))

        # Input pill — Apple search-bar style
        bar = ctk.CTkFrame(wrap, fg_color=SURF2, corner_radius=14,
                           border_width=1, border_color=BORDER)
        bar.pack(fill="x")

        # Search icon
        ctk.CTkLabel(bar, text="⌕",
            font=ctk.CTkFont(size=18), text_color=LABEL3,
            fg_color="transparent").pack(side="left", padx=(14, 0))

        self.url_entry = ctk.CTkEntry(
            bar,
            placeholder_text="Dán link video vào đây…",
            height=48, border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT,
            placeholder_text_color=LABEL3,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(6, 0), pady=5)
        self.url_entry.bind("<Return>", lambda _: self._on_download())

        # Glow button wrapper
        BW, BH = 140, 38
        pad = 20
        self._glow_cv = tk.Canvas(
            bar, width=BW + pad * 2, height=BH + pad * 2,
            bg=SURF2, highlightthickness=0,
        )
        self._glow_cv.pack(side="right", padx=6, pady=5)

        self._glow_photo = make_btn_glow(BW, BH)
        self._glow_cv.create_image((BW + pad * 2) // 2, (BH + pad * 2) // 2,
                                   image=self._glow_photo)

        self.dl_btn = ctk.CTkButton(
            self._glow_cv, text="⬇  Tải xuống",
            width=BW, height=BH, corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=VIOLET, hover_color="#6d28d9", text_color="white",
            command=self._on_download,
        )
        self._glow_cv.create_window(
            (BW + pad * 2) // 2, (BH + pad * 2) // 2, window=self.dl_btn
        )

    # ── Scrollable download list ──────────────────────────────────────────────

    def _build_list(self):
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=SURF2,
            scrollbar_button_hover_color=BORDER,
        )
        self.scroll.pack(fill="both", expand=True, padx=26, pady=(12, 0))

        self._empty = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._empty.pack(expand=True, pady=40)

        ctk.CTkLabel(self._empty, text="⬇",
            font=ctk.CTkFont(size=36), text_color=LABEL3).pack()
        ctk.CTkLabel(self._empty,
            text="Chưa có video nào",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=LABEL2).pack(pady=(10, 3))
        ctk.CTkLabel(self._empty,
            text="Dán link vào ô bên trên và nhấn Tải xuống",
            font=ctk.CTkFont(size=11), text_color=LABEL3).pack()

    # ── USP strip — bottom ────────────────────────────────────────────────────

    def _build_usp(self):
        # Top separator
        ctk.CTkFrame(self, height=1, fg_color=SEP).pack(fill="x")

        usp_data = [
            ("⚡", "Siêu nhanh",         "Không giới hạn tốc độ hay hàng chờ"),
            ("🛡", "Riêng tư & An toàn", "Link không được lưu lại sau khi tải"),
            ("🌐", "500+ Nền tảng",       "YouTube · TikTok · Facebook và nhiều hơn"),
        ]

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=26, pady=(10, 14))
        row.grid_columnconfigure((0, 1, 2), weight=1, uniform="usp")

        for i, (icon, title, desc) in enumerate(usp_data):
            cell = ctk.CTkFrame(row, fg_color="transparent")
            cell.grid(row=0, column=i, sticky="nsew")

            # Vertical left-border only for middle cell dividers
            if i > 0:
                tk.Frame(cell, width=1, bg=SEP).pack(side="left", fill="y", padx=(0, 14))

            content = ctk.CTkFrame(cell, fg_color="transparent")
            content.pack(side="left", padx=(0 if i == 0 else 0, 0), pady=4, anchor="center")

            ctk.CTkLabel(content, text=icon,
                font=ctk.CTkFont(size=18), text_color=TEXT
            ).pack(anchor="w")

            ctk.CTkLabel(content, text=title,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=TEXT,
            ).pack(anchor="w", pady=(3, 0))

            ctk.CTkLabel(content, text=desc,
                font=ctk.CTkFont(size=10),
                text_color=LABEL2,
            ).pack(anchor="w", pady=(2, 0))

    # ── Events ────────────────────────────────────────────────────────────────

    def _on_resize(self, event):
        if event.widget is self:
            job = getattr(self, "_resize_job", None)
            if job:
                self.after_cancel(job)
            self._resize_job = self.after(100, self._render_hero)

    def _select_platform(self, platform: str):
        self.current_platform = platform
        for name, color in PLATFORMS:
            btn = self._tab_btns[name]
            if name == platform:
                btn.configure(text_color=color, border_color=color,
                              fg_color=_dim(color, 0.2))
            else:
                btn.configure(text_color=LABEL2, border_color=BORDER,
                              fg_color=SURF2)

    def _on_download(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        self.url_entry.delete(0, "end")
        self._empty.pack_forget()

        task = DownloadTask(url, self.current_platform)
        row  = DownloadRow(self.scroll, task, self)
        row.pack(fill="x", pady=(0, 8))

        threading.Thread(
            target=self._run_download, args=(task, row), daemon=True
        ).start()

    # ── Worker ────────────────────────────────────────────────────────────────

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
