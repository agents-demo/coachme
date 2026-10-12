// Everything an analysis produces, grouped by what the user cares about. Each
// item carries two clearly separated explanations:
//   - how:    PLAIN English, one line, for the player (no jargon).
//   - method: the TECHNICAL method, for a developer (shown behind "details").
//   - detail/engine: source location + third-party engine (behind "details").
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
      how: "Your clip as you uploaded it. The moments worth a look are marked on the timeline.",
      method: "n/a — this is your input file.",
      detail: "input · the file you uploaded",
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
      how: "A short clip around each flagged moment, so you can watch the key bits back to back.",
      method: "ffmpeg: trim ±window around each flagged timestamp, re-encode to a uniform size, concatenate.",
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
      how: "The few stills taken from your clip — the exact pictures the AI coach looked at. It picks the moments where the most happened.",
      method: "Motion-weighted sampling: per-frame grayscale abs-diff energy → keep the top frames up to a cap → tile into a contact sheet.",
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
      how: "How much you moved through the clip. Higher bar = more movement (a step or a swing).",
      method: "Per frame-pair: mean abs grayscale diff inside the subject mask (energy); inter-frame shift via FFT phase correlation.",
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
      how: "The clip split into parts where you were rallying vs. just moving, based on when the ball changed direction.",
      method: "Reverse points along the ball track (x-flip = hit, y-flip = bounce); label contiguous spans above a noise threshold.",
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
      how: "A heat map of where the picture changed most — red is where your action happened.",
      method: "Sum consecutive-frame abs grayscale diff, masked to the subject, normalised, drawn as a red overlay on frame 1.",
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
      how: "A map of the court: red is where you stood the most.",
      method: "2D histogram of the subject-box centre across frames, gaussian-blurred, drawn as a red overlay on frame 1.",
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
      how: "Your body drawn as a stick figure, so you can see your posture at a key moment.",
      method: "Pose model → 33 body landmarks per frame; join the landmark pairs to draw the skeleton.",
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
      how: "Your knee and elbow angles through the clip — watch for them dipping during a shot.",
      method: "Three-point joint angles from landmarks (e.g. hip–knee–ankle) computed per frame and plotted over time.",
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
      how: "Your body as a 3D model you can spin around. Depth is a best guess from a single camera.",
      method: "Pose model's world landmarks (metres) projected orthographically; render with rotate controls.",
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
        ? "The route the ball took, found automatically and drawn over a frame. A rough guide."
        : "The route the ball took, drawn over a frame. A rough guide — the ball is hard to track.",
      method: onnx
        ? "Trained YOLO detector per frame → constant-velocity nearest-neighbour tracker → path overlay."
        : "Colour/shape blob detector per frame → nearest-neighbour tracker → path overlay.",
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
      how: "The ball's route through the air in 3D. The shape is useful; the exact distances aren't.",
      method: "Depth z ∝ 1/√(blob area) (monocular size cue) combined with screen (x, y); plot (x, y, z) with rotate controls.",
      detail: "our code · core/stages/measure/ball.py · trajectory3d()",
      local: true,
    });
  }
  if (ball.length) groups.push({ id: "ball", group: "The ball", items: ball });

  return groups;
}
