async function request(path, options = {}) {
  const res = await fetch(path, options);
  const text = await res.text();
  let body = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { raw: text };
  }
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/api/auth")) {
      window.location.assign("/login");
    }
    const detail = body?.detail ?? body ?? {};
    const message =
      detail?.error?.message ||
      (typeof detail === "string" ? detail : "") ||
      `${res.status} ${res.statusText}`;
    const error = new Error(message);
    error.status = res.status;
    error.detail = detail;
    throw error;
  }
  return body;
}

export const getHealth = () => request("/api/health");
export const getMe = () => request("/api/auth/me");
export const login = (username, password) =>
  request("/api/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
export const logout = () => request("/api/auth/logout", { method: "POST" });
export const getRuns = () => request("/api/runs");
export const importRun = (path) =>
  request("/api/runs/import", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ path, confirm: true }),
  });
export const createRun = (payload) =>
  request("/api/runs", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
export const cancelRun = (runId) =>
  request(`/api/runs/${encodeURIComponent(runId)}/cancel`, { method: "POST" });
export const resumeRun = (runId) =>
  request(`/api/runs/${encodeURIComponent(runId)}/resume`, { method: "POST" });
export const deleteRun = (runId) =>
  request(`/api/runs/${encodeURIComponent(runId)}?confirm=${encodeURIComponent(runId)}`, { method: "DELETE" });
export const importRatings = (runId, rater, file, force = false) => {
  const form = new FormData();
  form.append("rater", rater);
  form.append("file", file);
  form.append("force", force ? "true" : "false");
  return request(`/api/runs/${encodeURIComponent(runId)}/ratings/import`, {
    method: "POST",
    body: form,
  });
};
export const validateManifest = (path) =>
  request(`/api/manifest/validate?path=${encodeURIComponent(path)}`);
export const getRun = (runId) => request(`/api/runs/${encodeURIComponent(runId)}`);
export const getClips = (runId) => request(`/api/runs/${encodeURIComponent(runId)}/clips`);
export const getClip = (runId, clipId) =>
  request(`/api/runs/${encodeURIComponent(runId)}/clips/${encodeURIComponent(clipId)}`);
export const getLabel = (clipId) => request(`/api/labels/${encodeURIComponent(clipId)}`);
export const getLabelContext = (runId, clipId) =>
  request(`/api/runs/${encodeURIComponent(runId)}/labels/${encodeURIComponent(clipId)}`);
export const saveLabel = (clipId, label, etag, labeler) =>
  request(`/api/labels/${encodeURIComponent(clipId)}?labeler=${encodeURIComponent(labeler)}`, {
    method: "PUT",
    headers: {
      "content-type": "application/json",
      "If-Match": `"${etag}"`,
    },
    body: JSON.stringify(label),
  });
export const scoreRun = (runId) =>
  request(`/api/runs/${encodeURIComponent(runId)}/score`, { method: "POST" });
export const sourceUrl = (runId, clipId) =>
  `/api/runs/${encodeURIComponent(runId)}/media/${encodeURIComponent(clipId)}/source`;
export const artifactUrl = (runId, clipId, kind) =>
  `/api/runs/${encodeURIComponent(runId)}/media/${encodeURIComponent(clipId)}/artifact/${encodeURIComponent(kind)}`;
export const getRateQueue = (runId, rater) =>
  request(`/api/runs/${encodeURIComponent(runId)}/rate?rater=${encodeURIComponent(rater)}`);
export const getBlind = (runId, clipId, rater) =>
  request(
    `/api/runs/${encodeURIComponent(runId)}/blind/${encodeURIComponent(clipId)}?rater=${encodeURIComponent(rater)}`,
  );
export const getRatingSheet = (runId, rater) =>
  request(`/api/runs/${encodeURIComponent(runId)}/ratings/${encodeURIComponent(rater)}`);
export const saveRating = (runId, rater, clipId, rating, etag) =>
  request(
    `/api/runs/${encodeURIComponent(runId)}/ratings/${encodeURIComponent(rater)}/${encodeURIComponent(clipId)}`,
    {
      method: "PUT",
      headers: { "content-type": "application/json", "If-Match": `"${etag}"` },
      body: JSON.stringify(rating),
    },
  );
export const submitRatings = (runId, rater) =>
  request(`/api/runs/${encodeURIComponent(runId)}/ratings/${encodeURIComponent(rater)}/submit`, {
    method: "POST",
  });
export const reopenRating = (runId, rater, clipId, reason) =>
  request(
    `/api/runs/${encodeURIComponent(runId)}/ratings/${encodeURIComponent(rater)}/${encodeURIComponent(clipId)}/reopen`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ reason }),
    },
  );
export const runStability = (runId, against) =>
  request(`/api/runs/${encodeURIComponent(runId)}/stability`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ against }),
  });
export const reviewTemplateUrl = (runId, kind) =>
  `/api/runs/${encodeURIComponent(runId)}/reviews/${encodeURIComponent(kind)}/template`;
export const importReview = (runId, kind, reviewer, file) => {
  const form = new FormData();
  form.append("reviewer", reviewer);
  form.append("file", file);
  return request(`/api/runs/${encodeURIComponent(runId)}/reviews/${encodeURIComponent(kind)}/import`, {
    method: "POST",
    body: form,
  });
};
export const getAdjudicationQueue = (runId) =>
  request(`/api/runs/${encodeURIComponent(runId)}/adjudication`);
export const getAdjudication = (runId, clipId) =>
  request(`/api/runs/${encodeURIComponent(runId)}/adjudication/${encodeURIComponent(clipId)}`);
export const saveAdjudication = (runId, clipId, decision, etag) =>
  request(`/api/runs/${encodeURIComponent(runId)}/adjudication/${encodeURIComponent(clipId)}`, {
    method: "PUT",
    headers: { "content-type": "application/json", "If-Match": `"${etag}"` },
    body: JSON.stringify(decision),
  });

export const LABELER_KEY = "coachme.benchmark.labeler";

export function getLabeler() {
  try {
    return localStorage.getItem(LABELER_KEY) || "coach-a";
  } catch {
    return "coach-a";
  }
}

export function setLabeler(name) {
  try {
    localStorage.setItem(LABELER_KEY, name);
  } catch {
    /* ignore */
  }
}
