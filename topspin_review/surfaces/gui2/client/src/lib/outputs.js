// Everything an analysis produces, grouped in plain language by what the user
// cares about. Each item carries a *friendly* provenance (`stepLabel`, `how`)
// plus the raw technical detail (`producer`, `where`) shown only behind a
// "details" toggle. Shared by the Review tabs and the first-run tour.
//
// `kind` maps to an artifact image route; items without a `kind` render via a
// dedicated component (video, charts, 3D). Items whose id is in INLINE
// (result/+page.svelte) live inside the Video view, not as tabs.

export function outputs(report) {
  const a = report?.artifacts || {};
  const m = report?.metrics || {};
  const hasPoseAngles = (m.pose || []).some((p) => p && p.l_knee != null);
  const hasPose3D = (m.pose || []).some((p) => p && p.landmarks3d);
  const hasBall3D = (m.ball?.trajectory3d || []).length > 2;
  const onnx = m.ball?.detector === "onnx-model";
  const groups = [];

  // --- Your clip --------------------------------------------------------------
  const clipItems = [
    {
      id: "video",
      label: "Video",
      stepLabel: "Your upload",
      how: "The clip you analysed, with the flagged moments marked on the timeline.",
      producer: "the uploaded file",
      where: "report.source",
      local: true,
    },
  ];
  let clips = [];
  try {
    clips = Object.entries(report?.clips || {});
  } catch {}
  if (clips.length) {
    clipItems.push({
      id: "clips",
      label: `Moment clips (${clips.length})`,
      stepLabel: "Cut after the report",
      how: "Short clips cut around each flagged moment so you can watch them back to back.",
      producer: "media.make_clips()",
      where: `${report.stem}_clips/`,
      local: true,
    });
  }
  if (a.frames) {
    clipItems.push({
      id: "frames",
      label: "Frames read",
      kind: "frames",
      stepLabel: "Rendered an image",
      how: "A few stills sampled from your clip — these are what the AI coach actually looked at.",
      producer: "imaging.contact_sheet()",
      where: a.frames.replace(/^.*[\\/]/, ""),
      local: true,
    });
  }
  groups.push({ id: "clip", group: "Your clip", items: clipItems });

  // --- Your movement ----------------------------------------------------------
  const movement = [
    {
      id: "movement",
      label: "Movement over time",
      stepLabel: "Measured your movement",
      how: "How much you moved, frame by frame — a spike is a step or a swing.",
      producer: "metrics.activity()",
      where: "report → metrics.activity",
      local: true,
    },
  ];
  if ((m.ball?.segments || []).length) {
    movement.push({
      id: "segments",
      label: "Segmentation phases",
      stepLabel: "Tracked the ball",
      how: "The clip split into rally / movement phases, found from the ball changing direction.",
      producer: "ball.phase_segments()",
      where: "report → metrics.ball.segments",
      local: true,
    });
  }
  if (a.motion) {
    movement.push({
      id: "motion",
      label: "Movement",
      kind: "motion",
      stepLabel: "Rendered an image",
      how: "A heat map of where the picture changed most — i.e. where your action happened.",
      producer: "metrics.motion_map()",
      where: a.motion.replace(/^.*[\\/]/, ""),
      local: true,
    });
  }
  if (a.heatmap) {
    movement.push({
      id: "heatmap",
      label: "Footwork",
      kind: "heatmap",
      stepLabel: "Rendered an image",
      how: "A map of where you spent the most time on court, built from your position each frame.",
      producer: "metrics.position_heatmap()",
      where: a.heatmap.replace(/^.*[\\/]/, ""),
      local: true,
    });
  }
  groups.push({ id: "movement", group: "Your movement", items: movement });

  // --- Your body --------------------------------------------------------------
  const body = [];
  if (a.pose_hero || a.pose) {
    body.push({
      id: "pose",
      label: "Body pose",
      kind: a.pose_hero ? "pose_hero" : "pose",
      stepLabel: "Detected your body",
      how: "Your skeleton detected on a frame, drawn over the video at the key moment.",
      producer: "pose.overlay() + contact sheet",
      where: (a.pose_hero || a.pose).replace(/^.*[\\/]/, ""),
      local: true,
    });
  }
  if (hasPoseAngles) {
    body.push({
      id: "pose_angles",
      label: "Body angles",
      stepLabel: "Detected your body",
      how: "How your knee and elbow angles changed through the clip — spot where they dip.",
      producer: "pose.estimate()",
      where: "report → metrics.pose",
      local: true,
    });
  }
  if (hasPose3D) {
    body.push({
      id: "pose3d",
      label: "Body 3D",
      stepLabel: "Detected your body",
      how: "A 3D reconstruction of your skeleton you can rotate. Depth is estimated, not measured.",
      producer: "pose.estimate() (world landmarks)",
      where: "report → metrics.pose[].landmarks3d",
      local: true,
    });
  }
  if (body.length) groups.push({ id: "body", group: "Your body", items: body });

  // --- The ball (outcome; least reliable signal, so it goes last) -------------
  const ball = [];
  if (a.ball) {
    ball.push({
      id: "ball",
      label: "Ball path",
      kind: "ball",
      stepLabel: "Tracked the ball",
      how: onnx
        ? "The ball's path drawn on a frame, detected by a trained AI model."
        : "The ball's path drawn on a frame, found with a colour/shape heuristic (a rough signal).",
      producer: "ball.overlay()",
      where: a.ball.replace(/^.*[\\/]/, ""),
      local: true,
    });
  }
  if (hasBall3D) {
    ball.push({
      id: "ball3d",
      label: "Ball flight",
      stepLabel: "Tracked the ball",
      how: "The ball's path in 3D — drag to rotate. Depth is estimated from the ball's apparent size.",
      producer: "ball.trajectory3d()",
      where: "report → metrics.ball.trajectory3d",
      local: true,
    });
  }
  if (ball.length) groups.push({ id: "ball", group: "The ball", items: ball });

  return groups;
}
