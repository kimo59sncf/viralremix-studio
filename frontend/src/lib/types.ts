export type AspectRatio = "original" | "16:9" | "9:16" | "1:1" | "4:5";
export type Temperature = "none" | "warm" | "cold";

export interface TransformationsParams {
  mirror_horizontal: boolean;
  rotation: number;
  zoom: number;
  aspect_ratio: AspectRatio;
  blurred_background: boolean;
}

export interface SpeedParams {
  rate: number;
}

export interface ColorParams {
  black_and_white: boolean;
  saturation: number;
  contrast: number;
  brightness: number;
  hue: number;
  temperature: Temperature;
}

export interface AudioParams {
  volume: number;
  mute: boolean;
}

export interface VideoParams {
  transformations: TransformationsParams;
  speed: SpeedParams;
  color: ColorParams;
  audio: AudioParams;
}

export interface VideoMetadata {
  id: string;
  filename: string;
  width: number | null;
  height: number | null;
  duration: number | null;
  has_audio: boolean;
}

export type JobStatusType = "queued" | "processing" | "done" | "error";

export interface JobStatus {
  job_id: string;
  status: JobStatusType;
  progress: number | null;
  error: string | null;
  download_url: string | null;
}
