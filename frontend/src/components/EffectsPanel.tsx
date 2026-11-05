import {
  Circle,
  Contrast,
  Crop,
  Droplets,
  FlipHorizontal,
  Gauge,
  Layers,
  Palette,
  RotateCw,
  Sun,
  Thermometer,
  Volume2,
  VolumeX,
  ZoomIn,
} from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Segmented } from "@/components/ui/segmented";
import { EffectCard, SectionTitle, SliderControl } from "./controls";
import type {
  AspectRatio,
  AudioParams,
  ColorParams,
  SpeedParams,
  Temperature,
  TransformationsParams,
  VideoParams,
} from "@/lib/types";

interface Props {
  params: VideoParams;
  setTransformations: (p: Partial<TransformationsParams>) => void;
  setSpeed: (p: Partial<SpeedParams>) => void;
  setColor: (p: Partial<ColorParams>) => void;
  setAudio: (p: Partial<AudioParams>) => void;
}

const ASPECT_OPTIONS: { value: string; label: string }[] = [
  { value: "original", label: "Original" },
  { value: "16:9", label: "16:9" },
  { value: "9:16", label: "9:16" },
  { value: "1:1", label: "1:1" },
  { value: "4:5", label: "4:5" },
];

const SPEED_OPTIONS: { value: string; label: string }[] = [
  { value: "0.5", label: "0.5×" },
  { value: "0.75", label: "0.75×" },
  { value: "1", label: "1×" },
  { value: "1.25", label: "1.25×" },
  { value: "1.5", label: "1.5×" },
  { value: "2", label: "2×" },
];

const TEMP_OPTIONS: { value: string; label: string }[] = [
  { value: "none", label: "Neutre" },
  { value: "warm", label: "Chaud" },
  { value: "cold", label: "Froid" },
];

export function EffectsPanel({ params, setTransformations, setSpeed, setColor, setAudio }: Props) {
  const t = params.transformations;
  const c = params.color;
  const a = params.audio;

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <SectionTitle>Transformations d'image</SectionTitle>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <EffectCard
            icon={<FlipHorizontal className="h-4 w-4" />}
            title="Miroir horizontal"
            active={t.mirror_horizontal}
            onReset={() => setTransformations({ mirror_horizontal: false })}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {t.mirror_horizontal ? "Activé" : "Désactivé"}
              </span>
              <Switch
                checked={t.mirror_horizontal}
                onCheckedChange={(v) => setTransformations({ mirror_horizontal: v })}
              />
            </div>
          </EffectCard>

          <EffectCard
            icon={<RotateCw className="h-4 w-4" />}
            title="Rotation légère"
            active={t.rotation !== 0}
            onReset={() => setTransformations({ rotation: 0 })}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {t.rotation !== 0 ? "Activé" : "Désactivé"}
              </span>
              <Switch
                checked={t.rotation !== 0}
                onCheckedChange={(v) => setTransformations({ rotation: v ? 5 : 0 })}
              />
            </div>
            {t.rotation !== 0 && (
              <SliderControl
                label="Angle"
                value={t.rotation}
                min={-15}
                max={15}
                step={1}
                onChange={(v) => setTransformations({ rotation: v })}
                format={(v) => `${v}°`}
              />
            )}
          </EffectCard>

          <EffectCard
            icon={<ZoomIn className="h-4 w-4" />}
            title="Zoom avant / arrière"
            active={t.zoom !== 1}
            onReset={() => setTransformations({ zoom: 1 })}
          >
            <SliderControl
              label="Zoom"
              value={t.zoom}
              min={0.5}
              max={3}
              step={0.1}
              onChange={(v) => setTransformations({ zoom: v })}
              format={(v) => `${v.toFixed(1)}×`}
            />
          </EffectCard>

          <EffectCard
            icon={<Crop className="h-4 w-4" />}
            title="Format"
            active={t.aspect_ratio !== "original"}
            onReset={() => setTransformations({ aspect_ratio: "original", blurred_background: false })}
          >
            <Segmented
              value={t.aspect_ratio}
              options={ASPECT_OPTIONS}
              onChange={(v) => setTransformations({ aspect_ratio: v as AspectRatio })}
            />
          </EffectCard>

          <EffectCard
            icon={<Layers className="h-4 w-4" />}
            title="Arrière-plan flouté"
            active={t.blurred_background}
            onReset={() => setTransformations({ blurred_background: false })}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {t.aspect_ratio === "original"
                  ? "Choisissez un format"
                  : t.blurred_background
                    ? "Activé"
                    : "Désactivé"}
              </span>
              <Switch
                checked={t.blurred_background}
                disabled={t.aspect_ratio === "original"}
                onCheckedChange={(v) => setTransformations({ blurred_background: v })}
              />
            </div>
          </EffectCard>
        </div>
      </section>

      <section className="space-y-3">
        <SectionTitle>Vitesse</SectionTitle>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <EffectCard
            icon={<Gauge className="h-4 w-4" />}
            title="Vitesse"
            active={params.speed.rate !== 1}
            onReset={() => setSpeed({ rate: 1 })}
          >
            <Segmented
              value={String(params.speed.rate)}
              options={SPEED_OPTIONS}
              onChange={(v) => setSpeed({ rate: parseFloat(v) })}
            />
          </EffectCard>
        </div>
      </section>

      <section className="space-y-3">
        <SectionTitle>Couleurs et rendu</SectionTitle>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <EffectCard
            icon={<Circle className="h-4 w-4" />}
            title="Noir et blanc"
            active={c.black_and_white}
            onReset={() => setColor({ black_and_white: false })}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {c.black_and_white ? "Activé" : "Désactivé"}
              </span>
              <Switch
                checked={c.black_and_white}
                onCheckedChange={(v) => setColor({ black_and_white: v })}
              />
            </div>
          </EffectCard>

          <EffectCard
            icon={<Droplets className="h-4 w-4" />}
            title="Saturation"
            active={c.saturation !== 1}
            onReset={() => setColor({ saturation: 1 })}
          >
            <SliderControl
              label="Intensité"
              value={c.saturation}
              min={0}
              max={2}
              step={0.05}
              onChange={(v) => setColor({ saturation: v })}
            />
          </EffectCard>

          <EffectCard
            icon={<Contrast className="h-4 w-4" />}
            title="Contraste"
            active={c.contrast !== 1}
            onReset={() => setColor({ contrast: 1 })}
          >
            <SliderControl
              label="Intensité"
              value={c.contrast}
              min={0}
              max={2}
              step={0.05}
              onChange={(v) => setColor({ contrast: v })}
            />
          </EffectCard>

          <EffectCard
            icon={<Sun className="h-4 w-4" />}
            title="Luminosité"
            active={c.brightness !== 0}
            onReset={() => setColor({ brightness: 0 })}
          >
            <SliderControl
              label="Intensité"
              value={c.brightness}
              min={-1}
              max={1}
              step={0.05}
              onChange={(v) => setColor({ brightness: v })}
            />
          </EffectCard>

          <EffectCard
            icon={<Palette className="h-4 w-4" />}
            title="Teinte"
            active={c.hue !== 0}
            onReset={() => setColor({ hue: 0 })}
          >
            <SliderControl
              label="Rotation"
              value={c.hue}
              min={-180}
              max={180}
              step={1}
              onChange={(v) => setColor({ hue: v })}
              format={(v) => `${v}°`}
            />
          </EffectCard>

          <EffectCard
            icon={<Thermometer className="h-4 w-4" />}
            title="Température"
            active={c.temperature !== "none"}
            onReset={() => setColor({ temperature: "none" })}
          >
            <Segmented
              value={c.temperature}
              options={TEMP_OPTIONS}
              onChange={(v) => setColor({ temperature: v as Temperature })}
            />
          </EffectCard>
        </div>
      </section>

      <section className="space-y-3">
        <SectionTitle>Audio</SectionTitle>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <EffectCard
            icon={<Volume2 className="h-4 w-4" />}
            title="Volume"
            active={a.volume !== 1}
            onReset={() => setAudio({ volume: 1 })}
          >
            <SliderControl
              label="Niveau"
              value={a.volume}
              min={0}
              max={2}
              step={0.05}
              onChange={(v) => setAudio({ volume: v })}
              format={(v) => `${Math.round(v * 100)} %`}
            />
          </EffectCard>

          <EffectCard
            icon={<VolumeX className="h-4 w-4" />}
            title="Supprimer l'audio"
            active={a.mute}
            onReset={() => setAudio({ mute: false })}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {a.mute ? "Coupé" : "Conservé"}
              </span>
              <Switch checked={a.mute} onCheckedChange={(v) => setAudio({ mute: v })} />
            </div>
          </EffectCard>
        </div>
      </section>

    </div>
  );
}
