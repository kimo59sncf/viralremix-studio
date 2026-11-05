"""Générateur de graphes de filtres FFmpeg à partir des paramètres utilisateur."""
from app.models import VideoParams


def _ratio(aspect: str):
    if aspect == "original":
        return None
    w, h = aspect.split(":")
    return int(w) / int(h)


def _fmt(n: float) -> str:
    return f"{n:.6f}".rstrip("0").rstrip(".")


def target_resolution(params: VideoParams, src_w, src_h):
    """Résolution de sortie (1080p) selon le format choisi."""
    ar = params.transformations.aspect_ratio
    if ar == "9:16":
        return 1080, 1920
    if ar == "1:1":
        return 1080, 1080
    if ar == "4:5":
        return 1080, 1350
    if ar == "16:9":
        return 1920, 1080
    # "original" : on conserve l'orientation de la source.
    if src_w and src_h and src_w >= src_h:
        return 1920, 1080
    return 1080, 1920


def _color_filters(c) -> list:
    f = []
    if c.black_and_white:
        f.append("hue=s=0")

    eq = []
    if c.saturation != 1.0:
        eq.append(f"saturation={_fmt(c.saturation)}")
    if c.contrast != 1.0:
        eq.append(f"contrast={_fmt(c.contrast)}")
    if c.brightness != 0.0:
        eq.append(f"brightness={_fmt(c.brightness)}")
    if eq:
        f.append("eq=" + ":".join(eq))

    if not c.black_and_white and c.hue != 0:
        f.append(f"hue=h={_fmt(c.hue)}")

    if c.temperature == "warm":
        f.append("colortemperature=temperature=4000")
    elif c.temperature == "cold":
        f.append("colortemperature=temperature=9500")

    return f


def _atempo_chain(rate: float) -> str:
    """atempo accepte 0.5..2.0 ; on chaîne pour couvrir d'autres valeurs."""
    parts = []
    r = rate
    while r < 0.5:
        parts.append("atempo=0.5")
        r /= 0.5
    while r > 2.0:
        parts.append("atempo=2.0")
        r /= 2.0
    parts.append(f"atempo={_fmt(r)}")
    return ",".join(parts)


def _equalizer_filters(preset: str) -> list:
    if preset == "bass":
        return ["equalizer=f=80:t=q:g=6:width_type=h"]
    if preset == "treble":
        return ["equalizer=f=8000:t=q:g=6:width_type=h"]
    if preset == "voice":
        return ["equalizer=f=2500:t=q:g=5:width_type=h"]
    if preset == "boost":
        return [
            "equalizer=f=60:t=q:g=5:width_type=h",
            "equalizer=f=12000:t=q:g=5:width_type=h",
        ]
    return []


def _effects_filters(e) -> list:
    f = []
    if e.glitch:
        f.append(
            "rgbashift=rh='if(lt(mod(t,0.3),0.08),random(1)*24-12,0)'"
            ":bh='if(lt(mod(t,0.3),0.08),random(1)*24-12,0)'"
        )
    if e.vignette:
        f.append("vignette=PI/4")
    if e.film_grain:
        f.append("noise=alls=15:allf=t+u")
    if e.motion_blur:
        f.append("tmix=frames=3")
    if e.flash:
        f.append("eq=brightness='if(lt(mod(t,1.5),0.1),0.5,0)'")
    return f


def output_duration(src_duration, params):
    """Durée estimée de sortie (fondus, progression)."""
    if not src_duration:
        return None
    sp = params.speed
    if sp.slow_motion:
        return src_duration * 2.0
    if sp.ramp:
        avg = (0.5 + sp.ramp_end) / 2.0
        return src_duration / avg if avg else src_duration
    if sp.rate:
        return src_duration / sp.rate
    return src_duration


def build_video_graph(params: VideoParams, src_w: int, src_h: int, out_w: int, out_h: int, src_duration=None) -> str:
    t = params.transformations
    c = params.color
    rate = params.speed.rate

    segs = []
    cur = "0:v"
    counter = {"n": 0}

    def nxt(prefix="s"):
        counter["n"] += 1
        return f"{prefix}{counter['n']}"

    def chain(filters, prefix="s"):
        nonlocal cur
        lab = nxt(prefix)
        segs.append(f"[{cur}]{filters}[{lab}]")
        cur = lab

    # 1. Miroir horizontal
    if t.mirror_horizontal:
        chain("hflip", "pre")

    # 2. Zoom (avant / arrière)
    if t.zoom > 1.0:
        z = _fmt(t.zoom)
        crop_w = max(2, round(src_w / t.zoom))
        crop_h = max(2, round(src_h / t.zoom))
        x = round((src_w - crop_w) / 2)
        y = round((src_h - crop_h) / 2)
        chain(f"crop={crop_w}:{crop_h}:{x}:{y}", "zoom")
    elif t.zoom < 1.0:
        new_w = max(2, round(src_w * t.zoom))
        new_h = max(2, round(src_h * t.zoom))
        x = round((src_w - new_w) / 2)
        y = round((src_h - new_h) / 2)
        chain(f"scale={new_w}:{new_h},pad={src_w}:{src_h}:{x}:{y}:black", "zoom")

    # 3. Format / recadrage / arrière-plan flouté
    ar = _ratio(t.aspect_ratio)
    if ar is not None:
        if t.blurred_background:
            bg = nxt("bg")
            fg = nxt("fg")
            ov = nxt("ov")
            segs.append(f"[{cur}]split[{bg}][{fg}]")
            segs.append(
                f"[{bg}]scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
                f"crop={out_w}:{out_h},boxblur=20:5[{bg}blur]"
            )
            segs.append(
                f"[{fg}]scale={out_w}:{out_h}:force_original_aspect_ratio=decrease[{fg}scale]"
            )
            segs.append(f"[{bg}blur][{fg}scale]overlay=(W-w)/2:(H-h)/2[{ov}]")
            cur = ov
        else:
            ars = _fmt(ar)
            chain(
                f"crop=min(iw\\,ih*{ars}):min(iw/{ars}\\,ih):"
                f"(iw-min(iw\\,ih*{ars}))/2:(ih-min(iw/{ars}\\,ih))/2",
                "crop",
            )

    # 4. Zoom dynamique (zoom progressif sur la durée)
    if t.dynamic_zoom and src_duration:
        s = _fmt(t.dynamic_zoom_strength)
        d = _fmt(src_duration)
        z = f"(1+{s}*t/{d})"
        chain(
            f"crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:(ih-ih/{z})/2",
            "dynzoom",
        )

    # 5. Couleurs
    cf = _color_filters(c)
    if cf:
        chain(",".join(cf), "color")

    # 6. Effets modernes
    ef = _effects_filters(params.effects)
    if ef:
        chain(",".join(ef), "fx")

    # 7. Vitesse
    sp = params.speed
    if sp.slow_motion:
        chain("minterpolate=fps=60:mi_mode=blend,setpts=2*PTS", "slowmo")
    elif sp.ramp and src_duration:
        start = 0.5
        end = sp.ramp_end
        expr = f"PTS/({_fmt(start)}+{_fmt(end - start)}*T/{_fmt(src_duration)})"
        chain(f"setpts={expr}", "ramp")
    elif rate != 1.0:
        chain(f"setpts=(1/{_fmt(rate)})*PTS", "speed")

    # 8. Mise à l'échelle finale + rotation légère (taille fixe conservée)
    tail = f"scale={out_w}:{out_h}"
    if t.rotation != 0:
        tail += f",rotate={_fmt(t.rotation)}*PI/180:ow={out_w}:oh={out_h}:fillcolor=black"
    segs.append(f"[{cur}]{tail}[vout]")

    return ";".join(segs)


def build_audio_graph(params: VideoParams, src_duration=None):
    a = params.audio
    sp = params.speed
    if a.mute:
        return None
    if sp.ramp:
        return None  # speed ramp : audio coupé pour éviter la désynchronisation

    f = []
    if a.volume != 1.0:
        f.append(f"volume={_fmt(a.volume)}")
    if sp.slow_motion:
        f.append("atempo=0.5")
    elif sp.rate != 1.0:
        f.append(_atempo_chain(sp.rate))

    if a.equalizer != "none":
        f.extend(_equalizer_filters(a.equalizer))

    dur_out = output_duration(src_duration, params)
    if a.fade_in > 0:
        f.append(f"afade=t=in:st=0:d={_fmt(a.fade_in)}")
    if a.fade_out > 0 and dur_out is not None and dur_out > a.fade_out:
        f.append(f"afade=t=out:st={_fmt(dur_out - a.fade_out)}:d={_fmt(a.fade_out)}")

    if f:
        return "[0:a]" + ",".join(f) + "[aout]"
    return "[0:a]anull[aout]"


def build_filter_complex(params, src_w, src_h, out_w, out_h, has_audio, src_duration=None):
    vg = build_video_graph(params, src_w, src_h, out_w, out_h, src_duration)
    ag = build_audio_graph(params, src_duration)
    parts = [vg]
    map_audio = bool(ag) and has_audio
    if map_audio:
        parts.append(ag)
    return ";".join(parts), map_audio
