"""VidGet Desktop — dark theme, compact single-line cards."""

import os
import platform
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

import customtkinter as ctk
import yt_dlp

# ── Palette ───────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG      = "#07070f"
CARD    = "#0e0e1c"
CARD2   = "#13132a"
BORDER  = "#1c1c32"
BORDER2 = "#272740"

VIOLET  = "#7c3aed"
VIO_LT  = "#a78bfa"
VIO_BG  = "#2d1b69"
VIO_H   = "#6d28d9"

TEXT    = "#f1f5f9"
TEXT2   = "#6b7280"
TEXT3   = "#374151"

OK      = "#10b981"
ERR     = "#f87171"
ERR_DK  = "#450a0a"
WARN    = "#fbbf24"
WARN_DK = "#451a03"

PLAT_C = {
    "YouTube":   "#FF4444",
    "TikTok":    "#00d4d4",
    "Facebook":  "#4090f7",
    "Instagram": "#e1306c",
    "Twitter/X": "#1d9bf0",
    "Khác":      "#a78bfa",
}

DLDIR = Path.home() / "Downloads" / "VidGet"
DLDIR.mkdir(parents=True, exist_ok=True)
FONT  = "Segoe UI"

def _ffmpeg_path() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
        for name in ("ffmpeg", "ffmpeg.exe"):
            p = os.path.join(base, name)
            if os.path.exists(p):
                return p
    return "ffmpeg"

def _open_folder(path: str):
    if platform.system() == "Darwin":
        subprocess.run(["open", path])
    elif platform.system() == "Windows":
        os.startfile(path)
    else:
        subprocess.run(["xdg-open", path])
_SPIN = ["◐", "◓", "◑", "◒"]
_BG_RGB = (7, 7, 15)

try:
    _PATH_SHORT = "~/" + str(DLDIR.relative_to(Path.home())).replace("\\", "/")
except ValueError:
    _PATH_SHORT = str(DLDIR)


# ── Colour helpers ────────────────────────────────────────────────────────────

def _hex(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _tint(h: str, a: float = 0.08) -> str:
    r, g, b = _hex(h)
    br, bg, bb = _BG_RGB
    return "#{:02x}{:02x}{:02x}".format(
        int(br+(r-br)*a), int(bg+(g-bg)*a), int(bb+(b-bb)*a))

def _shade(h: str, f: float) -> str:
    r, g, b = _hex(h)
    return "#{:02x}{:02x}{:02x}".format(
        min(255,int(r*f)), min(255,int(g*f)), min(255,int(b*f)))


# ── Utilities ─────────────────────────────────────────────────────────────────

def detect_platform(url: str) -> str:
    u = url.lower()
    if "youtube.com" in u or "youtu.be" in u: return "YouTube"
    if "tiktok.com" in u:                      return "TikTok"
    if "facebook.com" in u or "fb.watch" in u: return "Facebook"
    if "instagram.com" in u:                   return "Instagram"
    if "twitter.com" in u or "x.com" in u:    return "Twitter/X"
    return "Khác"

def fmt_size(b: int) -> str:
    if not b: return ""
    if b < 1_048_576: return f"{b/1024:.0f} KB"
    return f"{b/1_048_576:.1f} MB"


# ── Download task ─────────────────────────────────────────────────────────────

class DownloadTask:
    def __init__(self, url: str, platform: str):
        self.url = url; self.platform = platform
        self.title = "Đang lấy thông tin…"; self.status = "pending"
        self.cancel = threading.Event()
        self.filesize = 0; self.ext = ""


# ── Download card — compact single-line row (~34 px) ─────────────────────────

class DownloadCard(ctk.CTkFrame):
    """
    Layout (~34 px fixed height):
    ▌ [● YouTube]  Title text…         45% · 2.1 MB/s  [◑]  [■ Stop]
    ── 2 px progress bar ────────────────────────────────────────────
    """

    def __init__(self, parent, task: DownloadTask, app, **kw):
        col = PLAT_C.get(task.platform, VIOLET)
        super().__init__(parent,
                         fg_color=_tint(col, 0.06),
                         corner_radius=8,
                         border_width=1,
                         border_color=_tint(col, 0.22), **kw)
        self.configure(height=45)
        self.pack_propagate(False)
        self.task = task; self.app = app; self.color = col
        self._spin_idx = 0;  self._spinning = False
        self._dot_phase = 0; self._anim_on  = True
        self._anim_pos = 0.0; self._anim_dir = 0.04
        self._bar_color = col
        self._build()
        self._bar_tick(); self._anim_dots(); self._spin_start()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # 2 px progress bar — frame-based so height is guaranteed
        bar_wrap = ctk.CTkFrame(self, height=2, fg_color=BORDER, corner_radius=0)
        bar_wrap.pack(side="bottom", fill="x")
        bar_wrap.pack_propagate(False)
        self._bar_fill = ctk.CTkFrame(bar_wrap, fg_color=self.color, corner_radius=0)
        self._bar_fill.pack_propagate(False)
        self._bar_fill.place(x=0, y=0, relheight=1, relwidth=0)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="both", expand=True)

        # 3 px left accent stripe
        stripe = ctk.CTkFrame(row, width=3, fg_color=self.color, corner_radius=0)
        stripe.pack(side="left", fill="y")
        stripe.pack_propagate(False)

        # Platform pill — full name, auto-width
        pill = ctk.CTkFrame(row, height=22, corner_radius=6,
                            fg_color=_tint(self.color, 0.14),
                            border_width=1, border_color=_tint(self.color, 0.30))
        pill.pack(side="left", padx=(8, 0), pady=5)
        ctk.CTkLabel(pill, text="●",
            font=ctk.CTkFont(size=7), text_color=self.color,
            fg_color="transparent").pack(side="left", padx=(6, 0))
        ctk.CTkLabel(pill, text=self.task.platform,
            font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
            text_color=self.color, fg_color="transparent",
        ).pack(side="left", padx=(3, 7), pady=2)

        # ── Right block: icon + button (pack BEFORE title) ────────────────────
        rblock = ctk.CTkFrame(row, fg_color="transparent")
        rblock.pack(side="right", padx=8, pady=5)

        # Status icon
        self._icon = ctk.CTkLabel(rblock,
            text=_SPIN[0], width=22, height=22,
            font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
            text_color=VIO_LT, fg_color="transparent")
        self._icon.pack(side="left", padx=(0, 6))

        # Button slot — fixed size, buttons placed via place()
        self._slot = ctk.CTkFrame(rblock, fg_color="transparent", width=100, height=28)
        self._slot.pack(side="left")
        self._slot.pack_propagate(False)

        def _mkbtn(text, bg, fg, hover, cmd, brd=None):
            return ctk.CTkButton(self._slot, text=text,
                width=96, height=26, corner_radius=13,
                font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
                fg_color=bg, hover_color=hover, text_color=fg,
                border_width=1 if brd else 0,
                border_color=brd or bg, command=cmd)

        self._stop_btn  = _mkbtn("■  Stop",    ERR_DK, ERR,    "#601515", self._stop,
                                  brd=_tint(ERR, 0.28))
        self._open_btn  = _mkbtn("📁  Mở",     VIOLET, "white", VIO_H,    self._open)
        self._retry_btn = _mkbtn("↺  Thử lại", WARN_DK, WARN,  "#5c2a08", self._retry,
                                  brd=_tint(WARN, 0.28))
        self._stop_btn.place(relx=0.5, rely=0.5, anchor="center")

        # Status text (right of title, fixed width — pack BEFORE title)
        self._status = ctk.CTkLabel(row,
            text="Đang chuẩn bị", width=160, anchor="e",
            font=ctk.CTkFont(family=FONT, size=13),
            text_color=TEXT3, fg_color="transparent")
        self._status.pack(side="right", padx=(0, 6), pady=5)

        # Title — fills remaining space
        self._title = ctk.CTkLabel(row,
            text=self.task.title, anchor="w",
            font=ctk.CTkFont(family=FONT, size=14, weight="bold"),
            text_color=TEXT, fg_color="transparent")
        self._title.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=5)

    # ── Bar helper ────────────────────────────────────────────────────────────

    def _set_bar(self, val: float, color: str = None):
        c = color or self._bar_color
        if c != self._bar_color:
            self._bar_fill.configure(fg_color=c)
            self._bar_color = c
        self._bar_fill.place(relwidth=max(0.0, min(1.0, val)), relheight=1)

    # ── Animations ────────────────────────────────────────────────────────────

    def _bar_tick(self):
        if not self._anim_on: return
        self._anim_pos += self._anim_dir
        if   self._anim_pos >= 1.0: self._anim_pos = 1.0; self._anim_dir = -0.04
        elif self._anim_pos <= 0.0: self._anim_pos = 0.0; self._anim_dir =  0.04
        try:
            self._set_bar(self._anim_pos)
            self.after(25, self._bar_tick)
        except Exception: pass

    def _anim_dots(self):
        if not self._anim_on: return
        phases = ["Đang chuẩn bị", "Đang chuẩn bị ·",
                  "Đang chuẩn bị ··", "Đang chuẩn bị ···"]
        self._dot_phase = (self._dot_phase + 1) % 4
        try:
            self._status.configure(text=phases[self._dot_phase])
            self.after(360, self._anim_dots)
        except Exception: pass

    def _spin_start(self):
        self._spinning = True; self._spin_step()

    def _spin_step(self):
        if not self._spinning: return
        self._spin_idx = (self._spin_idx + 1) % 4
        try:
            self._icon.configure(text=_SPIN[self._spin_idx])
            self.after(110, self._spin_step)
        except Exception: pass

    # ── State updates ─────────────────────────────────────────────────────────

    def update_title(self, t: str):
        self._title.configure(text=(t[:55]+"…") if len(t) > 55 else t)

    def update_progress(self, pct: float, speed: str = ""):
        self._anim_on = False
        self._set_bar(pct / 100)
        spd = f" · {speed}" if speed else ""
        self._status.configure(text=f"{pct:.0f}%{spd}", text_color=TEXT2)

    def mark_success(self, filesize: int = 0, ext: str = ""):
        self._anim_on = self._spinning = False
        self._set_bar(1.0, OK)
        parts = [p for p in [ext.upper() if ext else "", fmt_size(filesize)] if p]
        self._status.configure(
            text=" · ".join(parts) if parts else "Hoàn thành",
            text_color=OK)
        self._icon.configure(text="✓", text_color=OK,
            font=ctk.CTkFont(family=FONT, size=16, weight="bold"))
        self._stop_btn.place_forget()
        self._open_btn.place(relx=0.5, rely=0.5, anchor="center")

    def mark_failed(self, msg: str = ""):
        self._anim_on = self._spinning = False
        self._set_bar(0.0, ERR)
        self._status.configure(
            text=(msg[:18]+"…") if len(msg) > 18 else (msg or "Lỗi"),
            text_color=ERR)
        self._icon.configure(text="✗", text_color=ERR,
            font=ctk.CTkFont(family=FONT, size=16, weight="bold"))
        self._stop_btn.place_forget()
        self._retry_btn.place(relx=0.5, rely=0.5, anchor="center")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _stop(self):
        self._anim_on = self._spinning = False
        self.task.cancel.set()
        self._set_bar(0.0, TEXT3)
        self._status.configure(text="Đã hủy", text_color=TEXT3)
        self._icon.configure(text="—", text_color=TEXT3,
            font=ctk.CTkFont(family=FONT, size=14, weight="bold"))
        self._stop_btn.place_forget()

    def _open(self): _open_folder(str(DLDIR))

    def _retry(self):
        self._anim_on = self._spinning = True
        self._anim_pos = 0.0; self._anim_dir = 0.04; self._dot_phase = 0
        self.task.cancel.clear(); self.task.status = "pending"
        self.task.title = "Đang lấy thông tin…"
        self._set_bar(0.0, self.color)
        self._title.configure(text="Đang lấy thông tin…", text_color=TEXT)
        self._status.configure(text="Đang chuẩn bị", text_color=TEXT3)
        self._icon.configure(text=_SPIN[0], text_color=VIO_LT,
            font=ctk.CTkFont(family=FONT, size=14, weight="bold"))
        self._retry_btn.place_forget()
        self._stop_btn.place(relx=0.5, rely=0.5, anchor="center")
        self._bar_tick(); self._anim_dots(); self._spin_step()
        threading.Thread(
            target=self.app._run, args=(self.task, self), daemon=True).start()


# ── Main window ───────────────────────────────────────────────────────────────

class VidGetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VidGet")
        self.geometry("936x680")
        self.minsize(744, 520)
        self.configure(fg_color=BG)
        self._build()

    def _build(self):
        root = ctk.CTkFrame(self, fg_color=BG)
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=1)

        self._build_topbar(root)  # row 0
        self._build_hero(root)    # row 1
        self._build_list(root)    # row 2
        self._build_usp(root)     # row 3

    # ── Top bar: logo (left) + folder path (right) ────────────────────────────

    def _build_topbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=36, pady=(24, 0))
        bar.grid_columnconfigure(1, weight=1)

        # ── Logo canvas: pixel-tight "by Toangomo" below VidGet ──────────────────
        f40  = tkfont.Font(family=FONT, size=40, weight="bold")
        f12  = tkfont.Font(family=FONT, size=12)
        vid_w = f40.measure("Vid")
        asc   = f40.metrics("ascent")
        desc  = f40.metrics("descent")
        sm_lh = f12.metrics("linespace")
        cv_h  = asc + desc + 3 + sm_lh

        logo_cv = tk.Canvas(bar, bg=BG, bd=0, highlightthickness=0,
                            width=vid_w + f40.measure("Get"), height=cv_h)
        logo_cv.grid(row=0, column=0, sticky="w")
        logo_cv.create_text(0,     0,            text="Vid",         font=f40, fill=TEXT,   anchor="nw")
        logo_cv.create_text(vid_w, 0,            text="Get",         font=f40, fill=VIO_LT, anchor="nw")
        logo_cv.create_text(2,     asc+desc+3,   text="by Toangomo", font=f12, fill=TEXT3,  anchor="nw")

        # ── Folder path (right, vertically centred in row) ────────────────────
        fbox = ctk.CTkFrame(bar, fg_color=CARD, corner_radius=8,
                            border_width=1, border_color=BORDER)
        fbox.grid(row=0, column=2, sticky="e")

        ctk.CTkLabel(fbox, text="📁",
            font=ctk.CTkFont(size=13), fg_color="transparent",
            text_color=TEXT3).pack(side="left", padx=(10, 0), pady=8)
        ctk.CTkLabel(fbox, text=_PATH_SHORT,
            font=ctk.CTkFont(family=FONT, size=12), text_color=TEXT2,
            fg_color="transparent").pack(side="left", padx=(5, 0), pady=8)
        ctk.CTkButton(fbox, text="Mở →",
            width=58, height=24, corner_radius=12,
            font=ctk.CTkFont(family=FONT, size=11, weight="bold"),
            fg_color=VIO_BG, hover_color=_shade(VIO_BG, 1.25),
            text_color=VIO_LT, border_width=1,
            border_color=_tint(VIOLET, 0.40),
            command=lambda: _open_folder(str(DLDIR)),
        ).pack(side="left", padx=(8, 10), pady=8)

    # ── Hero: pill badge + heading + subtitle + input ─────────────────────────

    def _build_hero(self, parent):
        hero = ctk.CTkFrame(parent, fg_color="transparent")
        hero.grid(row=1, column=0, sticky="ew", padx=52, pady=(28, 0))
        hero.grid_columnconfigure(0, weight=1)

        # Badge pill
        pw = ctk.CTkFrame(hero, fg_color="transparent")
        pw.grid(row=0, column=0)
        pill = ctk.CTkFrame(pw, fg_color=VIO_BG, corner_radius=20,
                            border_width=1, border_color=_tint(VIOLET, 0.45))
        pill.pack()
        ctk.CTkLabel(pill,
            text="✦  Miễn phí · Không đăng ký · Không quảng cáo",
            font=ctk.CTkFont(family=FONT, size=12),
            text_color=VIO_LT, fg_color="transparent",
        ).pack(padx=14, pady=6)

        # Heading — two-colour: white + violet
        hw = ctk.CTkFrame(hero, fg_color="transparent")
        hw.grid(row=1, column=0, pady=(12, 0))
        ctk.CTkLabel(hw, text="Tải video từ ",
            font=ctk.CTkFont(family=FONT, size=36, weight="bold"),
            text_color=TEXT, fg_color="transparent").pack(side="left")
        ctk.CTkLabel(hw, text="mọi nền tảng",
            font=ctk.CTkFont(family=FONT, size=36, weight="bold"),
            text_color=VIO_LT, fg_color="transparent").pack(side="left")

        # Subtitle
        ctk.CTkLabel(hero, text="Dán link — nhấn tải — xong.",
            font=ctk.CTkFont(family=FONT, size=15),
            text_color=TEXT2, fg_color="transparent",
        ).grid(row=2, column=0, pady=(7, 0))

        # Input card
        icard = ctk.CTkFrame(hero, fg_color=CARD2, corner_radius=14,
                             border_width=1, border_color=BORDER2)
        icard.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        icard.grid_columnconfigure(0, weight=1)

        irow = ctk.CTkFrame(icard, fg_color="transparent")
        irow.pack(fill="x", padx=8, pady=8)
        irow.grid_columnconfigure(0, weight=1)

        self._entry = ctk.CTkEntry(irow,
            placeholder_text="Dán link video vào đây…",
            height=44, border_width=0, fg_color="transparent",
            font=ctk.CTkFont(family=FONT, size=15),
            text_color=TEXT, placeholder_text_color=TEXT3)
        self._entry.grid(row=0, column=0, sticky="ew", padx=(10, 8))
        self._entry.bind("<Return>", lambda _: self._download())

        ctk.CTkButton(irow,
            text="↓  Tải xuống",
            width=148, height=44, corner_radius=22,
            font=ctk.CTkFont(family=FONT, size=15, weight="bold"),
            fg_color=VIOLET, hover_color=VIO_H, text_color="white",
            command=self._download,
        ).grid(row=0, column=1, padx=(0, 2))

    # ── Results list ──────────────────────────────────────────────────────────

    def _build_list(self, parent):
        self._scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=BORDER2,
            scrollbar_button_hover_color=BORDER2)
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=52, pady=(14, 0))

        self._empty = ctk.CTkFrame(self._scroll, fg_color=CARD,
                                   corner_radius=10, border_width=1, border_color=BORDER)
        self._empty.pack(fill="x")
        ctk.CTkLabel(self._empty, text="🎬",
            font=ctk.CTkFont(size=28), fg_color="transparent",
            text_color=TEXT3).pack(pady=(20, 4))
        ctk.CTkLabel(self._empty, text="Chưa có video nào",
            font=ctk.CTkFont(family=FONT, size=15, weight="bold"),
            fg_color="transparent", text_color=TEXT2).pack()
        ctk.CTkLabel(self._empty,
            text="Dán link vào ô trên và nhấn Tải xuống để bắt đầu",
            font=ctk.CTkFont(family=FONT, size=12),
            fg_color="transparent", text_color=TEXT3).pack(pady=(3, 20))

    # ── USP footer strip ──────────────────────────────────────────────────────

    def _build_usp(self, parent):
        usp = ctk.CTkFrame(parent, fg_color="transparent")
        usp.grid(row=3, column=0, pady=(10, 18))
        inner = ctk.CTkFrame(usp, fg_color="transparent")
        inner.pack()
        items = ["⚡  Tốc độ cao", "🛡  Riêng tư & Bảo mật", "✅  Miễn phí hoàn toàn"]
        for i, txt in enumerate(items):
            ctk.CTkLabel(inner, text=txt,
                font=ctk.CTkFont(family=FONT, size=16), text_color=TEXT2,
                fg_color="transparent").grid(row=0, column=i*2, padx=14)
            if i < 2:
                ctk.CTkLabel(inner, text="·", font=ctk.CTkFont(size=18),
                    text_color=BORDER2, fg_color="transparent").grid(row=0, column=i*2+1)

    # ── Download logic ────────────────────────────────────────────────────────

    def _download(self):
        url = self._entry.get().strip()
        if not url: return
        self._entry.delete(0, "end")
        self._empty.pack_forget()
        task = DownloadTask(url, detect_platform(url))
        card = DownloadCard(self._scroll, task, self)
        card.pack(fill="x", pady=(0, 5))
        threading.Thread(target=self._run, args=(task, card), daemon=True).start()

    def _run(self, task: DownloadTask, card: DownloadCard):
        def hook(d):
            if task.cancel.is_set(): raise Exception("Cancelled")
            if d["status"] != "downloading": return
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            done  = d.get("downloaded_bytes", 0)
            pct   = done / total * 100 if total else 0
            speed = d.get("_speed_str", "")
            if task.title == "Đang lấy thông tin…":
                stem = Path(d.get("filename", "")).stem
                if stem:
                    task.title = stem
                    self.after(0, card.update_title, stem)
            self.after(0, card.update_progress, pct, speed)

        opts = {
            "outtmpl": str(DLDIR / "%(title)s.%(ext)s"),
            "format":  "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "progress_hooks": [hook],
            "quiet": True, "no_warnings": True,
            "socket_timeout": 30, "retries": 5,
            "fragment_retries": 10,
            "ffmpeg_location": _ffmpeg_path(),
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info      = ydl.extract_info(task.url, download=True)
                task.title    = info.get("title", task.url)
                task.filesize = info.get("filesize") or info.get("filesize_approx", 0)
                task.ext      = info.get("ext", "mp4")
                task.status   = "done"
                self.after(0, card.update_title, task.title)
                self.after(0, card.mark_success, task.filesize, task.ext)
        except Exception as e:
            err = str(e)
            if "Cancelled" in err: return
            task.status = "failed"
            if "Sign in" in err or "bot" in err.lower():
                err = "YouTube đang bị chặn, thử lại sau."
            elif "unavailable" in err.lower() or "private" in err.lower():
                err = "Video không khả dụng hoặc bị giới hạn."
            elif "ffmpeg" in err.lower():
                err = "Không tìm thấy ffmpeg."
            self.after(0, card.mark_failed, err[:60])


if __name__ == "__main__":
    VidGetApp().mainloop()
