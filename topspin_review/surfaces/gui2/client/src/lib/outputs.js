// Technical provenance for everything an analysis produces: which pipeline step
// made it, which code produced it, where it lands, and whether it needs tokens.
// Shared by the Watch tabs, the "produced by" card, and the first-run tour.
// `kind` maps to an artifact image route; items without a `kind` are rendered by
// a dedicated component (video, charts, 3D).

export function outputs(report) {
  const a = report?.artifacts || {};
  const m = report?.metrics || {};
  const hasPoseAngles = (m.pose || []).some((p) => p && p.l_knee != null);
  const hasPose3D = (m.pose || []).some((p) => p && p.landmarks3d);
  const hasBall3D = (m.ball?.trajectory3d || []).length > 2;
  const groups = [];

  // Which detector produced the ball track (heuristic vs trained model).
  const ballSrc = m.ball?.detector === "onnx-model" ? "trained ONNX model" : "heuristic";

  groups.push({
    group: "Input",
    items: [
      {
        id: "video",
        label: "Video",
        producer: "your upload",
        step: "input (not produced)",
        where: "report.source",
        local: true,
      },
    ],
  });

  // Numbers + charts computed during the measure steps (no tokens).
  groups.push({
    group: "Measured (on-device, no tokens)",
    items: [
      {
        id: "movement",
        label: "Movement over time",
        producer: "metrics.activity()",
        step: "measuring motion",
        where: "report → metrics.activity",
        local: true,
      },
      {
        id: "segments",
        label: "Segmentation phases",
        producer: "ball.phase_segments()",
        step: "tracking ball",
        where: "report → metrics.ball.segments",
        local: true,
      },
      ...(hasPoseAngles
        ? [
            {
              id: "pose_angles",
              label: "Body angles",
              producer: "pose.estimate()",
              step: "estimating pose",
              where: "report → metrics.pose",
              local: true,
            },
          ]
        : []),
      ...(hasPose3D
        ? [
            {
              id: "pose3d",
              label: "Body 3D",
              producer: "pose.estimate() (world landmarks)",
              step: "estimating pose",
              where: "report → metrics.pose[].landmarks3d",
              local: true,
            },
          ]
        : []),
      ...(hasBall3D
        ? [
            {
              id: "ball3d",
              label: "Ball flight (3D)",
              producer: "ball.trajectory3d()",
              step: "tracking ball",
              where: "report → metrics.ball.trajectory3d",
              local: true,
            },
          ]
        : []),
    ],
  });

  // Image artifacts, all rendered together in one step (no tokens).
  const rendered = [];
  if (a.motion) {
    rendered.push({
      id: "motion",
      label: "Movement map",
      kind: "motion",
      producer: "metrics.motion_map()",
      step: "writing artifacts",
      where: `${a.motion.replace(/^.*[\\/]/, "")}`,
      local: true,
    });
  }
  if (a.heatmap) {
    rendered.push({
      id: "heatmap",
      label: "Footwork map",
      kind: "heatmap",
      producer: "metrics.position_heatmap()",
      step: "writing artifacts",
      where: `${a.heatmap.replace(/^.*[\\/]/, "")}`,
      local: true,
    });
  }
  if (a.ball) {
    rendered.push({
      id: "ball",
      label: "Ball path",
      kind: "ball",
      producer: `ball.overlay() · ${ballSrc}`,
      step: "writing artifacts",
      where: `${a.ball.replace(/^.*[\\/]/, "")}`,
      local: true,
    });
  }
  if (a.pose_hero || a.pose) {
    rendered.push({
      id: "pose",
      label: "Body pose",
      kind: a.pose_hero ? "pose_hero" : "pose",
      producer: "pose.overlay() + contact sheet",
      step: "writing artifacts",
      where: `${(a.pose_hero || a.pose).replace(/^.*[\\/]/, "")}`,
      local: true,
    });
  }
  if (a.frames) {
    rendered.push({
      id: "frames",
      label: "Frames read",
      kind: "frames",
      producer: "imaging.contact_sheet()",
      step: "writing artifacts",
      where: `${a.frames.replace(/^.*[\\/]/, "")}`,
      local: true,
    });
  }
  if (rendered.length) groups.push({ group: "Rendered images (on-device, no tokens)", items: rendered });

  // Cut from the clip after the report is written.
  let clips = [];
  try {
    clips = Object.entries(report?.clips || {});
  } catch {}
  if (clips.length) {
    groups.push({
      group: "Cut from the clip",
      items: [
        {
          id: "clips",
          label: `Moment clips (${clips.length})`,
          producer: "media.make_clips()",
          step: "after the report (post step)",
          where: `${report.stem}_clips/`,
          local: true,
        },
      ],
    });
  }

  return groups;
}
