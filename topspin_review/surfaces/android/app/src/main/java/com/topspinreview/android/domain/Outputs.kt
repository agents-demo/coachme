package com.topspinreview.android.domain

/** Technical provenance for each measured item (ported from `outputs.js`). */
object Outputs {
    data class Info(val method: String, val detail: String, val engine: String)

    val movement = Info(
        "For every consecutive pair of sampled frames: downscale to 320×180 grayscale, take the mean absolute pixel difference (inside the subject region when available) as the energy; the global shift (dx, dy) comes from a phase-correlation estimate.",
        "core/video/metrics.py · activity()",
        "NumPy",
    )
    val segments = Info(
        "Movement energy is compared against a threshold of max(median×1.3, median+0.5); contiguous spans above it become segments (≥0.4s). Each span is summarised by direction reversals along the tracked object's path.",
        "core/stages/measure/ball.py · phase_segments()",
        "—",
    )
    val lateral = Info(
        "The lower third of the subject box (the legs) is tracked frame by frame; the horizontal spread of its centre (max − min x) is the lateral range. Reversals in that path are counted as direction changes.",
        "core/video/metrics.py · body_regions()",
        "NumPy",
    )
    val motionMap = Info(
        "Absolute grayscale differences between consecutive frames are summed at 640×360, restricted to the subject region, normalised by the peak, and drawn as a red overlay on the first frame.",
        "core/video/metrics.py · motion_map()",
        "Pillow",
    )
    val positionMap = Info(
        "2D histogram of the subject-box centre across frames, gaussian-blurred, drawn as a red overlay on frame 1.",
        "core/video/metrics.py · position_heatmap()",
        "Pillow",
    )
    val skeleton = Info(
        "A pose model (mediapipe PoseLandmarker, lite) finds 33 body landmarks in each sampled frame; the standard skeleton connections are drawn as lines.",
        "integrations/pose.py · overlay()",
        "mediapipe",
    )
    val angles = Info(
        "From the 33 landmarks, joint angles are computed per frame from three points (knee = hip–knee–ankle, elbow = shoulder–elbow–wrist), plus stance width and a crouch measure.",
        "integrations/pose.py · estimate()",
        "mediapipe",
    )
    val pose3d = Info(
        "The same pose model returns world landmarks (3D, in metres) → 3D joint angles plus torso lean and shoulder/hip twist; drawn in 3D (orthographic projection). Depth from one camera is approximate.",
        "integrations/pose.py · estimate() (world landmarks)",
        "mediapipe",
    )
    val strokes = Info(
        "Track both pose wrists (landmarks 15/16) across frames, take the faster wrist per step, pick local maxima above a relative threshold, merge within 0.4s, and guess the dominant hand.",
        "core/stages/measure/strokes.py · segment()",
        "mediapipe",
    )
    val objectPath = Info(
        "A trained YOLO detector (ONNX, letterboxed to 640, class-agnostic NMS) finds the object in each frame; a constant-velocity nearest-neighbour tracker links detections (max jump 0.16, tolerating 2 missed frames, tracks ≥3 points). The main track is drawn over the middle frame.",
        "integrations/ballmodel.py · detect()",
        "onnxruntime",
    )
    val trajectory3d = Info(
        "Each tracked point gets a depth estimate z = sqrt(median_blob_area / blob_area) — a bigger blob is nearer (a monocular size cue) — combined with its screen (x, y) to plot a 3D path you can rotate. The direction of depth is meaningful; the absolute distance is not.",
        "core/stages/measure/ball.py · trajectory3d()",
        "—",
    )
    val framesRead = Info(
        "Adaptive motion-weighted sampling: decode up to 64 probe frames (downscaled to 160×90); per-interval motion = mean abs grayscale diff; the frame budget is split across intervals weighted 0.3 + energy/peak; first and last always kept; the chosen frames are tiled into one contact sheet.",
        "core/stages/measure/sampling.py + core/video/imaging.py · contact_sheet()",
        "ffmpeg + Pillow",
    )
}
