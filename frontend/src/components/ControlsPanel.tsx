import { CheckCircle2, Download, Loader2, Play, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { downloadFile } from "@/lib/api";
import type { JobStatus, VideoMetadata } from "@/lib/types";

function JobProgress({ job }: { job: JobStatus }) {
  if (job.status === "processing" || job.status === "queued") {
    const pct = job.progress ?? 0;
    return (
      <div className="space-y-1.5">
        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full bg-primary transition-all" style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-muted-foreground">
          {job.progress != null ? `Export en cours… ${Math.round(pct)} %` : "Préparation…"}
        </p>
      </div>
    );
  }
  if (job.status === "done") {
    return (
      <div className="space-y-2">
        <p className="flex items-center gap-1.5 text-xs text-emerald-400">
          <CheckCircle2 className="h-3.5 w-3.5" /> Export terminé
        </p>
        <Button variant="secondary" className="w-full" onClick={() => downloadFile(job.download_url!)}>
          <Download /> Télécharger la vidéo
        </Button>
      </div>
    );
  }
  if (job.status === "error") {
    return <p className="text-xs text-destructive">Erreur : {job.error}</p>;
  }
  return null;
}

interface Props {
  video: VideoMetadata | null;
  job: JobStatus | null;
  framePreviewUrl: string | null;
  frameLoading: boolean;
  previewLoading: boolean;
  onPreview: () => void;
  onExport: () => void;
  onReset: () => void;
}

export function ControlsPanel({
  video,
  job,
  framePreviewUrl,
  frameLoading,
  previewLoading,
  onPreview,
  onExport,
  onReset,
}: Props) {
  return (
    <Card className="h-fit">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {framePreviewUrl && (
          <div>
            <p className="mb-1 text-xs text-muted-foreground">Aperçu instantané</p>
            <div className="relative overflow-hidden rounded-lg border border-border bg-black">
              {frameLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                  <Loader2 className="h-5 w-5 animate-spin text-white" />
                </div>
              )}
              <img src={framePreviewUrl} className="w-full" alt="Aperçu" />
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <Button variant="outline" className="flex-1" onClick={onPreview} disabled={!video || previewLoading}>
            {previewLoading ? <Loader2 className="animate-spin" /> : <Play />}
            Aperçu
          </Button>
          <Button variant="ghost" onClick={onReset} disabled={!video} title="Réinitialiser">
            <RotateCcw />
          </Button>
        </div>

        <Button
          className="w-full"
          onClick={onExport}
          disabled={!video || job?.status === "processing" || job?.status === "queued"}
        >
          <Download /> Exporter
        </Button>

        {job && <JobProgress job={job} />}
      </CardContent>
    </Card>
  );
}
