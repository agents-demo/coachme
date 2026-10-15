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

// How sure the model is that a finding is real (from the sampled frames + measured motion).
export const CONF_TONE = { high: "text-bad", medium: "text-warn", low: "text-muted" };
export const CONF_HELP =
  "Confidence: how sure the model is that this finding is real, from the frames it read and the measured motion. " +
  "high = clear evidence; medium = likely; low = uncertain (treat as a hint, not a fact).";

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

// --- pipeline step naming (shared by the live progress feed and Diagnostics) ---
// Plain-English name for each internal step (tick) label.
export const STEP_NAME = {
  startup: "Load pipeline",
  preparing: "Prepare clip",
  "sampling frames": "Pick frames",
  "measuring motion": "Measure movement",
  "tracking ball": "Track ball",
  "estimating pose": "Estimate pose",
  "writing artifacts": "Render images",
  "vision: overview": "First look",
  "vision: zoom": "Zoom in",
  "vision: detail": "Detailed findings",
  "vision: reviewing image": "Review image",
  "agent writing report": "Write report",
  "agent: analyzing": "Analyze",
  "saving report": "Save report",
  verifying: "Double-check",
  exporting: "Export files",
  done: "Done",
};
// Joint-angle series used by the pose chart (shared so callers can render the legend).
export const POSE_SERIES = [
  { key: "l_knee", label: "Left knee", color: "#4f46e5" },
  { key: "r_knee", label: "Right knee", color: "#818cf8" },
  { key: "l_elbow", label: "Left elbow", color: "#34d399" },
  { key: "r_elbow", label: "Right elbow", color: "#fbbf24" },
];

export function shortLabel(stage) {
  return STEP_NAME[stage] || stage || "";
}

// The pipeline stage each step belongs to (architecture name in parentheses).
export const STEP_GROUP = {
  startup: "Setup",
  preparing: "Setup",
  "sampling frames": "Measure",
  "measuring motion": "Measure",
  "tracking ball": "Measure",
  "estimating pose": "Measure",
  "writing artifacts": "Measure",
  "vision: overview": "Vision (observe)",
  "vision: zoom": "Vision (observe)",
  "vision: detail": "Vision (observe)",
  "vision: reviewing image": "Vision (observe)",
  "agent writing report": "Report (coach)",
  "agent: analyzing": "Report (coach)",
  "saving report": "Report (coach)",
  verifying: "Report (coach)",
  exporting: "Finalize",
  done: "Finalize",
};
export const GROUP_ORDER = ["Setup", "Measure", "Vision (observe)", "Report (coach)", "Finalize", "Other"];

// Steps that make a model/agent call.
export const MODEL_STEP = {
  "vision: overview": "vision",
  "vision: detail": "vision",
  "vision: reviewing image": "vision",
  "agent writing report": "text",
  "agent: analyzing": "text",
  verifying: "text",
};

// Hover tooltip text for each step.
export const STEP_SHORT = {
  startup: "Load the pipeline code (imports) — pre-run overhead.",
  preparing: "Validate the clip and load your profile.",
  "sampling frames": "Choose the frames to analyze (motion-weighted).",
  "measuring motion": "Compute the objective metrics from the frames.",
  "tracking ball": "Find and link the ball across frames (heuristic or trained ONNX model — local, no tokens).",
  "estimating pose": "Detect body joints with mediapipe (local, on-device — no tokens).",
  "writing artifacts": "Render the frames + motion map the vision model reads.",
  "vision: overview": "Vision pass 1 — read the frames and pick the moments to zoom.",
  "vision: zoom": "Sample more frames inside those moments.",
  "vision: detail": "Vision pass 2 — findings with timestamps + confidence.",
  "vision: reviewing image": "One vision pass on the still image (posture only).",
  "agent writing report": "The text model writes the coaching report.",
  "agent: analyzing": "Agentic mode — the model drives the analysis.",
  "saving report": "Save the report file.",
  verifying: "A second model pass that prunes unsupported findings.",
  exporting: "Wrap-up: collect token usage, save the run's details, then write the export files (Markdown / HTML / PDF).",
  done: "Run complete.",
};
