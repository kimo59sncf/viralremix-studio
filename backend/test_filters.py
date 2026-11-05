"""Test direct des filtres FFmpeg générés (sans passer par l'API)."""
from app.models import VideoParams
from app.services import command_builder, processing_service

SRC = "test.mp4"
SRC_W, SRC_H = 1280, 720
DUR = 8.0


def run(name, params):
    out_w, out_h = command_builder.target_resolution(params, SRC_W, SRC_H)
    fc, map_audio = command_builder.build_filter_complex(
        params, SRC_W, SRC_H, out_w, out_h, True, DUR
    )
    out = f"out_{name}.mp4"
    print(f"=== {name} (map_audio={map_audio}) ===")
    print("fc:", fc)
    cmd = processing_service.build_command(SRC, out, fc, map_audio)
    try:
        processing_service.run(cmd)
        print(f"OK -> {out}")
    except Exception as e:
        print("FAIL:", str(e)[:600])


p1 = VideoParams()
p1.transformations.dynamic_zoom = True
p1.transformations.dynamic_zoom_strength = 0.5
p1.speed.rate = 1.5
p1.color.saturation = 1.1
p1.color.contrast = 1.1
p1.effects.glitch = True
p1.effects.motion_blur = True
p1.effects.film_grain = True
p1.effects.flash = True
p1.effects.vignette = True
p1.audio.fade_in = 0.5
p1.audio.fade_out = 0.5
p1.audio.equalizer = "bass"
run("effects_audio", p1)

p2 = VideoParams()
p2.speed.slow_motion = True
run("slow_motion", p2)

p3 = VideoParams()
p3.speed.ramp = True
p3.speed.ramp_end = 2.5
run("speed_ramp", p3)
