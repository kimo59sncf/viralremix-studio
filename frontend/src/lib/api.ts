import type { JobStatus, VideoMetadata, VideoParams } from "./types";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = String(data.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function uploadVideo(file: File): Promise<VideoMetadata> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/import", { method: "POST", body: form });
  return handle<VideoMetadata>(res);
}

export async function createPreview(
  videoId: string,
  params: VideoParams,
  start = 0,
  duration = 4
): Promise<string> {
  const res = await fetch("/api/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id: videoId, params, start, duration }),
  });
  const data = await handle<{ url: string }>(res);
  return data.url;
}

export async function createFramePreview(
  videoId: string,
  params: VideoParams,
  time = 0
): Promise<string> {
  const res = await fetch("/api/preview-frame", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id: videoId, params, time }),
  });
  const data = await handle<{ url: string }>(res);
  return data.url;
}

export async function exportVideo(
  videoId: string,
  params: VideoParams
): Promise<{ job_id: string }> {
  const res = await fetch("/api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id: videoId, params }),
  });
  return handle<{ job_id: string }>(res);
}

export async function getJob(jobId: string): Promise<JobStatus> {
  const res = await fetch(`/api/jobs/${jobId}`);
  return handle<JobStatus>(res);
}

export function downloadFile(url: string, filename = "viralremix_output.mp4") {
  fetch(url)
    .then((r) => r.blob())
    .then((blob) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(a.href);
    });
}
