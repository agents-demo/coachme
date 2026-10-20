package com.coachme.android.pipeline

import android.graphics.Bitmap
import android.graphics.Color
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/** The result of measuring a clip: the metrics JSON plus the rendered maps. */
data class Measured(
    val json: JsonObject,
    val motionMap: Bitmap?,
    val positionMap: Bitmap?,
    val activity: List<Pair<Double, Double>>,
)

/**
 * Metrics, ported from `core/video/metrics.py` (Appendix B/L).
 * Analysis grid 320×180; maps 640×360. Pure pixel math on [Bitmap]s.
 */
object Metrics {
    private const val AW = 320
    private const val AH = 180
    private const val MW = 640
    private const val MH = 360
    private const val FG = 18f        // foreground threshold
    private const val MIN_PIX = 20

    fun analyze(frames: List<Sampler.Frame>, regionBox: FloatArray? = null): Measured {
        val bg = background(frames)
        val region = subjectRegion(frames, bg, regionBox)
        val activity = activity(frames)
        val track = subjectTrack(frames, bg, region)
        val regTrack = regions(frames, bg, region)
        val mech = mechanics(regTrack)
        val footSeries = footworkSeries(regTrack, frames)

        val energies = activity.map { it.second }
        val meanE = if (energies.isEmpty()) 0.0 else energies.sum() / energies.size
        val maxE = energies.maxOrNull() ?: 0.0
        val peakT = activity.maxByOrNull { it.second }?.first ?: 0.0

        val mechJson = buildJsonObject {
            put("lower_lateral_range", mech.lowerLateral)
            put("lower_vertical_range", mech.lowerVertical)
            put("upper_lateral_range", mech.upperLateral)
            put("lower_direction_changes", mech.dirChanges)
            put("crouch_box_range", mech.crouchRange)
        }

        val shiftsList = shifts(frames)
        val boxes = track.filterNotNull()
        val subW = if (boxes.isEmpty()) 0.0 else boxes.map { it.w }.average()
        val subH = if (boxes.isEmpty()) 0.0 else boxes.map { it.h }.average()

        val json = buildJsonObject {
            put("activity", buildJsonArray {
                activity.forEachIndexed { i, (t, e) ->
                    val (dx, dy) = shiftsList.getOrElse(i) { 0.0 to 0.0 }
                    add(buildJsonObject { put("t", round(t, 2)); put("energy", round(e, 2)); put("dx", round(dx, 1)); put("dy", round(dy, 1)) })
                }
            })
            put("mean_energy", round(meanE, 2))
            put("max_energy", round(maxE, 2))
            put("peak_motion_time", round(peakT, 2))
            put(
                "net_shift",
                buildJsonArray {
                    add(JsonPrimitive(round(shiftsList.sumOf { it.first }, 1)))
                    add(JsonPrimitive(round(shiftsList.sumOf { it.second }, 1)))
                },
            )
            put(
                "posture",
                buildJsonObject {
                    if (boxes.isNotEmpty()) {
                        put("box_height_mean", round(subH, 3))
                        put("box_width_mean", round(subW, 3))
                        put("aspect_mean", round(subH / maxOf(1e-6, subW), 2))
                        put("lateral_range", round(boxes.map { it.cx }.maxOrNull()!! - boxes.map { it.cx }.minOrNull()!!, 3))
                        put("coverage_mean", round(boxes.map { it.coverage }.average(), 3))
                    }
                },
            )
            put("mechanics", mechJson)
            put(
                "calibration",
                buildJsonObject {
                    put("subject_width", round(subW, 3)); put("subject_height", round(subH, 3)); put("basis", "subject_box")
                },
            )
            put(
                "calibrated",
                buildJsonObject {
                    if (subW > 0) {
                        put("lower_lateral_range_bw", round(mech.lowerLateral / subW, 3))
                        put("upper_lateral_range_bw", round(mech.upperLateral / subW, 3))
                    }
                    if (subH > 0) put("crouch_change_bh", round(mech.crouchRange / subH, 3))
                },
            )
            put("footwork_series", footSeries)
            put("subject_coverage", round(region.count { it }.toDouble() / (AW * AH), 3))
        }

        return Measured(json, motionMap(frames, region), positionHeatmap(frames, track), activity)
    }

    /** Metrics rendered for prompts (subset of `metrics.text()`; Appendix L1). */
    fun text(m: JsonObject): String {
        val mean = m["mean_energy"] ?: JsonPrimitive(0)
        val max = m["max_energy"] ?: JsonPrimitive(0)
        val peak = m["peak_motion_time"] ?: JsonPrimitive(0)
        val mech = m["mechanics"] as? JsonObject
        val activity = m["activity"] as? JsonArray ?: JsonArray(emptyList())
        val rendered = activity.joinToString("; ") {
            val o = it as JsonObject
            "t=${o["t"]}s E=${o["energy"]}"
        }
        val mechLine = mech?.let {
            "- mechanics: lower-body lateral range ${it["lower_lateral_range"]}, direction changes ${it["lower_direction_changes"]}, upper-body lateral range ${it["upper_lateral_range"]}, crouch change ${it["crouch_box_range"]}"
        } ?: ""
        val post = m["posture"] as? JsonObject
        val postLine = if (post != null && post.isNotEmpty()) {
            "- subject box: mean height ${post["box_height_mean"]} width ${post["box_width_mean"]} (aspect ${post["aspect_mean"]}), lateral drift ${post["lateral_range"]}"
        } else ""
        val cal = m["calibrated"] as? JsonObject
        val calLine = if (cal != null && cal.isNotEmpty()) {
            "- calibrated (body-relative, distance-independent): " + cal.entries.joinToString(", ") { "${it.key}=${it.value}" }
        } else ""
        return listOf(
            "- overall motion: mean energy $mean, peak $max at t=${peak}s",
            "- activity timeline: $rendered",
            mechLine,
            postLine,
            calLine,
        ).filter { it.isNotEmpty() }.joinToString("\n")
    }

    /** Public: the per-step movement energy for a frame set (used for segmentation). */
    fun activityPairs(frames: List<Sampler.Frame>): List<Pair<Double, Double>> = activity(frames)

    // --- analysis ---------------------------------------------------------------

    private fun background(frames: List<Sampler.Frame>): FloatArray {
        val n = frames.size
        val stack = frames.map { gray(it.bitmap, AW, AH) }
        val bg = FloatArray(AW * AH)
        for (v in 0 until AW * AH) {
            val vals = FloatArray(n) { stack[it][v] }
            vals.sort()
            bg[v] = if (n % 2 == 1) vals[n / 2] else (vals[n / 2 - 1] + vals[n / 2]) / 2f
        }
        return bg
    }

    private fun subjectRegion(frames: List<Sampler.Frame>, bg: FloatArray, regionBox: FloatArray?): BooleanArray {
        if (regionBox != null && regionBox.size == 4) return regionFromBox(regionBox)
        val mask = BooleanArray(AW * AH)
        for (f in frames) {
            val g = gray(f.bitmap, AW, AH)
            for (v in 0 until AW * AH) if (abs(g[v] - bg[v]) > FG) mask[v] = true
        }
        return largestComponent(mask)
    }

    /** Boolean mask for a normalized [left, top, right, bottom] box in 0..1. */
    private fun regionFromBox(box: FloatArray): BooleanArray {
        val out = BooleanArray(AW * AH)
        val x0 = (box[0] * AW).toInt().coerceIn(0, AW - 1)
        val x1 = (box[2] * AW).toInt().coerceIn(0, AW)
        val y0 = (box[1] * AH).toInt().coerceIn(0, AH - 1)
        val y1 = (box[3] * AH).toInt().coerceIn(0, AH)
        for (y in y0 until y1) for (x in x0 until x1) out[y * AW + x] = true
        return out
    }

    private fun largestComponent(mask: BooleanArray): BooleanArray {
        val seen = BooleanArray(mask.size)
        var best: IntArray? = null
        val queue = ArrayDeque<Int>()
        for (start in mask.indices) {
            if (!mask[start] || seen[start]) continue
            val comp = ArrayList<Int>()
            queue.addLast(start); seen[start] = true
            while (queue.isNotEmpty()) {
                val v = queue.removeFirst(); comp.add(v)
                val x = v % AW; val y = v / AW
                for ((dx, dy) in NEIGHBORS) {
                    val nx = x + dx; val ny = y + dy
                    if (nx in 0 until AW && ny in 0 until AH) {
                        val nv = ny * AW + nx
                        if (mask[nv] && !seen[nv]) { seen[nv] = true; queue.addLast(nv) }
                    }
                }
            }
            if (best == null || comp.size > best.size) best = comp.toIntArray()
        }
        val out = BooleanArray(mask.size)
        best?.forEach { out[it] = true }
        return out
    }

    private fun activity(frames: List<Sampler.Frame>): List<Pair<Double, Double>> {
        val out = ArrayList<Pair<Double, Double>>()
        val grays = frames.map { gray(it.bitmap, AW, AH) }
        for (i in 1 until frames.size) {
            var s = 0.0
            val a = grays[i - 1]; val b = grays[i]
            for (v in a.indices) s += abs(a[v] - b[v])
            out.add(frames[i].t to s / a.size)
        }
        return out
    }

    /** Per-step global translation (dx, dy) in analysis-pixel units. */
    private fun shifts(frames: List<Sampler.Frame>): List<Pair<Double, Double>> {
        val out = ArrayList<Pair<Double, Double>>()
        for (i in 1 until frames.size) out.add(globalShift(frames[i - 1].bitmap, frames[i].bitmap))
        return out
    }

    /** Global translation between two frames (brute-force SAD over a ±6px window at 64×64). */
    private fun globalShift(prev: Bitmap, cur: Bitmap): Pair<Double, Double> {
        val n = 64
        val a = gray(prev, n, n); val b = gray(cur, n, n)
        var bestSad = Double.MAX_VALUE; var bx = 0; var by = 0
        for (dy in -6..6) for (dx in -6..6) {
            var sad = 0.0; var cnt = 0
            val y0 = maxOf(0, -dy); val y1 = minOf(n, n - dy)
            val x0 = maxOf(0, -dx); val x1 = minOf(n, n - dx)
            var y = y0
            while (y < y1) { var x = x0; while (x < x1) { sad += abs(a[(y + dy) * n + (x + dx)] - b[y * n + x]); cnt++; x++ }; y++ }
            if (cnt > 0) { val s = sad / cnt; if (s < bestSad) { bestSad = s; bx = dx; by = dy } }
        }
        return (bx.toDouble() * AW / n) to (by.toDouble() * AH / n)
    }

    private data class Track(val cx: Double, val cy: Double, val w: Double, val h: Double, val coverage: Double)

    private fun subjectTrack(frames: List<Sampler.Frame>, bg: FloatArray, region: BooleanArray): List<Track?> =
        frames.map { f ->
            val g = gray(f.bitmap, AW, AH)
            var minX = AW; var maxX = -1; var minY = AH; var maxY = -1; var sumX = 0; var sumY = 0; var count = 0
            for (v in 0 until AW * AH) {
                if (!region[v]) continue
                if (abs(g[v] - bg[v]) > FG) {
                    val x = v % AW; val y = v / AW
                    if (x < minX) minX = x; if (x > maxX) maxX = x
                    if (y < minY) minY = y; if (y > maxY) maxY = y
                    sumX += x; sumY += y; count++
                }
            }
            if (count < MIN_PIX) null else Track(
                cx = sumX.toDouble() / count / AW,
                cy = sumY.toDouble() / count / AH,
                w = (maxX - minX).toDouble() / AW,
                h = (maxY - minY).toDouble() / AH,
                coverage = count.toDouble() / (AW * AH),
            )
        }

    private data class RegionRow(val lower: Double?, val middle: Double?, val upper: Double?, val middleW: Double?, val lowerCy: Double?)

    private fun regions(frames: List<Sampler.Frame>, bg: FloatArray, region: BooleanArray): List<RegionRow> =
        frames.map { f ->
            val g = gray(f.bitmap, AW, AH)
            val counts = IntArray(3)
            val sums = DoubleArray(3)
            val minX = IntArray(3) { AW }; val maxX = IntArray(3) { -1 }
            val sumY = DoubleArray(3)
            for (v in 0 until AW * AH) {
                if (!region[v]) continue
                if (abs(g[v] - bg[v]) > FG) {
                    val x = v % AW; val y = v / AW
                    val band = (y / (AH / 3)).coerceIn(0, 2)
                    sums[band] = sums[band] + x
                    counts[band] = counts[band] + 1
                    sumY[band] = sumY[band] + y
                    if (x < minX[band]) minX[band] = x
                    if (x > maxX[band]) maxX[band] = x
                }
            }
            fun cx(b: Int): Double? = if (counts[b] < 10) null else sums[b] / counts[b] / AW
            fun cw(b: Int): Double? = if (counts[b] < 10 || maxX[b] < 0) null else (maxX[b] - minX[b]).toDouble() / AW
            fun cy(b: Int): Double? = if (counts[b] < 10) null else sumY[b] / counts[b] / AH
            RegionRow(lower = cx(2), middle = cx(1), upper = cx(0), middleW = cw(1), lowerCy = cy(2))
        }

    private data class Mech(
        val lowerLateral: Double, val lowerVertical: Double, val upperLateral: Double,
        val dirChanges: Int, val crouchRange: Double,
    )

    private fun mechanics(rows: List<RegionRow>): Mech {
        val lower = rows.mapNotNull { it.lower }
        val upper = rows.mapNotNull { it.upper }
        val lowerCy = rows.mapNotNull { it.lowerCy }
        val mids = rows.mapNotNull { it.middleW }
        if (lower.isEmpty()) return Mech(0.0, 0.0, 0.0, 0, 0.0)
        val deltas = (1 until lower.size).map { lower[it] - lower[it - 1] }
        var changes = 0
        for (i in 1 until deltas.size) if (deltas[i] * deltas[i - 1] < 0 && abs(deltas[i]) > 0.005) changes++
        return Mech(
            lowerLateral = round((lower.maxOrNull()!! - lower.minOrNull()!!), 3),
            lowerVertical = if (lowerCy.isEmpty()) 0.0 else round(lowerCy.maxOrNull()!! - lowerCy.minOrNull()!!, 3),
            upperLateral = if (upper.isEmpty()) 0.0 else round(upper.maxOrNull()!! - upper.minOrNull()!!, 3),
            dirChanges = changes,
            crouchRange = if (mids.isEmpty()) 0.0 else round(mids.maxOrNull()!! - mids.minOrNull()!!, 3),
        )
    }

    private fun footworkSeries(rows: List<RegionRow>, frames: List<Sampler.Frame>): JsonArray = buildJsonArray {
        rows.forEachIndexed { i, r ->
            add(buildJsonObject {
                put("t", round(frames.getOrNull(i)?.t ?: i.toDouble(), 2))
                put("x", r.lower?.let { JsonPrimitive(round(it, 3)) } ?: kotlinx.serialization.json.JsonNull)
            })
        }
    }

    private fun motionMap(frames: List<Sampler.Frame>, region: BooleanArray): Bitmap? {
        if (frames.size < 2) return null
        val grays = frames.map { gray(it.bitmap, MW, MH) }
        val acc = FloatArray(MW * MH)
        for (i in 1 until grays.size) {
            val a = grays[i - 1]; val b = grays[i]
            for (v in acc.indices) acc[v] += abs(a[v] - b[v])
        }
        val regMask = scaleMask(region)
        var peak = 0f
        for (v in acc.indices) { if (!regMask[v]) acc[v] = 0f; if (acc[v] > peak) peak = acc[v] }
        if (peak <= 0f) return null
        val base = frames[0].bitmap.let { Bitmap.createScaledBitmap(it, MW, MH, true) }
        val out = base.copy(Bitmap.Config.ARGB_8888, true)
        val px = IntArray(MW * MH); out.getPixels(px, 0, MW, 0, 0, MW, MH)
        for (v in px.indices) {
            val a = acc[v] / peak
            val p = px[v]
            val r = min(255, (((p shr 16) and 0xff) + a * 200f).toInt())
            val g = (((p shr 8) and 0xff) * (1f - 0.6f * a)).toInt()
            val b = ((p and 0xff) * (1f - 0.6f * a)).toInt()
            px[v] = Color.rgb(r, g, b)
        }
        out.setPixels(px, 0, MW, 0, 0, MW, MH)
        return out
    }

    private fun positionHeatmap(frames: List<Sampler.Frame>, track: List<Track?>): Bitmap? {
        val pts = track.filterNotNull()
        if (pts.size < 3 || frames.isEmpty()) return null
        val gw = MW / 4; val gh = MH / 4
        val grid = IntArray(gw * gh)
        pts.forEach { p ->
            val x = (p.cx * gw).toInt().coerceIn(0, gw - 1)
            val y = (p.cy * gh).toInt().coerceIn(0, gh - 1)
            grid[y * gw + x] = min(255, grid[y * gw + x] + 60)
        }
        var peak = 0f
        for (v in grid) if (v > peak) peak = v.toFloat()
        if (peak <= 0f) return null
        val base = Bitmap.createScaledBitmap(frames[0].bitmap, MW, MH, true)
        val out = base.copy(Bitmap.Config.ARGB_8888, true)
        val px = IntArray(MW * MH); out.getPixels(px, 0, MW, 0, 0, MW, MH)
        for (y in 0 until MH) for (x in 0 until MW) {
            // nearest grid sample, normalised
            val heat = grid[(y / 4) * gw + (x / 4)] / peak
            val v = y * MW + x
            val p = px[v]
            val r = min(255, (((p shr 16) and 0xff) + heat * 200f).toInt())
            val g = ((p shr 8) and 0xff).let { (it * (1f - 0.7f * heat)).toInt() }
            val b = (p and 0xff).let { (it * (1f - 0.7f * heat)).toInt() }
            px[v] = Color.rgb(r, g, b)
        }
        out.setPixels(px, 0, MW, 0, 0, MW, MH)
        return out
    }

    // --- helpers ----------------------------------------------------------------

    private val NEIGHBORS = arrayOf(-1 to 0, 1 to 0, 0 to -1, 0 to 1)

    private fun scaleMask(region: BooleanArray): BooleanArray {
        val out = BooleanArray(MW * MH)
        for (y in 0 until MH) for (x in 0 until MW) {
            val sx = x * AW / MW; val sy = y * AH / MH
            out[y * MW + x] = region[sy * AW + sx]
        }
        return out
    }

    private fun gray(bmp: Bitmap, w: Int, h: Int): FloatArray {
        val s = Bitmap.createScaledBitmap(bmp, w, h, true)
        val px = IntArray(w * h); s.getPixels(px, 0, w, 0, 0, w, h)
        return FloatArray(px.size) {
            val p = px[it]
            0.299f * ((p shr 16) and 0xff) + 0.587f * ((p shr 8) and 0xff) + 0.114f * (p and 0xff)
        }
    }

    private fun round(v: Double, dp: Int): Double = Math.round(v * POW[dp]) / POW[dp]
    private val POW = doubleArrayOf(1.0, 10.0, 100.0, 1000.0)
}
