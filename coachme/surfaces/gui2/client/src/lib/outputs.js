// Everything an analysis produces, grouped by what the user cares about. Each
// item carries two clearly separated explanations:
//   - how:    PLAIN English, for the player (no jargon).
//   - method: the full TECHNICAL method, for a developer (behind "details").
//   - detail/engine: source location + third-party engine (behind "details").
//
// Groups are separated by nature in the UI: the "clip" group (your media) renders
// on the Video tab; the rest (movement / body / ball) are the measured outputs on
// the Measurements tab. `kind` maps to an artifact image route; items without a
// `kind` render via a dedicated component (video, charts, 3D, strokes).

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
      how: "Your uploaded clip, played back here. The moments the coach pointed out are in the Key moments tab.",
      local: true,
    },
  ];
  if (a.frames) {
    clipItems.push({
      id: "frames",
      label: "Frames read",
      kind: "frames",
      stepLabel: "Drew the picture",
      how: "The handful of stills taken from your clip — the exact pictures the AI coach looked at. It favours the moments where the most happened.",
      method: "Adaptive motion-weighted sampling: ffmpeg decodes up to 64 probe frames (downscaled to 160×90); per-interval motion = mean abs grayscale diff between consecutive probes; the frame budget (default 12) is split across intervals weighted 0.3 + energy/peak; frames are placed evenly inside each interval, first and last always kept. The chosen frames are then tiled into one contact sheet (Pillow) and cached.",
      detail: "core/stages/measure/sampling.py + core/video/imaging.py · contact_sheet()",
      engine: "ffmpeg (decode) + Pillow",
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
      how: "The clip's movement energy, moment to moment — a peak is a burst of action.",
      method: "For every consecutive pair of sampled frames: downscale to 320×180 grayscale, take the mean absolute pixel difference (inside the subject region when available) as the energy; the global shift (dx, dy) between the two frames comes from FFT phase correlation.",
      detail: "core/video/metrics.py · activity()",
      engine: "NumPy",
      local: true,
    },
  ];
  if ((m.ball?.segments || []).length) {
    movement.push({
      id: "segments",
      label: "Active spans",
      stepLabel: "Tracked the ball",
      how: "Stretches where the picture stayed consistently active, separated by calmer gaps.",
      method: "Movement energy is compared against a threshold of max(median×1.3, median+0.5); contiguous spans above it become segments (≥0.4s). Each span is summarised by direction reversals along the tracked object's path (horizontal vs vertical flips).",
      detail: "core/stages/measure/ball.py · phase_segments()",
      local: true,
    });
  }
  groups.push({ id: "movement", group: "Motion", items: movement });

  // --- Maps (static spatial results of analysing the video) -------------------
  const maps = [];
  if (m.mechanics && m.mechanics.lower_lateral_range != null) {
    maps.push({
      id: "lateral",
      label: "Side-to-side movement",
      stepLabel: "Measured your movement",
      how: "How far your lower body (hips and legs) travelled left–right across the clip, as a share of the frame width.",
      method: "The lower third of the subject box (the legs) is tracked frame by frame; the horizontal spread of its centre (max − min x) is the lateral range, in fractions of the frame width. Reversals in that path are counted as direction changes.",
      detail: "core/video/metrics.py · body_regions()",
      engine: "NumPy",
      local: true,
      lateral: m.mechanics.lower_lateral_range,
      steps: m.mechanics.lower_direction_changes,
    });
  }
  if (a.motion) {
    maps.push({
      id: "motion",
      label: "Movement map",
      kind: "motion",
      stepLabel: "Drew the picture",
      how: "A heat map of where the picture changed most — red is where the action happened.",
      method: "Absolute grayscale differences between consecutive frames are summed at 640×360, restricted to the subject region, normalised by the peak, and drawn as a red overlay on the first frame.",
      detail: "core/video/metrics.py · motion_map()",
      engine: "Pillow",
      local: true,
    });
  }
  if (a.heatmap) {
    maps.push({
      id: "heatmap",
      label: "Position map",
      kind: "heatmap",
      stepLabel: "Drew the picture",
      how: "A map of where the subject spent the most time within the frame.",
      method: "2D histogram of the subject-box centre across frames, gaussian-blurred, drawn as a red overlay on frame 1.",
      detail: "core/video/metrics.py · position_heatmap()",
      engine: "Pillow",
      local: true,
    });
  }
  if (maps.length) groups.push({ id: "maps", group: "Movement", items: maps });

  // --- Your body --------------------------------------------------------------
  const body = [];
  if (a.pose_hero || a.pose) {
    body.push({
      id: "pose",
      label: "Skeleton",
      kind: a.pose_hero ? "pose_hero" : "pose",
      stepLabel: "Detected your body",
      how: "Your body drawn as a stick figure, so you can see your posture at a key moment.",
      method: "A pose model (mediapipe PoseLandmarker, lite) finds 33 body landmarks in each sampled frame; the standard skeleton connections are drawn as lines. The single 'hero' frame is the peak-motion moment; the sheet draws every sampled frame.",
      detail: "integrations/pose.py · overlay()",
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
      method: "From the 33 landmarks, joint angles are computed per frame from three points (knee = hip–knee–ankle, elbow = shoulder–elbow–wrist), plus stance width and a crouch measure. The chart plots each sampled frame; the summary reports the mean and range.",
      detail: "integrations/pose.py · estimate()",
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
      method: "The same pose model also returns world landmarks (3D, in metres). These give 3D joint angles plus torso lean and shoulder/hip twist, and the per-frame 3D points are stored so the skeleton can be drawn in 3D and rotated (orthographic projection). Depth from one camera is approximate.",
      detail: "integrations/pose.py · estimate() (world landmarks)",
      engine: "mediapipe",
      local: true,
    });
  }
  if ((m.strokes || []).length) {
    body.push({
      id: "strokes",
      label: "Fast-hand events",
      stepLabel: "Estimated pose",
      how: "Moments where a hand moved fastest, with which hand.",
      method: "Track both pose wrists (landmarks 15/16) across frames, take the faster wrist per step, pick local maxima above a relative threshold, merge within 0.4s, and guess the dominant hand.",
      detail: "core/stages/measure/strokes.py · segment()",
      engine: "mediapipe",
      local: true,
    });
  }
  if (body.length) groups.push({ id: "body", group: "Pose", items: body });

  // --- The ball (outcome; least reliable signal, so it goes last) -------------
  const ball = [];
  if (a.ball) {
    ball.push({
      id: "ball",
      label: "Object path",
      kind: "ball",
      stepLabel: "Tracked the object",
      how: onnx
        ? "The route the tracked object took, found automatically and drawn over a frame. A rough guide."
        : "The route the tracked object took, drawn over a frame. A rough guide — small fast objects are hard to track reliably.",
      method: onnx
        ? "A trained YOLO detector (ONNX, letterboxed to 640, class-agnostic NMS) finds the object in each frame; a constant-velocity nearest-neighbour tracker links detections (max jump 0.16, tolerating 2 missed frames, tracks of ≥3 points). The main track is drawn over the middle frame."
        : "Each frame is masked for bright, round-ish warm/white blobs (small colour+shape criteria, optionally confirmed by OpenCV Hough circles); a constant-velocity nearest-neighbour tracker links them (max jump 0.16, tolerating 2 missed frames, tracks of ≥3 points), and the main track is drawn over the middle frame.",
      detail: onnx ? "integrations/ballmodel.py · detect()" : "core/stages/measure/ball.py · candidates()",
      engine: onnx ? "onnxruntime" : "NumPy",
      local: true,
    });
  } else {
    ball.push({
      id: "ball",
      label: "Object path",
      stepLabel: "Tracked the object",
      how: "No small moving object detected in this clip — automatic tracking is hard here.",
      method: onnx
        ? "A trained YOLO detector (ONNX) ran on every sampled frame, but no stable track formed (needs ≥3 linked points)."
        : "Bright, round-ish blob detection ran on every frame, but no stable track formed (needs ≥3 linked points).",
      detail: onnx ? "integrations/ballmodel.py · detect()" : "core/stages/measure/ball.py · candidates()",
      engine: onnx ? "onnxruntime" : "NumPy",
      local: true,
    });
  }
  if (hasBall3D) {
    ball.push({
      id: "ball3d",
      label: "Object trajectory",
      stepLabel: "Tracked the object",
      how: "The object's route in 3D. The shape is useful; the exact distances aren't.",
      method: "Each tracked point gets a depth estimate z = sqrt(median_blob_area / blob_area) — a bigger blob is nearer (a monocular size cue) — combined with its screen (x, y) to plot a 3D path you can rotate. The direction of depth is meaningful; the absolute distance is not.",
      detail: "core/stages/measure/ball.py · trajectory3d()",
      local: true,
    });
  }
  groups.push({ id: "ball", group: "Tracked object", items: ball });

  return groups;
}
