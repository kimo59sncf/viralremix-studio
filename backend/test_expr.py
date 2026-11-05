import subprocess

from app.services.ffmpeg_locator import get_ffmpeg_path

ffmpeg = get_ffmpeg_path()
candidates = {
    "r*24-12": "rgbashift=rh='random(1)*24-12'",
    "if_random": "rgbashift=rh='if(1,random(1),0)'",
    "if_lt_random": "rgbashift=rh='if(lt(t,1),random(1),0)'",
    "full_glitch": "rgbashift=rh='if(lt(mod(t,0.3),0.08),random(1)*24-12,0)'",
    "full_glitch_eq": "eq=brightness='if(lt(mod(t,0.3),0.08),random(1)*24-12,0)'",
}
for name, vf in candidates.items():
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", "test.mp4",
           "-t", "1", "-vf", vf, "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    status = "OK  " if p.returncode == 0 else "FAIL"
    print(f"\n{status} {name}")
    if p.returncode:
        print((p.stderr or "").strip()[:800])
