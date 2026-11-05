"""Configuration partagée du backend."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp"
UPLOAD_DIR = TEMP_DIR / "uploads"
PREVIEW_DIR = TEMP_DIR / "previews"
OUTPUT_DIR = TEMP_DIR / "outputs"

MAX_UPLOAD_MB = 2048
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm"}

PREVIEW_MAX_DIM = 480
FRAME_MAX_DIM = 640
