import asyncio
import json
import os
import shutil
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

DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

jobs: dict[str, dict[str, Any]] = {}


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

    def hook(d: dict):
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
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            job["title"] = info.get("title", url)
            job["percent"] = 100.0
            job["status"] = "done"
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)


def _find_video(folder: Path) -> Path | None:
    for ext in (".mp4", ".webm", ".mkv", ".avi", ".mov"):
        matches = list(folder.glob(f"*{ext}"))
        if matches:
            return matches[0]
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
