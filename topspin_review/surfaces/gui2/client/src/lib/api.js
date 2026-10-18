import { currentLanguage } from "$lib/appearance";

// Same-origin when served by FastAPI; CORS is enabled for the Vite dev server.
// The API lives at the server root; the SPA is mounted under /gui2.
export async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

export const getReports = () => api("/reports");
export const getSettings = () => api("/settings");
export const saveSettings = (patch) =>
  api("/settings", {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(patch),
  });
export const getReport = (stem) => api(`/reports/${encodeURIComponent(stem)}`);
export const deleteReport = (stem) => api(`/reports/${encodeURIComponent(stem)}`, { method: "DELETE" });
export const ask = (stem, q) =>
  api(
    `/reports/${encodeURIComponent(stem)}/ask?q=${encodeURIComponent(q)}&language=${encodeURIComponent(currentLanguage())}`,
  );
export const saveAnnotations = (stem, annotations) =>
  api(`/reports/${encodeURIComponent(stem)}/annotations`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ annotations }),
  });
export const patchReport = (stem, patch) =>
  api(`/reports/${encodeURIComponent(stem)}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(patch),
  });
export const feedback = (stem, item, vote, note = "") =>
  api(`/reports/${encodeURIComponent(stem)}/feedback`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ item, vote, note }),
  });
export const compare = (a, b) => api(`/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`);

export const analyzeAsync = (body) =>
  api("/analyze/async", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ ...body, language: currentLanguage() }),
  });

export const jobStatus = (id) => api(`/jobs/${encodeURIComponent(id)}`);
export const cancel = (id) => api(`/jobs/${encodeURIComponent(id)}/cancel`, { method: "POST" });
export const retry = (id) => api(`/jobs/${encodeURIComponent(id)}/retry`, { method: "POST" });
export const jobs = () => api("/jobs");
export const readiness = () => api("/ready");
export const getProfile = () => api("/profile");
export const saveProfile = (profile) =>
  api("/profile", {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(profile),
  });
export const getConfig = () => api("/config");
export const getTrends = () => api("/trends");
export const samples = () => api("/samples");

export const source = (stem) => `/source/${encodeURIComponent(stem)}`;
export const artifact = (stem, kind) => `/artifact/${encodeURIComponent(stem)}/${kind}`;
export const clip = (stem, key) => `/clip/${encodeURIComponent(stem)}/${encodeURIComponent(key)}`;
export const callImage = (stem, name) => `/callmedia/${encodeURIComponent(stem)}/${encodeURIComponent(name)}`;
export const exportUrl = (stem, fmt) => `/export/${encodeURIComponent(stem)}/${fmt}`;
export const reelUrl = (stem) => `/reel/${encodeURIComponent(stem)}`;
export const cardUrl = (stem) => `/cards/${encodeURIComponent(stem)}`;
export const trimUrl = (stem, start, end, fmt = "mp4", vertical = false) =>
  `/trim/${encodeURIComponent(stem)}?start=${start}&end=${end}&fmt=${fmt}&vertical=${vertical}`;
// A thumbnail for a session card: the full-frame pose image (real frame + skeleton) if present,
// else the motion map, else the frames contact sheet, else the source photo.
export const thumb = (report) =>
  report.has_pose_hero
    ? `/thumb/${encodeURIComponent(report.stem)}`
    : report.has_motion
      ? artifact(report.stem, "motion")
      : report.has_frames
        ? artifact(report.stem, "frames")
        : report.is_photo && report.has_source
          ? source(report.stem)
          : "";

export async function upload(file) {
  const form = new FormData();
  form.append("file", file);
  return api("/upload", { method: "POST", body: form });
}

// Fetch a video from a link (YouTube etc.) and return its server-side path.
export const youtube = (url) =>
  api("/youtube", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ url }),
  });
