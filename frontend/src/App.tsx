import { useCallback, useEffect, useRef, useState } from "react";
import { Clapperboard } from "lucide-react";
import type {
  AudioParams,
  ColorParams,
  JobStatus,
  SpeedParams,
  TransformationsParams,
  VideoMetadata,
  VideoParams,
} from "@/lib/types";
import { defaultParams } from "@/lib/defaultParams";
import { createFramePreview, createPreview, exportVideo, getJob } from "@/lib/api";
import { ImportPanel } from "@/components/ImportPanel";
import { EffectsPanel } from "@/components/EffectsPanel";
import { ControlsPanel } from "@/components/ControlsPanel";

export default function App() {
  const [video, setVideo] = useState<VideoMetadata | null>(null);
  const [params, setParams] = useState<VideoParams>(defaultParams());
  const [playerSrc, setPlayerSrc] = useState<string | null>(null);
  const [playerLabel, setPlayerLabel] = useState<string>("Aperçu");
  const [framePreviewUrl, setFramePreviewUrl] = useState<string | null>(null);
  const [frameLoading, setFrameLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [job, setJob] = useState<JobStatus | null>(null);

  const playerTimeRef = useRef(0);
  const pollRef = useRef<number | null>(null);

  const stopPoll = useCallback(() => {
    if (pollRef.current != null) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => () => stopPoll(), [stopPoll]);

  const setTransformations = useCallback(
    (patch: Partial<TransformationsParams>) =>
      setParams((p) => ({ ...p, transformations: { ...p.transformations, ...patch } })),
    []
  );
  const setSpeed = useCallback(
    (patch: Partial<SpeedParams>) => setParams((p) => ({ ...p, speed: { ...p.speed, ...patch } })),
    []
  );
  const setColor = useCallback(
    (patch: Partial<ColorParams>) => setParams((p) => ({ ...p, color: { ...p.color, ...patch } })),
    []
  );
  const setAudio = useCallback(
    (patch: Partial<AudioParams>) => setParams((p) => ({ ...p, audio: { ...p.audio, ...patch } })),
    []
  );

  // Aperçu d'image automatique (debounced) quand les paramètres changent.
  useEffect(() => {
    if (!video) return;
    setFrameLoading(true);
    const t = setTimeout(async () => {
      try {
        const url = await createFramePreview(video.id, params, playerTimeRef.current);
        setFramePreviewUrl(`${url}?t=${Date.now()}`);
      } catch {
        /* silencieux */
      } finally {
        setFrameLoading(false);
      }
    }, 700);
    return () => {
      clearTimeout(t);
      setFrameLoading(false);
    };
  }, [params, video]);

  function handleImported(meta: VideoMetadata) {
    setVideo(meta);
    setParams(defaultParams());
    setPlayerSrc(`/api/video/${meta.id}`);
    setPlayerLabel("Original");
    setFramePreviewUrl(null);
    setJob(null);
    stopPoll();
  }

  function handleReset() {
    setParams(defaultParams());
    if (video) {
      setPlayerSrc(`/api/video/${video.id}`);
      setPlayerLabel("Original");
    }
    setJob(null);
    stopPoll();
  }

  async function handlePreview() {
    if (!video) return;
    setPreviewLoading(true);
    try {
      const url = await createPreview(video.id, params, 0, 4);
      setPlayerSrc(url);
      setPlayerLabel("Aperçu");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erreur lors de l'aperçu.");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleExport() {
    if (!video) return;
    try {
      const { job_id } = await exportVideo(video.id, params);
      setJob({ job_id, status: "queued", progress: 0, error: null, download_url: null });
      stopPoll();
      pollRef.current = window.setInterval(async () => {
        try {
          const status = await getJob(job_id);
          setJob(status);
          if (status.status === "done" || status.status === "error") stopPoll();
        } catch {
          /* on garde le polling */
        }
      }, 800);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erreur lors de l'export.");
    }
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-border bg-background/90 px-5 py-3.5 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Clapperboard className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-bold leading-tight tracking-tight">ViralRemix Studio</h1>
            <p className="text-xs text-muted-foreground">Transformations vidéo rapides · 100 % local</p>
          </div>
        </div>
      </header>

      <main className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-[340px_minmax(0,1fr)_360px]">
        <ImportPanel
          video={video}
          playerSrc={playerSrc}
          playerLabel={playerLabel}
          onTimeUpdate={(t) => {
            playerTimeRef.current = t;
          }}
          onImported={handleImported}
        />
        <EffectsPanel
          params={params}
          setTransformations={setTransformations}
          setSpeed={setSpeed}
          setColor={setColor}
          setAudio={setAudio}
        />
        <ControlsPanel
          video={video}
          job={job}
          framePreviewUrl={framePreviewUrl}
          frameLoading={frameLoading}
          previewLoading={previewLoading}
          onPreview={handlePreview}
          onExport={handleExport}
          onReset={handleReset}
        />
      </main>
    </div>
  );
}
