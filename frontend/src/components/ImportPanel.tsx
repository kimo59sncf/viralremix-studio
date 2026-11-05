import { useRef, useState } from "react";
import { Film, Loader2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { uploadVideo } from "@/lib/api";
import type { VideoMetadata } from "@/lib/types";

function formatDuration(s: number | null) {
  if (s == null) return "—";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${String(sec).padStart(2, "0")}`;
}

export function ImportPanel({
  video,
  playerSrc,
  playerLabel,
  onTimeUpdate,
  onImported,
}: {
  video: VideoMetadata | null;
  playerSrc: string | null;
  playerLabel: string;
  onTimeUpdate: (t: number) => void;
  onImported: (meta: VideoMetadata) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const meta = await uploadVideo(file);
      onImported(meta);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur d'importation.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <Card className="h-fit">
      <CardContent className="space-y-3 p-4">
        <input
          ref={inputRef}
          type="file"
          accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
          className="hidden"
          onChange={handleFile}
        />
        <Button className="w-full" onClick={() => inputRef.current?.click()} disabled={uploading}>
          {uploading ? <Loader2 className="animate-spin" /> : <Upload />}
          {uploading ? "Importation…" : "Importer une vidéo"}
        </Button>
        <p className="text-[11px] leading-relaxed text-muted-foreground">
          Formats : MP4, MOV, WebM
        </p>
        {error && <p className="text-xs text-destructive">{error}</p>}

        {video && (
          <div className="space-y-0.5 text-xs text-muted-foreground">
            <p className="truncate font-medium text-foreground">{video.filename}</p>
            <p>Durée : {formatDuration(video.duration)}</p>
            <p>
              Résolution :{" "}
              {video.width && video.height ? `${video.width}×${video.height}` : "—"}
            </p>
          </div>
        )}

        {playerSrc && (
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Film className="h-3.5 w-3.5" /> {playerLabel}
            </div>
            <video
              key={playerSrc}
              src={playerSrc}
              controls
              className="aspect-video w-full rounded-lg border border-border bg-black"
              onTimeUpdate={(e) => onTimeUpdate(e.currentTarget.currentTime)}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
