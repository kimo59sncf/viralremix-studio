"""Gestion des dossiers temporaires."""
import shutil

from app import config


def ensure_dirs() -> None:
    for d in (config.TEMP_DIR, config.UPLOAD_DIR, config.PREVIEW_DIR, config.OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)


def cleanup_all() -> None:
    """Nettoie tous les fichiers temporaires (appelé au démarrage)."""
    for d in (config.UPLOAD_DIR, config.PREVIEW_DIR, config.OUTPUT_DIR):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    ensure_dirs()
