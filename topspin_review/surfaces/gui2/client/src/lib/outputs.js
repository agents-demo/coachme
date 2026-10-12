// Plain-language catalog of everything an analysis produces, grouped by what the
// user cares about. Shared by the Watch tabs, the "what this session produced"
// card, and the first-run tour. `kind` maps to an artifact image route; items
// without a `kind` are rendered by a dedicated component (video, charts, 3D).

export function outputs(report) {
  const a = report?.artifacts || {};
  const m = report?.metrics || {};
  const hasPoseAngles = (m.pose || []).some((p) => p && p.l_knee != null);
  const hasPose3D = (m.pose || []).some((p) => p && p.landmarks3d);
  const hasBall3D = (m.ball?.trajectory3d || []).length > 2;
  const groups = [];

  groups.push({
    group: "Your clip",
    items: [
      {
        id: "video",
        label: "Video",
        what: "Your clip, with the moments the coach flagged.",
        why: "Click a moment to jump there; step frame-by-frame to study it.",
      },
    ],
  });

  const movement = [];
  if (a.motion) {
    movement.push({
      id: "motion",
      label: "Movement",
      kind: "motion",
      what: "A map of where the picture changed most.",
      why: "Shows where your action happened in the frame.",
    });
  }
  if (a.heatmap) {
    movement.push({
      id: "heatmap",
      label: "Footwork",
      kind: "heatmap",
      what: "Where you spent the most time on court.",
      why: "See if you stay stuck in one spot.",
    });
  }
  if (movement.length) groups.push({ group: "Your movement", items: movement });

  const ball = [];
  if (a.ball) {
    ball.push({
      id: "ball",
      label: "Ball path",
      kind: "ball",
      what: "The path traced for the ball across the clip.",
      why: "A rough signal of the rally — not a precise measurement.",
    });
  }
  if (hasBall3D) {
    ball.push({
      id: "ball3d",
      label: "Ball flight",
      what: "The ball's path in 3D.",
      why: "Drag to rotate and see the flight shape.",
    });
  }
  if (ball.length) groups.push({ group: "The ball", items: ball });

  const body = [];
  if (a.pose_hero || a.pose) {
    body.push({
      id: "pose",
      label: "Body pose",
      kind: a.pose_hero ? "pose_hero" : "pose",
      what: "Your skeleton drawn on a frame.",
      why: "Check your posture at the key moment.",
    });
  }
  if (hasPoseAngles) {
    body.push({
      id: "pose_angles",
      label: "Body angles",
      what: "How your joints bend over the clip.",
      why: "See where a knee or elbow dips during the stroke.",
    });
  }
  if (hasPose3D) {
    body.push({
      id: "pose3d",
      label: "Body 3D",
      what: "Your skeleton in 3D.",
      why: "Drag to rotate and inspect your shape.",
    });
  }
  if (body.length) groups.push({ group: "Your body", items: body });

  const images = [];
  if (a.frames) {
    images.push({
      id: "frames",
      label: "Frames read",
      kind: "frames",
      what: "The stills the coach looked at.",
      why: "The visual evidence behind the report.",
    });
  }
  if (images.length) groups.push({ group: "What the coach saw", items: images });

  return groups;
}
