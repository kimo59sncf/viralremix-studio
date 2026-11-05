"""Schémas Pydantic partagés."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

AspectRatio = Literal["original", "16:9", "9:16", "1:1", "4:5"]
Temperature = Literal["none", "warm", "cold"]
EqualizerPreset = Literal["none", "bass", "treble", "voice", "boost"]


class TransformationsParams(BaseModel):
    mirror_horizontal: bool = False
    rotation: float = 0.0  # degrés
    zoom: float = 1.0  # 0.5 .. 3.0
    aspect_ratio: AspectRatio = "original"
    blurred_background: bool = False
    dynamic_zoom: bool = False
    dynamic_zoom_strength: float = 0.5  # 0 .. 1


class SpeedParams(BaseModel):
    rate: float = 1.0  # 0.5 / 0.75 / 1 / 1.25 / 1.5 / 2
    slow_motion: bool = False
    ramp: bool = False
    ramp_end: float = 2.0  # vitesse d'arrivée du speed ramp


class ColorParams(BaseModel):
    black_and_white: bool = False
    saturation: float = 1.0  # 0 .. 2
    contrast: float = 1.0  # 0 .. 2
    brightness: float = 0.0  # -1 .. 1
    hue: float = 0.0  # degrés -180 .. 180
    temperature: Temperature = "none"


class EffectsParams(BaseModel):
    glitch: bool = False
    motion_blur: bool = False
    film_grain: bool = False
    flash: bool = False
    vignette: bool = False


class AudioParams(BaseModel):
    volume: float = 1.0  # 0 .. 2
    mute: bool = False
    fade_in: float = 0.0  # secondes
    fade_out: float = 0.0  # secondes
    equalizer: EqualizerPreset = "none"


class VideoParams(BaseModel):
    transformations: TransformationsParams = Field(default_factory=TransformationsParams)
    speed: SpeedParams = Field(default_factory=SpeedParams)
    color: ColorParams = Field(default_factory=ColorParams)
    effects: EffectsParams = Field(default_factory=EffectsParams)
    audio: AudioParams = Field(default_factory=AudioParams)


class VideoMetadata(BaseModel):
    id: str
    filename: str
    path: str = Field(exclude=True)
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    has_audio: bool = True


class PreviewRequest(BaseModel):
    video_id: str
    params: VideoParams = Field(default_factory=VideoParams)
    start: float = 0.0
    duration: float = 3.0


class FrameRequest(BaseModel):
    video_id: str
    params: VideoParams = Field(default_factory=VideoParams)
    time: float = 0.0


class ExportRequest(BaseModel):
    video_id: str
    params: VideoParams = Field(default_factory=VideoParams)


class ExportResponse(BaseModel):
    job_id: str


class UrlResponse(BaseModel):
    url: str


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "done", "error"]
    progress: Optional[float] = None
    error: Optional[str] = None
    download_url: Optional[str] = None
