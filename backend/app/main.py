"""Application FastAPI — ViralRemix Studio."""
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app import config
from app.models import (
    ExportRequest,
    ExportResponse,
    FrameRequest,
    JobStatus,
    PreviewRequest,
    UrlResponse,
    VideoMetadata,
)
from app.services import command_builder, processing_service
from app.services.export_service import JOBS, start_export
from app.services.import_service import VIDEOS, import_video
from app.temp_manager import cleanup_all

PREVIEWS: dict = {}


@asynccontextmanager
async def lifespan(app):
    cleanup_all()
    yield


app = FastAPI(title="ViralRemix Studio API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "app": "ViralRemix Studio API",
        "interface": "http://localhost:5173",
        "docs": "/docs",
    }


def _get_meta(video_id: str) -> VideoMetadata:
    meta = VIDEOS.get(video_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Vidéo introuvable.")
    return meta


def _even(n) -> int:
    return max(2, int(n) // 2 * 2)


def _preview_dims(out_w, out_h, max_dim):
    scale = max_dim / max(out_w, out_h)
    return _even(out_w * scale), _even(out_h * scale)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/import", response_model=VideoMetadata)
def import_video_endpoint(file: UploadFile = File(...)):
    return import_video(file)


@app.get("/api/video/{video_id}")
def get_video(video_id: str):
    meta = _get_meta(video_id)
    ext = "." + meta.path.rsplit(".", 1)[-1].lower()
    media = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}
    return FileResponse(meta.path, media_type=media.get(ext, "video/mp4"))


@app.post("/api/preview", response_model=UrlResponse)
def preview(req: PreviewRequest):
    meta = _get_meta(req.video_id)
    out_w, out_h = command_builder.target_resolution(req.params, meta.width, meta.height)
    pw, ph = _preview_dims(out_w, out_h, config.PREVIEW_MAX_DIM)
    fc, map_audio = command_builder.build_filter_complex(
        req.params, meta.width, meta.height, pw, ph, meta.has_audio, meta.duration
    )

    preview_id = uuid.uuid4().hex
    out_dir = config.PREVIEW_DIR / preview_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "preview.mp4"
    cmd = processing_service.build_command(
        meta.path,
        str(out_path),
        fc,
        map_audio,
        start=req.start,
        duration=req.duration,
        crf=28,
    )
    processing_service.run(cmd)
    PREVIEWS[preview_id] = str(out_path)
    return UrlResponse(url=f"/api/preview/{preview_id}")


@app.get("/api/preview/{preview_id}")
def get_preview(preview_id: str):
    path = PREVIEWS.get(preview_id)
    if not path:
        raise HTTPException(status_code=404, detail="Aperçu introuvable.")
    media_type = "image/jpeg" if path.endswith(".jpg") else "video/mp4"
    return FileResponse(path, media_type=media_type)


@app.post("/api/preview-frame", response_model=UrlResponse)
def preview_frame(req: FrameRequest):
    meta = _get_meta(req.video_id)
    out_w, out_h = command_builder.target_resolution(req.params, meta.width, meta.height)
    pw, ph = _preview_dims(out_w, out_h, config.FRAME_MAX_DIM)
    fc, _ = command_builder.build_filter_complex(
        req.params, meta.width, meta.height, pw, ph, False, meta.duration
    )

    fid = uuid.uuid4().hex
    out_dir = config.PREVIEW_DIR / fid
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "frame.jpg"
    cmd = processing_service.build_command(
        meta.path, str(out_path), fc, False, start=req.time, is_image=True
    )
    processing_service.run(cmd)
    PREVIEWS[fid] = str(out_path)
    return UrlResponse(url=f"/api/preview/{fid}")


@app.post("/api/export", response_model=ExportResponse)
def export(req: ExportRequest):
    job_id = start_export(req.video_id, req.params)
    return ExportResponse(job_id=job_id)


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Tâche introuvable.")
    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job.get("progress"),
        error=job.get("error"),
        download_url=f"/api/jobs/{job_id}/download" if job["status"] == "done" else None,
    )


@app.get("/api/jobs/{job_id}/download")
def download(job_id: str):
    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Export non disponible.")
    return FileResponse(
        job["path"], media_type="video/mp4", filename="viralremix_output.mp4"
    )
