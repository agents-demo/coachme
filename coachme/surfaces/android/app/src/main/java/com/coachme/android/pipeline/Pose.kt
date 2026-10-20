package com.coachme.android.pipeline

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.sqrt

/**
 * Pose, ported from `integrations/pose.py` (MediaPipe Tasks PoseLandmarker, lite).
 * Produces per-frame 2D + world landmarks, joint angles and 3D summaries.
 */
class Pose(context: Context) {
    private val landmarker: PoseLandmarker = PoseLandmarker.createFromOptions(
        context,
        PoseLandmarker.PoseLandmarkerOptions.builder()
            .setBaseOptions(BaseOptions.builder().setModelAssetPath("pose_landmarker_lite.task").build())
            .setRunningMode(RunningMode.IMAGE)
            .setNumPoses(1)
            .setMinPoseDetectionConfidence(0.5f)
            .setMinPosePresenceConfidence(0.5f)
            .setMinTrackingConfidence(0.5f)
            .build(),
    )

    /** Landmarks per frame: `[x,y,z,vis]` (x,y normalized; z relative), and world `[x,y,z]` metres. */
    data class PoseFrame(val lm: List<FloatArray>?, val world: List<FloatArray>?)

    fun detect(frames: List<Sampler.Frame>): List<PoseFrame> = frames.map { f ->
        runCatching {
            val res = landmarker.detect(BitmapImageBuilder(f.bitmap).build())
            val lm = res.landmarks().firstOrNull()?.map { floatArrayOf(it.x(), it.y(), it.z(), it.visibility().orElse(0f)) }
            val w = res.worldLandmarks().firstOrNull()?.map { floatArrayOf(it.x(), it.y(), it.z()) }
            PoseFrame(lm, w)
        }.getOrElse { PoseFrame(null, null) }
    }

    // --- summaries --------------------------------------------------------------

    fun summarize(poses: List<PoseFrame>): JsonObject {
        val lk = avgAngle(poses, 23, 25, 27); val rk = avgAngle(poses, 24, 26, 28)
        val le = avgAngle(poses, 11, 13, 15); val re = avgAngle(poses, 12, 14, 16)
        return buildJsonObject {
            lk?.let { put("l_knee_mean", round(it)) }; rk?.let { put("r_knee_mean", round(it)) }
            le?.let { put("l_elbow_mean", round(it)) }; re?.let { put("r_elbow_mean", round(it)) }
        }
    }

    fun summarize3d(poses: List<PoseFrame>): JsonObject {
        val leans = poses.mapNotNull { torsoLean(it.world) }
        val twists = poses.mapNotNull { twist(it.world) }
        return buildJsonObject {
            leans.takeIf { it.isNotEmpty() }?.let { put("torso_lean_mean", round(it.average())) }
            twists.takeIf { it.isNotEmpty() }?.let { put("shoulder_hip_twist_mean", round(it.average())) }
        }
    }

    /** Per-frame world landmarks (3D), for the Body 3D view. */
    fun series3d(poses: List<PoseFrame>): JsonArray = buildJsonArray {
        poses.forEach { p ->
            val w = p.world
            if (w == null) add(kotlinx.serialization.json.JsonNull)
            else add(buildJsonArray {
                w.forEach { lm ->
                    add(buildJsonArray { add(JsonPrimitive(lm[0].toDouble())); add(JsonPrimitive(lm[1].toDouble())); add(JsonPrimitive(lm[2].toDouble())) })
                }
            })
        }
    }

    /** Per-frame joint angles (degrees), for the pose-angle chart. */
    fun anglesSeries(poses: List<PoseFrame>, times: List<Double>): JsonArray = buildJsonArray {
        poses.forEachIndexed { i, p ->
            val lm = p.lm
            if (lm == null || lm.size <= 28) add(kotlinx.serialization.json.JsonNull)
            else add(buildJsonObject {
                put("t", round(times.getOrElse(i) { i.toDouble() }, 2))
                put("l_knee", round(angle(lm[23], lm[25], lm[27])))
                put("r_knee", round(angle(lm[24], lm[26], lm[28])))
                put("l_elbow", round(angle(lm[11], lm[13], lm[15])))
                put("r_elbow", round(angle(lm[12], lm[14], lm[16])))
            })
        }
    }

    /** Fast-hand events (appendix · strokes.py): wrist-speed local maxima. */
    fun strokes(poses: List<PoseFrame>, frames: List<Sampler.Frame>, relThreshold: Double = 0.35, minGap: Double = 0.4): JsonArray {
        val speed = DoubleArray(poses.size)
        val hand = arrayOfNulls<String>(poses.size)
        for (i in 1 until poses.size) {
            val a = poses[i - 1].lm; val b = poses[i].lm
            if (a == null || b == null) continue
            val lw = dist(a[15], b[15]); val rw = dist(a[16], b[16])
            val faster = if (lw >= rw) "left" else "right"
            speed[i] = maxOf(lw, rw); hand[i] = faster
        }
        val peak = speed.maxOrNull() ?: 0.0
        if (peak <= 0.0) return JsonArray(emptyList())
        val threshold = peak * relThreshold
        val events = arrayListOf<Triple<Double, String, Double>>()
        for (i in 1 until speed.size - 1) {
            if (speed[i] >= threshold && speed[i] >= speed[i - 1] && speed[i] >= speed[i + 1]) {
                events.add(Triple(frames[i].t, hand[i] ?: "?", speed[i]))
            }
        }
        val merged = arrayListOf<Triple<Double, String, Double>>()
        for (e in events) {
            val last = merged.lastOrNull()
            if (last != null && e.first - last.first < minGap) {
                if (e.third > last.third) merged[merged.size - 1] = e
            } else merged.add(e)
        }
        return buildJsonArray {
            merged.forEach { (t, h, s) ->
                add(buildJsonObject { put("t", round(t)); put("hand", h); put("strength", round(s, 3)) })
            }
        }
    }

    /** Coarse footwork from the pose ankles (appendix · metrics.footwork). */
    fun footwork(poses: List<PoseFrame>): JsonObject {
        val xs = ArrayList<Double>(); val ys = ArrayList<Double>()
        poses.forEach { p ->
            val lm = p.lm
            if (lm == null || lm.size <= 28) return@forEach
            xs.add(((lm[27][0] + lm[28][0]) / 2).toDouble())
            ys.add(((lm[27][1] + lm[28][1]) / 2).toDouble())
        }
        if (xs.size < 3) return JsonObject(emptyMap())
        val dx = (1 until xs.size).map { xs[it] - xs[it - 1] }
        var steps = 0
        for (i in 1 until dx.size) if (dx[i] * dx[i - 1] < 0 && abs(dx[i]) > 0.01) steps++
        var hops = 0
        for (i in 1 until ys.size - 1) if (ys[i] <= ys[i - 1] && ys[i] <= ys[i + 1] && (minOf(ys[i - 1], ys[i + 1]) - ys[i]) > 0.015) hops++
        return buildJsonObject {
            put("steps", steps); put("hops", hops)
            put("base_travel", round(xs.maxOrNull()!! - xs.minOrNull()!!))
        }
    }

    // --- overlay ----------------------------------------------------------------

    fun overlay(frames: List<Sampler.Frame>, poses: List<PoseFrame>): Bitmap? {
        val base = frames.firstOrNull()?.bitmap ?: return null
        val out = base.copy(Bitmap.Config.ARGB_8888, true)
        val c = Canvas(out)
        val paint = Paint().apply { color = Color.rgb(52, 211, 153); strokeWidth = 4f; isAntiAlias = true }
        val w = out.width.toFloat(); val h = out.height.toFloat()
        poses.forEach { p ->
            val lm = p.lm ?: return@forEach
            for ((a, b) in SKELETON) {
                if (a >= lm.size || b >= lm.size) continue
                c.drawLine(lm[a][0] * w, lm[a][1] * h, lm[b][0] * w, lm[b][1] * h, paint)
            }
        }
        return out
    }

    private fun avgAngle(poses: List<PoseFrame>, a: Int, b: Int, c: Int): Double? {
        val vals = poses.mapNotNull { p ->
            val lm = p.lm ?: return@mapNotNull null
            if (lm.size <= maxOf(a, b, c)) return@mapNotNull null
            angle(lm[a], lm[b], lm[c])
        }
        return vals.takeIf { it.isNotEmpty() }?.average()
    }

    private fun angle(a: FloatArray, b: FloatArray, c: FloatArray): Double {
        val ang = Math.toDegrees(
            atan2((c[1] - b[1]).toDouble(), (c[0] - b[0]).toDouble()) -
                atan2((a[1] - b[1]).toDouble(), (a[0] - b[0]).toDouble())
        )
        val v = abs(ang)
        return if (v > 180) 360 - v else v
    }

    private fun torsoLean(world: List<FloatArray>?): Double? {
        if (world == null || world.size <= 24) return null
        val shoulderMid = mid(world[11], world[12]); val hipMid = mid(world[23], world[24])
        return abs(Math.toDegrees(atan2((shoulderMid[0] - hipMid[0]).toDouble(), (hipMid[1] - shoulderMid[1]).toDouble())))
    }

    private fun twist(world: List<FloatArray>?): Double? {
        if (world == null || world.size <= 24) return null
        val sh = Math.toDegrees(atan2((world[12][2] - world[11][2]).toDouble(), (world[12][0] - world[11][0]).toDouble()))
        val hip = Math.toDegrees(atan2((world[24][2] - world[23][2]).toDouble(), (world[24][0] - world[23][0]).toDouble()))
        return abs(sh - hip)
    }

    private fun mid(a: FloatArray, b: FloatArray) = floatArrayOf((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
    private fun dist(a: FloatArray, b: FloatArray): Double {
        val dx = (a[0] - b[0]).toDouble(); val dy = (a[1] - b[1]).toDouble()
        return sqrt(dx * dx + dy * dy)
    }

    private fun round(v: Double, dp: Int = 1): Double = Math.round(v * POW2[dp]) / POW2[dp]
    private val POW2 = doubleArrayOf(1.0, 10.0, 100.0, 1000.0)

    private companion object {
        val SKELETON = arrayOf(
            11 to 12, 11 to 13, 13 to 15, 12 to 14, 14 to 16,
            11 to 23, 12 to 24, 23 to 24, 23 to 25, 25 to 27, 24 to 26, 26 to 28,
        )
    }
}
