"""Service d'exportation : rendu final en tâche de fond avec progression."""
import threading
import uuid

from fastapi import HTTPException

from app import config
from app.services import command_builder, import_service, processing_service

JOBS: dict = {}


def start_export(video_id: str, params) -> str:
    meta = import_service.VIDEOS.get(video_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Vidéo introuvable.")

    job_id = uuid.uuid4().hex
    out_dir = config.OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "output.mp4"

    JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "error": None,
        "path": str(out_path),
    }

    thread = threading.Thread(
        target=_run, args=(job_id, meta, params, out_path), daemon=True
    )
    thread.start()
    return job_id


def _run(job_id, meta, params, out_path):
    job = JOBS[job_id]
    try:
        job["status"] = "processing"
        out_w, out_h = command_builder.target_resolution(
            params, meta.width, meta.height
        )
        fc, map_audio = command_builder.build_filter_complex(
            params, meta.width, meta.height, out_w, out_h, meta.has_audio, meta.duration
        )

        total = command_builder.output_duration(meta.duration, params)

        cmd = processing_service.build_command(meta.path, str(out_path), fc, map_audio)

        def cb(p):
            job["progress"] = round(p, 1)

        processing_service.run(cmd, progress_cb=cb, total_seconds=total)
        job["progress"] = 100.0
        job["status"] = "done"
    except Exception as e:  # noqa: BLE001
        job["status"] = "error"
        job["error"] = str(e)
