"""Analyse d'un fichier vidéo via FFmpeg (durée, résolution, flux)."""
import re
import subprocess


def probe(ffmpeg: str, path: str) -> dict:
    cmd = [ffmpeg, "-hide_banner", "-i", path]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    info = proc.stderr or ""

    result = {
        "duration": None,
        "width": None,
        "height": None,
        "has_video": False,
        "has_audio": False,
    }

    for line in info.splitlines():
        if "Duration:" in line:
            m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", line)
            if m:
                result["duration"] = (
                    int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
                )
        if "Stream #" in line and "Video:" in line:
            result["has_video"] = True
            if result["width"] is None:
                m = re.search(r"(\d{2,5})x(\d{2,5})", line)
                if m:
                    result["width"] = int(m.group(1))
                    result["height"] = int(m.group(2))
        if "Stream #" in line and "Audio:" in line:
            result["has_audio"] = True

    return result
