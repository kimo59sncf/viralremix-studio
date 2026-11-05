import type { VideoParams } from "./types";

export function defaultParams(): VideoParams {
  return {
    transformations: {
      mirror_horizontal: false,
      rotation: 0,
      zoom: 1,
      aspect_ratio: "original",
      blurred_background: false,
    },
    speed: { rate: 1 },
    color: {
      black_and_white: false,
      saturation: 1,
      contrast: 1,
      brightness: 0,
      hue: 0,
      temperature: "none",
    },
    audio: { volume: 1, mute: false },
  };
}
