package com.topspinreview.android.pipeline

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

/**
 * Metrics, ported from `core/video/metrics.py`. P1 computes the **activity** timeline (movement
 * energy) and renders it as prompt text; mechanics/pose/ball are the next phases (Appendix A).
 */
object Metrics {
    fun analyze(frames: List<Sampler.Frame>): JsonObject {
        val activity = buildJsonArray {
            for (i in 1 until frames.size) {
                add(
                    buildJsonObject {
                        put("t", round(frames[i].t, 2))
                        put("energy", round(energy(frames[i - 1], frames[i]), 2))
                        put("dx", 0.0); put("dy", 0.0) // TODO P2: FFT phase correlation
                    }
                )
            }
        }
        val energies = (activity as JsonArray).map { it.let { o -> (o as JsonObject)["energy"]!!.toString().toFloat() } }
        val maxE = energies.maxOrNull() ?: 0f
        val meanE = if (energies.isEmpty()) 0f else energies.sum() / energies.size
        val peakT = (activity.maxByOrNull { (it as JsonObject)["energy"]!!.toString().toFloat() } as? JsonObject)
            ?.get("t") ?: JsonPrimitive(0)
        return buildJsonObject {
            put("activity", activity)
            put("mean_energy", round(meanE.toDouble(), 2))
            put("max_energy", round(maxE.toDouble(), 2))
            put("peak_motion_time", peakT)
            put("net_shift", buildJsonArray { add(0.0); add(0.0) })
        }
    }

    /** Metrics rendered for prompts (subset of `metrics.text()`; see Appendix L1). */
    fun text(m: JsonObject): String {
        val mean = m["mean_energy"] ?: JsonPrimitive(0)
        val max = m["max_energy"] ?: JsonPrimitive(0)
        val peak = m["peak_motion_time"] ?: JsonPrimitive(0)
        val activity = m["activity"] as? JsonArray ?: JsonArray(emptyList())
        val rendered = activity.joinToString("; ") {
            val o = it as JsonObject
            "t=${o["t"]}s E=${o["energy"]}"
        }
        return "- overall motion: mean energy $mean, peak $max at t=${peak}s\n- activity timeline: $rendered"
    }

    private fun energy(a: Sampler.Frame, b: Sampler.Frame): Double {
        val ga = gray(a.bitmap); val gb = gray(b.bitmap)
        var s = 0.0
        for (i in ga.indices) s += kotlin.math.abs(ga[i] - gb[i])
        return if (ga.isEmpty()) 0.0 else s / ga.size
    }

    private fun gray(bmp: android.graphics.Bitmap): FloatArray {
        val s = android.graphics.Bitmap.createScaledBitmap(bmp, 320, 180, true)
        val px = IntArray(320 * 180); s.getPixels(px, 0, 320, 0, 0, 320, 180)
        return FloatArray(px.size) {
            val p = px[it]
            0.299f * ((p shr 16) and 0xff) + 0.587f * ((p shr 8) and 0xff) + 0.114f * (p and 0xff)
        }
    }

    private fun round(v: Double, dp: Int): Double = Math.round(v * Math.pow(10.0, dp.toDouble())) / Math.pow(10.0, dp.toDouble())
}
