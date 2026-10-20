package com.coachme.android.pipeline

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.put

/** Footage-quality gate, ported from `core/stages/measure/quality.py` (Appendix L3). */
object Quality {
    fun evaluate(meta: Sampler.Meta, frameCount: Int, metrics: JsonObject): JsonObject {
        val warnings = ArrayList<String>()

        if (meta.height in 1 until 480) warnings.add("low resolution")
        if (meta.fps > 0.1 && meta.fps < 25) warnings.add("low frame rate (${meta.fps.toInt()} fps) — fast footwork may be missed")
        if (meta.duration > 0.1 && meta.duration < 3) warnings.add("very short clip (a few rallies are better)")
        if (frameCount < 8) warnings.add("few frames sampled")
        val meanEnergy = (metrics["mean_energy"]?.toString()?.toDoubleOrNull() ?: 0.0)
        if (meanEnergy <= 0.0) warnings.add("little visible movement detected")
        val coverage = metrics["subject_coverage"]?.toString()?.toDoubleOrNull()
        if (coverage == null) warnings.add("could not isolate the player from the background")

        return buildJsonObject {
            put("warnings", buildJsonArray { warnings.forEach { add(JsonPrimitive(it)) } })
        }
    }
}
