"""Service d'importation : upload, validation, analyse du fichier."""
import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app import config
from app.models import VideoMetadata
from app.services.ffmpeg_locator import get_ffmpeg_path
from app.services.probe import probe

VIDEOS: dict = {}


def import_video(file: UploadFile) -> VideoMetadata:
    filename = file.filename or "video"
    ext = Path(filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté ({ext}). Formats acceptés : MP4, MOV, WebM.",
        )

    video_id = uuid.uuid4().hex
    dest_dir = config.UPLOAD_DIR / video_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"input{ext}"

    size = 0
    try:
        with open(dest_path, "wb") as out:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > config.MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Fichier trop volumineux (max {config.MAX_UPLOAD_MB} Mo).",
                    )
                out.write(chunk)
    except Exception:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise

    if size == 0:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="Fichier vide.")

    try:
        ffmpeg = get_ffmpeg_path()
        info = probe(ffmpeg, str(dest_path))
    except RuntimeError as e:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

    if not info["has_video"]:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="Aucun flux vidéo détecté dans ce fichier.")

    meta = VideoMetadata(
        id=video_id,
        filename=filename,
        path=str(dest_path),
        width=info["width"],
        height=info["height"],
        duration=info["duration"],
        has_audio=info["has_audio"],
    )
    VIDEOS[video_id] = meta
    return meta
