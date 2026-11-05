"""Service de traitement : construction et exécution des commandes FFmpeg."""
import subprocess
import threading

from app.services.ffmpeg_locator import get_ffmpeg_path


def build_command(
    input_path,
    output_path,
    filter_complex,
    map_audio,
    *,
    start=None,
    duration=None,
    is_image=False,
    crf=23,
):
    ffmpeg = get_ffmpeg_path()
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    if start is not None:
        cmd += ["-ss", str(start)]
    cmd += ["-i", input_path]
    if not is_image and duration is not None:
        cmd += ["-t", str(duration)]
    cmd += ["-filter_complex", filter_complex, "-map", "[vout]"]
    if map_audio:
        cmd += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-an"]
    if is_image:
        cmd += ["-frames:v", "1", "-q:v", "2"]
    else:
        cmd += [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
        ]
    cmd += ["-progress", "pipe:1", "-nostats"]
    cmd.append(output_path)
    return cmd


def run(cmd, progress_cb=None, total_seconds=None):
    """Exécute ffmpeg et remonte la progression (out_time_us)."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    stderr_lines = []

    def drain_stderr():
        for line in proc.stderr:
            stderr_lines.append(line.rstrip())

    thread = threading.Thread(target=drain_stderr, daemon=True)
    thread.start()

    for line in proc.stdout:
        line = line.strip()
        if line.startswith("out_time_us="):
            try:
                us = int(line.split("=", 1)[1])
            except ValueError:
                continue
            if progress_cb and total_seconds:
                pct = us / (total_seconds * 1_000_000) * 100
                progress_cb(max(0.0, min(pct, 100.0)))
        elif line == "progress=end" and progress_cb:
            progress_cb(100.0)

    proc.wait()
    thread.join(timeout=5)

    if proc.returncode != 0:
        tail = "\n".join(stderr_lines[-20:])
        raise RuntimeError(tail or f"FFmpeg a échoué (code {proc.returncode}).")
