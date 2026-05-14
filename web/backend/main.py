import asyncio
import base64
import json
import os
import shutil
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any

import yt_dlp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI()

_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS: list[str] = _raw_origins.split(",") if _raw_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}

DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "/tmp/vidget_downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Write YouTube cookies from env var to a temp file once at startup
_COOKIES_FILE: str | None = None
_cookies_b64 = os.getenv("YOUTUBE_COOKIES_B64", "").strip()
if _cookies_b64:
    try:
        _tmp = tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False)
        _tmp.write(base64.b64decode(_cookies_b64))
        _tmp.close()
        _COOKIES_FILE = _tmp.name
    except Exception:
        pass

jobs: dict[str, dict[str, Any]] = {}
cancel_flags: dict[str, threading.Event] = {}


class DownloadRequest(BaseModel):
    url: str
    platform: str


@app.post("/api/download")
async def start_download(req: DownloadRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "title": None,
        "percent": 0.0,
        "speed": "",
        "filepath": None,
        "error": None,
    }
    threading.Thread(
        target=_run_download, args=(job_id, req.url), daemon=True
    ).start()
    return {"job_id": job_id}


@app.get("/api/progress/{job_id}")
async def stream_progress(job_id: str):
    async def event_gen():
        while True:
            if job_id not in jobs:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
                return

            job = jobs[job_id]

            if job["status"] in ("pending", "downloading"):
                yield f"data: {json.dumps({'type': 'progress', 'percent': job['percent'], 'speed': job['speed'], 'title': job['title']})}\n\n"
            elif job["status"] == "done":
                yield f"data: {json.dumps({'type': 'done', 'title': job['title'], 'download_url': f'/api/file/{job_id}'})}\n\n"
                return
            elif job["status"] == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': job['error'] or 'Unknown error'})}\n\n"
                return

            await asyncio.sleep(0.4)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/cancel/{job_id}")
async def cancel_download(job_id: str):
    flag = cancel_flags.get(job_id)
    if flag:
        flag.set()
    if job_id in jobs:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = "Đã hủy tải xuống"
    return {"ok": True}


@app.get("/api/file/{job_id}")
async def download_file(job_id: str):
    filepath = _find_video(DOWNLOAD_DIR / job_id)
    if not filepath:
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(
        path=str(filepath),
        filename=filepath.name,
        media_type="application/octet-stream",
    )


# ── Download worker ────────────────────────────────────────────────────────

def _run_download(job_id: str, url: str):
    job = jobs[job_id]
    job["status"] = "downloading"
    out_dir = DOWNLOAD_DIR / job_id
    out_dir.mkdir(exist_ok=True)

    cancel = threading.Event()
    cancel_flags[job_id] = cancel

    def hook(d: dict):
        if cancel.is_set():
            raise Exception("Cancelled by user")
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            done = d.get("downloaded_bytes", 0)
            job["percent"] = round(done / total * 100, 1) if total else 0
            job["speed"] = d.get("_speed_str", "")
            if not job["title"]:
                stem = Path(d.get("filename", "")).stem
                if stem:
                    job["title"] = stem

    opts = {
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 10,
        "extractor_retries": 10,
        "fragment_retries": 10,
        "geo_bypass": True,
        "extractor_args": {
            "youtube": {
                # tv_embedded & mweb avoid PO token requirement; ios is fast
                "player_client": ["tv_embedded", "ios", "mweb", "web_creator"],
                "player_skip": ["webpage", "js"],
            },
        },
        "no_playlist": True,
    }

    # Use cookies: env var (base64) takes priority, then local cookies.txt
    if _COOKIES_FILE:
        opts["cookiefile"] = _COOKIES_FILE
    else:
        local_cookies = Path(__file__).parent / "cookies.txt"
        if local_cookies.exists():
            opts["cookiefile"] = str(local_cookies)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            job["title"] = info.get("title", url)
            job["percent"] = 100.0
            job["status"] = "done"
    except Exception as e:
        job["status"] = "error"
        err = str(e)
        if "Sign in" in err or "bot" in err.lower() or "429" in err:
            err = "YouTube đang chặn server. Hãy thử lại hoặc dùng link khác."
        elif "unavailable" in err.lower() or "private" in err.lower():
            err = "Video không khả dụng hoặc bị giới hạn."
        elif "ffmpeg" in err.lower():
            err = "ffmpeg không tìm thấy trên server."
        elif "Cancelled" in err:
            err = "Đã hủy tải xuống."
        else:
            err = f"Lỗi: {err[:120]}"
        job["error"] = err


def _find_video(folder: Path) -> Path | None:
    for ext in (".mp4", ".webm", ".mkv", ".avi", ".mov"):
        matches = list(folder.glob(f"*{ext}"))
        if matches:
            return matches[0]
    return None


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
