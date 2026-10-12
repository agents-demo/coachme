// Everything an analysis produces, grouped in plain language by what the user
// cares about. Each item carries:
//   - how:    a one-line description of the ALGORITHM / method (the interesting part)
//   - stepLabel: the pipeline step it belongs to (friendly)
//   - detail: the source location + engine, shown only behind a "details" toggle
// Shared by the Review tabs and the first-run tour.
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
      how: "The clip you analysed — nothing is computed for it. The flagged moments are marked on the timeline.",
      detail: "Input · the file you uploaded",
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
      how: "For each flagged moment, a short window around its timestamp is cut out and re-encoded to a common size, so they play back to back.",
      detail: "our code · integrations/media.py · make_clips()",
      engine: "ffmpeg",
      local: true,
    });
  }
  if (a.frames) {
    clipItems.push({
      id: "frames",
      label: "Frames read",
      kind: "frames",
      stepLabel: "Rendered an image",
      how: "How the video becomes stills: the clip is probed for movement and the busiest moments are sampled (up to a cap), then tiled into one sheet — these are the stills the AI coach actually reads.",
      detail: "our code · core/video/imaging.py · contact_sheet()",
      engine: "Pillow",
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
      how: "For each pair of sampled frames, the average pixel change (restricted to your body) is measured — that's the movement energy; the global shift comes from phase correlation of the two frames.",
      detail: "our code · core/video/metrics.py · activity()",
      engine: "NumPy",
      local: true,
    },
  ];
  if ((m.ball?.segments || []).length) {
    movement.push({
      id: "segments",
      label: "Segmentation phases",
      stepLabel: "Tracked the ball",
      how: "The tracked ball's direction changes are found (a horizontal flip = a hit, a vertical flip = a bounce); stretches where movement stays above the pause level are labelled as rally / movement.",
      detail: "our code · core/stages/measure/ball.py · phase_segments()",
      local: true,
    });
  }
  if (a.motion) {
    movement.push({
      id: "motion",
      label: "Movement",
      kind: "motion",
      stepLabel: "Rendered an image",
      how: "Pixel differences between consecutive frames are summed, restricted to your body, normalised, and drawn as a red heat map over the first frame — red = where the picture changed most.",
      detail: "our code · core/video/metrics.py · motion_map()",
      engine: "Pillow",
      local: true,
    });
  }
  if (a.heatmap) {
    movement.push({
      id: "heatmap",
      label: "Footwork",
      kind: "heatmap",
      stepLabel: "Rendered an image",
      how: "Your position in every frame is dropped into a coarse grid, the grid is blurred, and it's drawn as a red heat map over the first frame — red = where you spent the most time.",
      detail: "our code · core/video/metrics.py · position_heatmap()",
      engine: "Pillow",
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
      how: "A pose model finds 33 body points (shoulders, elbows, hips, knees…) in each frame; they're joined with lines to draw your skeleton.",
      detail: "our code · integrations/pose.py · overlay()",
      engine: "mediapipe",
      local: true,
    });
  }
  if (hasPoseAngles) {
    body.push({
      id: "pose_angles",
      label: "Body angles",
      stepLabel: "Detected your body",
      how: "From the body points, joint angles are computed each frame (e.g. the angle between hip–knee and knee–ankle) and plotted over time.",
      detail: "our code · integrations/pose.py · estimate()",
      engine: "mediapipe",
      local: true,
    });
  }
  if (hasPose3D) {
    body.push({
      id: "pose3d",
      label: "Body 3D",
      stepLabel: "Detected your body",
      how: "The pose model also estimates each point's 3D position (in metres); the skeleton is drawn in 3D so you can rotate it. Depth is estimated from one camera, so treat it as an indicator.",
      detail: "our code · integrations/pose.py · estimate() (world landmarks)",
      engine: "mediapipe",
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
        ? "A trained detector finds the ball in each frame; a constant-velocity tracker links the detections into a path, which is drawn over a frame."
        : "Bright, round-ish blobs are found in each frame; a nearest-neighbour tracker links them into a path, which is drawn over a frame (a rough signal).",
      detail: onnx ? "our code · integrations/ballmodel.py · detect()" : "our code · core/stages/measure/ball.py · candidates()",
      engine: onnx ? "onnxruntime" : "NumPy",
      local: true,
    });
  }
  if (hasBall3D) {
    ball.push({
      id: "ball3d",
      label: "Ball flight",
      stepLabel: "Tracked the ball",
      how: "Depth is inferred from the ball's apparent size (bigger = nearer) and combined with its screen position to plot a 3D path you can rotate. Direction of depth is meaningful; distance is not.",
      detail: "our code · core/stages/measure/ball.py · trajectory3d()",
      local: true,
    });
  }
  if (ball.length) groups.push({ id: "ball", group: "The ball", items: ball });

  return groups;
}
