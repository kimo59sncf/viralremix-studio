"""Localise le binaire FFmpeg (bundled via imageio-ffmpeg, sinon PATH)."""
import shutil


def get_ffmpeg_path() -> str:
    # 1. Binaire statique fourni par le paquet imageio-ffmpeg.
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    # 2. FFmpeg présent dans le PATH système.
    found = shutil.which("ffmpeg")
    if found:
        return found

    raise RuntimeError(
        "FFmpeg introuvable. Installez le paquet 'imageio-ffmpeg' ou ajoutez ffmpeg au PATH."
    )
