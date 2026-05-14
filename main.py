"""VidGet — Raycast/Linear/Terminal aesthetic."""

import os
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageTk
import yt_dlp

# ── Palette ───────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG     = "#0d0d14"   # near-black with blue undertone
S1     = "#13131e"   # surface 1
S2     = "#191926"   # surface 2
BORDER = "#22223a"   # border
LINE   = "#1a1a2a"   # separator line
ACC    = "#7c5cfc"   # electric violet
ACC2   = "#00d4ff"   # cyan
TEXT   = "#f0f0ff"   # primary
DIM    = "#8888a8"   # secondary
MUTE   = "#303050"   # muted / disabled
OK     = "#00e676"   # success neon green
ERR    = "#ff1744"   # error neon red
WARN   = "#ffc400"   # warning amber

PLAT = [
    ("YouTube",   "#ff1744", "YT"),
    ("TikTok",    "#00e5ff", "TK"),
    ("Facebook",  "#2979ff", "FB"),
    ("Instagram", "#f50057", "IG"),
    ("Twitter/X", "#00b0ff",  "X"),
    ("Khác",      "#aa00ff", "···"),
]
PCOLOR = {name: color for name, color, _ in PLAT}
PSHORT = {name: short for name, color, short in PLAT}

DLDIR = Path.home() / "Downloads" / "VidGet"
DLDIR.mkdir(parents=True, exist_ok=True)


# ── PIL helpers ───────────────────────────────────────────────────────────────

def _h(s: str):
    s = s.lstrip("#")
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))

def _dim_hex(h: str, f: float = 0.18) -> str:
    r, g, b = _h(h)
    return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"


def header_canvas_bg(w: int, h: int) -> ImageTk.PhotoImage:
    """Flat dark with a 1-px electric accent line at the bottom."""
    img = Image.new("RGB", (w, h), _h(BG))
    # Faint violet gradient only in top-right corner
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse([w - 320, -120, w + 60, h + 60], fill=(124, 92, 252, 22))
    glow = glow.filter(ImageFilter.GaussianBlur(55))
    img.paste(glow, mask=glow.split()[3])
    # Bottom accent line: violet → cyan gradient
    ld = ImageDraw.Draw(img)
    for x in range(w):
        t = x / max(w - 1, 1)
        c = _lerp(_h(ACC), _h(ACC2), t)
        ld.point((x, h - 1), fill=c)
    return ImageTk.PhotoImage(img)


def make_logo_icon(sz: int = 44) -> ImageTk.PhotoImage:
    """Square icon: gradient bg, bold ▼ mark."""
    pad = 6
    tot = sz + pad * 2
    base = Image.new("RGB", (sz, sz))
    d = ImageDraw.Draw(base)
    for y in range(sz):
        t = y / sz
        base.paste(Image.new("RGB", (sz, 1), _lerp(_h("#9b6bff"), _h("#5b30d6"), t)), (0, y))

    mask = Image.new("L", (sz, sz), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sz-1, sz-1], radius=sz//5, fill=255)

    icon = Image.new("RGBA", (tot, tot), (0, 0, 0, 0))
    icon.paste(base.convert("RGBA"), (pad, pad), mask)

    # Glow
    gl = icon.filter(ImageFilter.GaussianBlur(pad))
    r, g, b, a = gl.split()
    gl = Image.merge("RGBA", (r, g, b, a.point(lambda x: int(x * 0.5))))
    out = Image.new("RGBA", (tot, tot), (0, 0, 0, 0))
    out.paste(gl, mask=gl.split()[3])
    out.paste(icon, mask=icon.split()[3])

    # V lettermark
    fd = ImageDraw.Draw(out)
    cx, cy = tot // 2, tot // 2 + 1
    arm = sz * 0.2
    lw = max(3, sz // 8)
    fd.line([(cx - arm, cy - arm * 0.8), (cx, cy + arm * 0.65)], fill=(255,255,255,240), width=lw)
    fd.line([(cx + arm, cy - arm * 0.8), (cx, cy + arm * 0.65)], fill=(255,255,255,240), width=lw)
    return ImageTk.PhotoImage(out)


def make_btn_glow(w: int, h: int, color: str) -> ImageTk.PhotoImage:
    pad = 22
    img = Image.new("RGBA", (w+pad*2, h+pad*2), (0,0,0,0))
    ImageDraw.Draw(img).rounded_rectangle(
        [pad, pad, w+pad, h+pad], radius=10, fill=(*_h(color), 110))
    return ImageTk.PhotoImage(img.filter(ImageFilter.GaussianBlur(16)))


# ── Download task ─────────────────────────────────────────────────────────────

class DownloadTask:
    def __init__(self, url: str, platform: str):
        self.url = url; self.platform = platform
        self.title = "Đang lấy thông tin…"; self.status = "pending"
        self.cancel = threading.Event()


# ── Download row (flat list style) ───────────────────────────────────────────

class DownloadRow(tk.Frame):
    """A flat list row — no card border, just a bottom separator line."""

    def __init__(self, parent, task: DownloadTask, app, **kw):
        super().__init__(parent, bg=BG, **kw)
        self.task  = task
        self.app   = app
        self.color = PCOLOR.get(task.platform, ACC)
        self._pulse_job = None
        self._pulse_val = 0
        self._build()

    def _build(self):
        self.grid_columnconfigure(2, weight=1)

        # ── Status dot (animated canvas) ──
        self._dot_cv = tk.Canvas(self, width=14, height=14,
                                  bg=BG, highlightthickness=0)
        self._dot_cv.grid(row=0, column=0, padx=(14, 0), pady=14)
        self._dot = self._dot_cv.create_oval(2, 2, 12, 12,
                                              fill=MUTE, outline="")
        self._start_pulse()

        # ── Platform tag ──
        short = PSHORT.get(self.task.platform, "?")
        tag = tk.Label(self, text=short,
            bg=_dim_hex(self.color, 0.2), fg=self.color,
            font=("Consolas", 9, "bold"), padx=6, pady=2,
            relief="flat")
        tag.grid(row=0, column=1, padx=(10, 0), pady=(15, 14), sticky="n")

        # ── Title + progress ──
        center = tk.Frame(self, bg=BG)
        center.grid(row=0, column=2, padx=(10, 8), pady=(12, 10), sticky="ew")
        center.grid_columnconfigure(0, weight=1)

        self._title = tk.Label(center, text=self.task.title,
            bg=BG, fg=TEXT, font=("Segoe UI", 12, "bold"),
            anchor="w", justify="left")
        self._title.grid(row=0, column=0, columnspan=2, sticky="ew")

        self._bar_frame = tk.Frame(center, bg=BG)
        self._bar_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        self._bar_bg = tk.Frame(self._bar_frame, bg=MUTE, height=2)
        self._bar_bg.pack(fill="x")

        self._bar_fill = tk.Frame(self._bar_bg, bg=self.color, height=2, width=0)
        self._bar_fill.place(x=0, y=0, relheight=1)

        self._bar_bg.bind("<Configure>", self._sync_bar)
        self._bar_pct = 0.0

        self._sub = tk.Label(center, text="Đang chuẩn bị…",
            bg=BG, fg=DIM, font=("Consolas", 10), anchor="w")
        self._sub.grid(row=2, column=0, sticky="ew", pady=(3, 0))

        # ── Action buttons ──
        self._btn_area = tk.Frame(self, bg=BG)
        self._btn_area.grid(row=0, column=3, padx=(0, 14), pady=(14, 14), sticky="n")

        self._stop_btn  = self._mk_btn("✕  Stop", ERR,    self._stop)
        self._open_btn  = self._mk_btn("⌂  Open", ACC2,   self._open)
        self._retry_btn = self._mk_btn("↺  Retry", WARN,  self._retry)

        self._stop_btn.pack()

        # ── Bottom separator ──
        tk.Frame(self, bg=LINE, height=1).grid(
            row=1, column=0, columnspan=4, sticky="ew")

    def _mk_btn(self, text, color, cmd):
        return tk.Button(self._btn_area, text=text, bg=_dim_hex(color, 0.16),
            fg=color, font=("Segoe UI", 10), relief="flat", padx=10, pady=4,
            activebackground=_dim_hex(color, 0.28), activeforeground=color,
            cursor="hand2", command=cmd, bd=0)

    def _sync_bar(self, e=None):
        w = self._bar_bg.winfo_width()
        self._bar_fill.place(x=0, y=0, relheight=1,
                              width=max(0, int(w * self._bar_pct)))

    # ── Pulse animation ───────────────────────────────────────────────────────

    def _start_pulse(self):
        self._pulse_val = (self._pulse_val + 1) % 20
        bright = self._pulse_val < 10
        if self.task.status in ("pending", "downloading"):
            color = self.color if bright else _dim_hex(self.color, 0.5)
            self._dot_cv.itemconfig(self._dot, fill=color)
            self._pulse_job = self.after(90, self._start_pulse)

    def _stop_pulse(self):
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None

    # ── State updates ─────────────────────────────────────────────────────────

    def update_title(self, t: str):
        self._title.config(text=(t[:68]+"…") if len(t)>68 else t)

    def update_progress(self, pct: float, speed: str = ""):
        self._bar_pct = pct / 100
        self._sync_bar()
        spd = f"  {speed}" if speed else ""
        self._sub.config(text=f"{pct:05.1f}%{spd}", fg=DIM)

    def mark_success(self):
        self._stop_pulse()
        self._dot_cv.itemconfig(self._dot, fill=OK)
        self._bar_pct = 1.0; self._sync_bar()
        self._bar_fill.config(bg=OK)
        self._sub.config(text="Done", fg=OK)
        self._stop_btn.pack_forget()
        self._open_btn.pack()

    def mark_failed(self, msg: str = ""):
        self._stop_pulse()
        self._dot_cv.itemconfig(self._dot, fill=ERR)
        self._bar_fill.config(bg=ERR)
        self._sub.config(text=msg or "Failed", fg=ERR)
        self._stop_btn.pack_forget()
        self._retry_btn.pack()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _stop(self):
        self.task.cancel.set()
        self._stop_pulse()
        self._dot_cv.itemconfig(self._dot, fill=MUTE)
        self._sub.config(text="Cancelled", fg=DIM)
        self._stop_btn.pack_forget()

    def _open(self): os.startfile(str(DLDIR))

    def _retry(self):
        self.task.cancel.clear(); self.task.status = "pending"
        self._bar_pct = 0.0; self._sync_bar()
        self._bar_fill.config(bg=self.color)
        self._sub.config(text="Đang chuẩn bị…", fg=DIM)
        self._dot_cv.itemconfig(self._dot, fill=MUTE)
        self._retry_btn.pack_forget()
        self._stop_btn.pack()
        self._start_pulse()
        threading.Thread(target=self.app._run_download,
                         args=(self.task, self), daemon=True).start()


# ── App ───────────────────────────────────────────────────────────────────────

class VidGetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VidGet")
        self.geometry("980x720")
        self.minsize(780, 540)
        self.configure(fg_color=BG)
        self.current_platform = "YouTube"
        self._tab_btns: dict[str, tk.Button] = {}
        self._hdr_photo = self._icon_photo = self._glow_photo = None
        self._build()
        self.bind("<Configure>", self._on_resize)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self._build_header()
        self._build_platform()
        self._build_input()
        self._build_list()
        self._build_usp()

    # Header ──────────────────────────────────────────────────────────────────

    def _build_header(self):
        self._hdr_cv = tk.Canvas(self, height=76, bg=BG, highlightthickness=0)
        self._hdr_cv.pack(fill="x")
        self.after(50, self._render_header)

    def _render_header(self, _=None):
        cv = self._hdr_cv
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 4: self.after(60, self._render_header); return

        cv.delete("all")
        self._hdr_photo = header_canvas_bg(w, h)
        cv.create_image(0, 0, anchor="nw", image=self._hdr_photo)

        # Icon
        self._icon_photo = make_logo_icon(44)
        cv.create_image(30, h//2, anchor="center", image=self._icon_photo)

        # "VIDGET" in tight letter-spaced style
        cv.create_text(58, h//2 - 10, text="VID", anchor="w",
            fill=TEXT, font=("Segoe UI", 22, "bold"))
        cv.create_text(101, h//2 - 10, text="GET", anchor="w",
            fill=ACC, font=("Segoe UI", 22, "bold"))

        cv.create_text(58, h//2 + 14, text="Video Downloader  ·  v2.0",
            anchor="w", fill=MUTE, font=("Consolas", 9))

        # Right: save path
        cv.create_text(w - 14, h//2, anchor="e",
            text=f"⌂  {DLDIR}",
            fill=MUTE, font=("Consolas", 9))

    # Platform chips ──────────────────────────────────────────────────────────

    def _build_platform(self):
        bar = tk.Frame(self, bg=S1, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="PLATFORM", bg=S1, fg=MUTE,
            font=("Consolas", 9, "bold")).pack(side="left", padx=(16,12), pady=12)

        # thin vertical rule
        tk.Frame(bar, bg=LINE, width=1).pack(side="left", fill="y", pady=8)

        for name, color, short in PLAT:
            btn = tk.Button(bar, text=short,
                bg=S1, fg=DIM,
                font=("Consolas", 10, "bold"),
                relief="flat", padx=12, pady=6,
                activebackground=_dim_hex(color, 0.22),
                activeforeground=color,
                cursor="hand2", bd=0,
                command=lambda p=name: self._select(p))
            btn.pack(side="left", padx=1)
            self._tab_btns[name] = btn

        self._select("YouTube")

        # Bottom border of bar
        tk.Frame(self, bg=LINE, height=1).pack(fill="x")

    # Input ───────────────────────────────────────────────────────────────────

    def _build_input(self):
        wrap = tk.Frame(self, bg=S1, height=58)
        wrap.pack(fill="x")
        wrap.pack_propagate(False)

        # Prompt prefix
        tk.Label(wrap, text=">_", bg=S1, fg=ACC,
            font=("Consolas", 13, "bold")).pack(side="left", padx=(16,0))

        self._entry = ctk.CTkEntry(
            wrap,
            placeholder_text="Dán link video vào đây…",
            height=36, border_width=1, border_color=BORDER,
            fg_color=S2, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT, placeholder_text_color=MUTE,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        self._entry.bind("<Return>", lambda _: self._download())

        # Glow download button
        BW, BH, pad = 138, 36, 16
        self._glow_cv = tk.Canvas(wrap, width=BW+pad*2, height=BH+pad*2,
                                   bg=S1, highlightthickness=0)
        self._glow_cv.pack(side="right", padx=(0, 12), pady=10)
        self._glow_photo = make_btn_glow(BW, BH, ACC)
        self._glow_cv.create_image((BW+pad*2)//2, (BH+pad*2)//2, image=self._glow_photo)

        dl = ctk.CTkButton(
            self._glow_cv, text="DOWNLOAD  ▶",
            width=BW, height=BH, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=ACC, hover_color="#6d45e0", text_color=TEXT,
            command=self._download,
        )
        self._glow_cv.create_window((BW+pad*2)//2, (BH+pad*2)//2, window=dl)

        tk.Frame(self, bg=LINE, height=1).pack(fill="x")

    # List ────────────────────────────────────────────────────────────────────

    def _build_list(self):
        # Column header
        hdr = tk.Frame(self, bg=S1, height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        col_kw = dict(bg=S1, fg=MUTE, font=("Consolas", 8, "bold"), anchor="w")
        tk.Label(hdr, text="  ●  PLAT   TITLE", **col_kw).pack(side="left", padx=(12,0))
        tk.Label(hdr, text="PROGRESS  ·  SPEED", **col_kw).pack(side="right", padx=(0, 130))
        tk.Frame(self, bg=LINE, height=1).pack(fill="x")

        # Scrollable frame (plain tk for flat-list rows)
        self._list_outer = ctk.CTkScrollableFrame(
            self, fg_color=BG,
            scrollbar_button_color=S2, scrollbar_button_hover_color=BORDER)
        self._list_outer.pack(fill="both", expand=True)

        # Empty state
        self._empty = tk.Frame(self._list_outer, bg=BG)
        self._empty.pack(expand=True, pady=50)
        tk.Label(self._empty, text="No downloads yet",
            bg=BG, fg=MUTE, font=("Consolas", 13, "bold")).pack()
        tk.Label(self._empty, text="paste a link above and press DOWNLOAD",
            bg=BG, fg=MUTE, font=("Consolas", 10)).pack(pady=(6,0))

    # USP bottom bar ──────────────────────────────────────────────────────────

    def _build_usp(self):
        tk.Frame(self, bg=LINE, height=1).pack(fill="x")

        bar = tk.Frame(self, bg=S1, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        items = [
            ("⚡", "FAST", "Tốc độ tối đa"),
            ("🛡", "PRIVATE", "Không lưu link"),
            ("🌐", "500+", "Nền tảng hỗ trợ"),
        ]
        for i, (icon, label, desc) in enumerate(items):
            if i > 0:
                tk.Frame(bar, bg=LINE, width=1).pack(side="left", fill="y", pady=10)
            cell = tk.Frame(bar, bg=S1)
            cell.pack(side="left", expand=True, fill="both")
            tk.Label(cell, text=f"{icon}  {label}",
                bg=S1, fg=ACC, font=("Consolas", 10, "bold")).pack(pady=(7,1))
            tk.Label(cell, text=desc,
                bg=S1, fg=DIM, font=("Consolas", 8)).pack()

    # ── Events ────────────────────────────────────────────────────────────────

    def _on_resize(self, e):
        if e.widget is self:
            j = getattr(self, "_rjob", None)
            if j: self.after_cancel(j)
            self._rjob = self.after(100, self._render_header)

    def _select(self, name: str):
        self.current_platform = name
        for n, color, short in PLAT:
            btn = self._tab_btns[n]
            if n == name:
                btn.config(bg=_dim_hex(color, 0.22), fg=color)
            else:
                btn.config(bg=S1, fg=DIM)

    def _download(self):
        url = self._entry.get().strip()
        if not url: return
        self._entry.delete(0, "end")
        self._empty.pack_forget()

        task = DownloadTask(url, self.current_platform)
        row  = DownloadRow(self._list_outer, task, self)
        row.pack(fill="x")

        threading.Thread(target=self._run_download,
                         args=(task, row), daemon=True).start()

    # ── Worker ────────────────────────────────────────────────────────────────

    def _run_download(self, task: DownloadTask, row: DownloadRow):
        def hook(d):
            if task.cancel.is_set(): raise Exception("Cancelled")
            if d["status"] != "downloading": return
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            done  = d.get("downloaded_bytes", 0)
            pct   = done / total * 100 if total else 0
            speed = d.get("_speed_str", "")
            if task.title == "Đang lấy thông tin…":
                stem = Path(d.get("filename","")).stem
                if stem:
                    task.title = stem
                    self.after(0, row.update_title, stem)
            self.after(0, row.update_progress, pct, speed)

        opts = {
            "outtmpl": str(DLDIR / "%(title)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "progress_hooks": [hook],
            "quiet": True, "no_warnings": True,
            "socket_timeout": 30, "retries": 5,
            "extractor_args": {
                "youtube": {"player_client": ["ios","android","tv_embedded"]},
            },
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(task.url, download=True)
                task.title = info.get("title", task.url)
                task.status = "done"
                self.after(0, row.update_title, task.title)
                self.after(0, row.mark_success)
        except Exception as e:
            err = str(e)
            if "Cancelled" in err: return
            task.status = "failed"
            if "Sign in" in err or "bot" in err.lower(): err = "YouTube đang chặn. Thử link khác."
            elif "unavailable" in err.lower():           err = "Video không khả dụng."
            self.after(0, row.mark_failed, err[:72])


if __name__ == "__main__":
    VidGetApp().mainloop()
