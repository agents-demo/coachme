// Everything an analysis produces, grouped in plain language by what the user
// cares about, with technical provenance (which step produced it, which code,
// where it lands, whether it needs tokens). Shared by the Watch tabs and the
// first-run tour. `kind` maps to an artifact image route; items without a `kind`
// render via a dedicated component (video, charts, 3D). Items whose id is in
// INLINE (in result/+page.svelte) live inside the Video view, not as tabs.

export function outputs(report) {
  const a = report?.artifacts || {};
  const m = report?.metrics || {};
  const hasPoseAngles = (m.pose || []).some((p) => p && p.l_knee != null);
  const hasPose3D = (m.pose || []).some((p) => p && p.landmarks3d);
  const hasBall3D = (m.ball?.trajectory3d || []).length > 2;
  const ballSrc = m.ball?.detector === "onnx-model" ? "trained ONNX model" : "heuristic";
  const groups = [];

  // --- Your clip --------------------------------------------------------------
  const clipItems = [
    { id: "video", label: "Video", producer: "your upload", step: "input", where: "report.source", local: true },
  ];
  let clips = [];
  try {
    clips = Object.entries(report?.clips || {});
  } catch {}
  if (clips.length) {
    clipItems.push({
      id: "clips",
      label: `Moment clips (${clips.length})`,
      producer: "media.make_clips()",
      step: "after the report",
      where: `${report.stem}_clips/`,
      local: true,
    });
  }
  if (a.frames) {
    clipItems.push({ id: "frames", label: "Frames read", kind: "frames", producer: "imaging.contact_sheet()", step: "writing artifacts", where: a.frames.replace(/^.*[\\/]/, ""), local: true });
  }
  groups.push({ id: "clip", group: "Your clip", items: clipItems });

  // --- Your movement ----------------------------------------------------------
  const movement = [
    { id: "movement", label: "Movement over time", producer: "metrics.activity()", step: "measuring motion", where: "report → metrics.activity", local: true },
  ];
  {
    const segs = m.ball?.segments || [];
    if (segs.length) {
      movement.push({ id: "segments", label: "Segmentation phases", producer: "ball.phase_segments()", step: "tracking ball", where: "report → metrics.ball.segments", local: true });
    }
  }
  if (a.motion) {
    movement.push({ id: "motion", label: "Movement", kind: "motion", producer: "metrics.motion_map()", step: "writing artifacts", where: a.motion.replace(/^.*[\\/]/, ""), local: true });
  }
  if (a.heatmap) {
    movement.push({ id: "heatmap", label: "Footwork", kind: "heatmap", producer: "metrics.position_heatmap()", step: "writing artifacts", where: a.heatmap.replace(/^.*[\\/]/, ""), local: true });
  }
  groups.push({ id: "movement", group: "Your movement", items: movement });

  // --- The ball ---------------------------------------------------------------
  const ball = [];
  if (a.ball) {
    ball.push({ id: "ball", label: "Ball path", kind: "ball", producer: `ball.overlay() · ${ballSrc}`, step: "writing artifacts", where: a.ball.replace(/^.*[\\/]/, ""), local: true });
  }
  if (hasBall3D) {
    ball.push({ id: "ball3d", label: "Ball flight", producer: "ball.trajectory3d()", step: "tracking ball", where: "report → metrics.ball.trajectory3d", local: true });
  }
  if (ball.length) groups.push({ id: "ball", group: "The ball", items: ball });

  // --- Your body --------------------------------------------------------------
  const body = [];
  if (a.pose_hero || a.pose) {
    body.push({ id: "pose", label: "Body pose", kind: a.pose_hero ? "pose_hero" : "pose", producer: "pose.overlay() + contact sheet", step: "writing artifacts", where: (a.pose_hero || a.pose).replace(/^.*[\\/]/, ""), local: true });
  }
  if (hasPoseAngles) {
    body.push({ id: "pose_angles", label: "Body angles", producer: "pose.estimate()", step: "estimating pose", where: "report → metrics.pose", local: true });
  }
  if (hasPose3D) {
    body.push({ id: "pose3d", label: "Body 3D", producer: "pose.estimate() (world landmarks)", step: "estimating pose", where: "report → metrics.pose[].landmarks3d", local: true });
  }
  if (body.length) groups.push({ id: "body", group: "Your body", items: body });

  return groups;
}
