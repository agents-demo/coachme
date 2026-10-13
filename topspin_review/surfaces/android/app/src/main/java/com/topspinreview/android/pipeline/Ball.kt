package com.topspinreview.android.pipeline

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.nio.FloatBuffer
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

/**
 * Ball detection (ONNX YOLOv5, single class) + constant-velocity tracker, ported from
 * `core/stages/measure/ball.py` + `integrations/ballmodel.py` (Appendix B/L10).
 */
class Ball(private val context: Context) {
    private val env: OrtEnvironment = OrtEnvironment.getEnvironment()
    private val session: OrtSession by lazy {
        val bytes = context.assets.open("ball.onnx").use { it.readBytes() }
        env.createSession(bytes, OrtSession.SessionOptions())
    }

    data class Detection(val cx: Double, val cy: Double, val w: Double, val h: Double, val score: Double)

    private data class TrackPoint(val frame: Int, val cx: Double, val cy: Double, val area: Double)

    /** Detections per frame (normalized to the video frame). */
    fun detect(frames: List<Sampler.Frame>, conf: Double = 0.25, iou: Double = 0.45): List<List<Detection>> =
        frames.map { rawDetect(it.bitmap, conf, iou) }

    private fun rawDetect(bmp: Bitmap, conf: Double, iou: Double): List<Detection> {
        val size = 640
        val scale = min(size.toDouble() / bmp.width, size.toDouble() / bmp.height)
        val nw = (bmp.width * scale).toInt(); val nh = (bmp.height * scale).toInt()
        val dx = (size - nw) / 2; val dy = (size - nh) / 2
        val canvas = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        Canvas(canvas).apply { drawColor(Color.rgb(114, 114, 114)); drawBitmap(Bitmap.createScaledBitmap(bmp, nw, nh, true), dx.toFloat(), dy.toFloat(), null) }
        val px = IntArray(size * size); canvas.getPixels(px, 0, size, 0, 0, size, size)
        val chw = FloatArray(3 * size * size)
        for (i in px.indices) {
            val p = px[i]
            chw[i] = ((p shr 16) and 0xff) / 255f
            chw[size * size + i] = ((p shr 8) and 0xff) / 255f
            chw[2 * size * size + i] = (p and 0xff) / 255f
        }
        val input = OnnxTensor.createTensor(env, FloatBuffer.wrap(chw), longArrayOf(1, 3, size.toLong(), size.toLong()))
        val name = session.inputNames.first()
        val out = input.use { tensor ->
            session.run(mapOf(name to tensor)).use { result ->
                @Suppress("UNCHECKED_CAST")
                (result[0].value as Array<Array<FloatArray>>)[0]
            }
        }
        val dets = ArrayList<Detection>()
        for (row in out) {
            val score = row[4]
            if (score < conf) continue
            // YOLOv5: cx, cy, w, h (pixels in 640 space)
            val cx = row[0]; val cy = row[1]; val w = row[2]; val h = row[3]
            dets.add(Detection(cx = cx.toDouble(), cy = cy.toDouble(), w = w.toDouble(), h = h.toDouble(), score = score.toDouble()))
        }
        // NMS
        val kept = ArrayList<Detection>()
        for (d in dets.sortedByDescending { it.score }) {
            if (kept.none { iou(it, d) > iou }) kept.add(d)
        }
        // Undo letterbox → normalized frame coords
        return kept.map {
            Detection(
                cx = ((it.cx - dx) / nw).coerceIn(0.0, 1.0),
                cy = ((it.cy - dy) / nh).coerceIn(0.0, 1.0),
                w = it.w / nw, h = it.h / nh, score = it.score,
            )
        }
    }

    private fun iou(a: Detection, b: Detection): Double {
        val ax1 = a.cx - a.w / 2; val ay1 = a.cy - a.h / 2; val ax2 = a.cx + a.w / 2; val ay2 = a.cy + a.h / 2
        val bx1 = b.cx - b.w / 2; val by1 = b.cy - b.h / 2; val bx2 = b.cx + b.w / 2; val by2 = b.cy + b.h / 2
        val ix = max(0.0, min(ax2, bx2) - max(ax1, bx1)); val iy = max(0.0, min(ay2, by2) - max(ay1, by1))
        val inter = ix * iy
        val union = a.w * a.h + b.w * b.h - inter
        return if (union <= 0) 0.0 else inter / union
    }

    /**
     * Link detections into the main track (constant velocity, max jump 0.16, tolerate 2 misses,
     * keep tracks ≥3 points and travel ≥0.05), then summarise.
     */
    fun process(times: List<Double>, dets: List<List<Detection>>, activity: List<Pair<Double, Double>>): JsonObject {
        data class T(val pts: MutableList<TrackPoint>, var vx: Double = 0.0, var vy: Double = 0.0, var missed: Int = 0)
        val tracks = ArrayList<T>()
        val finished = ArrayList<T>()
        for (i in dets.indices) {
            val remaining = dets[i].toMutableList()
            for (t in tracks) {
                val last = t.pts.last()
                val predX = last.cx + t.vx; val predY = last.cy + t.vy
                val best = remaining.minByOrNull { abs(it.cx - predX) + abs(it.cy - predY) }
                if (best != null && abs(best.cx - predX) + abs(best.cy - predY) <= 0.16) {
                    val dx = best.cx - last.cx; val dy = best.cy - last.cy
                    t.vx = if (t.pts.size == 1) dx else 0.6 * dx + 0.4 * t.vx
                    t.vy = if (t.pts.size == 1) dy else 0.6 * dy + 0.4 * t.vy
                    t.pts.add(TrackPoint(i, best.cx, best.cy, best.w * best.h)); t.missed = 0
                    remaining.remove(best)
                } else { t.missed++ }
            }
            for (d in remaining) tracks.add(T(mutableListOf(TrackPoint(i, d.cx, d.cy, d.w * d.h))))
            val iter = tracks.iterator()
            while (iter.hasNext()) { val t = iter.next(); if (t.missed > 2) { finished.add(t); iter.remove() } }
        }
        finished.addAll(tracks)
        val usable = finished.filter { t ->
            val travel = (t.pts.maxOf { it.cx } - t.pts.minOf { it.cx }) + (t.pts.maxOf { it.cy } - t.pts.minOf { it.cy })
            t.pts.size >= 3 && travel >= 0.05
        }
        val main = usable.maxByOrNull { it.pts.size }

        val path = buildJsonArray {
            main?.pts?.forEach { p -> add(buildJsonObject { put("t", round(times.getOrElse(p.frame) { 0.0 })); put("x", round(p.cx, 3)); put("y", round(p.cy, 3)) }) }
        }
        val visible = main?.pts?.size ?: 0
        // speed in normalized units/second
        val speeds = main?.let { t ->
            (1 until t.pts.size).map { k ->
                val a = t.pts[k - 1]; val b = t.pts[k]
                val dt = (times.getOrElse(b.frame) { 0.0 } - times.getOrElse(a.frame) { 0.0 }).takeIf { it > 0 } ?: 1.0
                sqrt((b.cx - a.cx).let { it * it } + (b.cy - a.cy).let { it * it }) / dt
            }
        } ?: emptyList()

        val stats = buildJsonObject {
            put("visible_frames", visible)
            put("max_speed", round(speeds.maxOrNull() ?: 0.0, 4))
            put("mean_speed", round(speeds.average().takeIf { !it.isNaN() } ?: 0.0, 4))
            put("hits", reversals(main?.pts ?: emptyList(), times) { it.cx })
            put("bounces", reversals(main?.pts ?: emptyList(), times) { it.cy })
        }
        val trajectory = buildJsonArray {
            val areas = main?.pts?.map { it.area }?.sorted() ?: emptyList()
            val medianArea = if (areas.isEmpty()) 1.0 else areas[areas.size / 2]
            main?.pts?.forEach { p ->
                val z = if (p.area > 0) sqrt(medianArea / p.area) else 1.0
                add(buildJsonObject { put("x", round(p.cx, 3)); put("y", round(p.cy, 3)); put("z", round(z, 3)) })
            }
        }
        val segments = segments(activity)
        return buildJsonObject {
            put("detector", "onnx-model")
            put("path", path)
            put("segments", segments)
            put("trajectory3d", trajectory)
            put("stats", stats)
        }
    }

    /** Direction reversals of a coordinate along the track (contacts / bounces). */
    private fun reversals(pts: List<TrackPoint>, times: List<Double>, axis: (TrackPoint) -> Double): JsonArray = buildJsonArray {
        for (i in 1 until pts.size - 1) {
            val d1 = axis(pts[i]) - axis(pts[i - 1]); val d2 = axis(pts[i + 1]) - axis(pts[i])
            if (d1 * d2 < 0 && abs(d2) > 0.02) add(buildJsonObject { put("t", round(times.getOrElse(pts[i].frame) { 0.0 })) })
        }
    }

    /** Movement-energy segments: threshold max(median·1.3, median+0.5); spans ≥0.4 s. */
    private fun segments(activity: List<Pair<Double, Double>>): JsonArray {
        if (activity.isEmpty()) return JsonArray(emptyList())
        val sorted = activity.map { it.second }.sorted()
        val median = sorted[sorted.size / 2]
        val threshold = max(median * 1.3, median + 0.5)
        val out = ArrayList<Pair<Double, Double>>()
        var start: Double? = null; var prev = 0.0
        activity.forEach { (t, e) ->
            if (e >= threshold) { if (start == null) start = t; prev = t }
            else if (start != null) { if (prev - start!! >= 0.4) out.add(start!! to prev); start = null }
        }
        start?.let { if (prev - it >= 0.4) out.add(it to prev) }
        return buildJsonArray {
            out.forEach { (s, e) -> add(buildJsonObject { put("start", round(s)); put("end", round(e)) }) }
        }
    }

    fun overlay(base: Bitmap?, ball: JsonObject): Bitmap? {
        val b = base ?: return null
        val out = b.copy(Bitmap.Config.ARGB_8888, true)
        val c = Canvas(out)
        val paint = Paint().apply { color = Color.rgb(251, 113, 133); strokeWidth = 4f; isAntiAlias = true }
        val w = out.width.toFloat(); val h = out.height.toFloat()
        (ball["path"] as? JsonArray)?.forEach { el ->
            val o = el as? JsonObject ?: return@forEach
            val x = o["x"]?.toString()?.toDoubleOrNull() ?: return@forEach
            val y = o["y"]?.toString()?.toDoubleOrNull() ?: return@forEach
            c.drawCircle((x * w).toFloat(), (y * h).toFloat(), 6f, paint)
        }
        return out
    }

    private fun round(v: Double, dp: Int = 2): Double {
        val p = Math.pow(10.0, dp.toDouble()); return Math.round(v * p) / p
    }
}
