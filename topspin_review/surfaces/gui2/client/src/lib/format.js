// Small shared helpers for the gui2 client.

export const pretty = (v) => {
  if (v == null || v === "") return "";
  if (typeof v === "string") {
    try {
      return JSON.stringify(JSON.parse(v), null, 2);
    } catch {
      return v;
    }
  }
  return JSON.stringify(v, null, 2);
};

export function scoreTone(score) {
  if (score >= 80) return "text-good";
  if (score >= 60) return "text-warn";
  return "text-bad";
}

export function issueText(issue) {
  if (typeof issue === "string") return issue;
  return issue?.issue || "";
}

export function evidenceTimes(issue) {
  return (issue?.evidence_times || []).filter((t) => t != null);
}

// Every (issue, timestamp) pair, flattened, for the moments playlist.
export function moments(report) {
  const out = [];
  (report?.issues || []).forEach((issue, i) => {
    const times = evidenceTimes(issue);
    if (!times.length) {
      out.push({ idx: i, t: null, text: issueText(issue), confidence: issue?.confidence || "" });
    } else {
      times.forEach((t) => out.push({ idx: i, t, text: issueText(issue), confidence: issue?.confidence || "" }));
    }
  });
  return out.sort((a, b) => (a.t ?? 1e9) - (b.t ?? 1e9));
}

// One entry per issue (text once) with all its timestamps as chips.
export function issueGroups(report) {
  return (report?.issues || []).map((issue, i) => ({
    idx: i,
    text: issueText(issue),
    confidence: issue?.confidence || "",
    times: evidenceTimes(issue),
  }));
}

// Movement-over-time series from the report metrics.
export function movementSeries(report) {
  const activity = (report?.metrics || {}).activity || [];
  return activity.map((s) => ({ t: s.t, energy: s.energy }));
}

export function fmtTime(seconds) {
  if (seconds == null) return "";
  const s = Math.max(0, Number(seconds));
  const m = Math.floor(s / 60);
  const r = (s % 60).toFixed(1).padStart(4, "0");
  return m ? `${m}:${r}` : `${r}s`;
}

export function captionFor(report) {
  if (!report) return "";
  const n = (report.issues || []).length;
  return `My ${report.sport || "session"} coaching report 🏓\n${n} thing(s) to work on · focus: ${report.focus || "—"}\n\n#TopspinReview`;
}

export const JOB_TONE = { done: "text-good", running: "text-accent2", failed: "text-bad", cancelled: "text-muted" };
