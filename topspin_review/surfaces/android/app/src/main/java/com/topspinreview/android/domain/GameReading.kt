package com.topspinreview.android.domain

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

/**
 * Translate measured metrics into table-tennis readings, ported from `domain/game_reading.py`
 * (Appendix L4). Grouped Play / Player / Ball, plus the notable moments.
 */
object GameReading {
    fun summarize(metrics: JsonObject): JsonObject {
        val ball = metrics["ball"] as? JsonObject ?: JsonObject(emptyMap())
        val stats = ball["stats"] as? JsonObject ?: JsonObject(emptyMap())
        val segments = ball["segments"] as? JsonArray ?: JsonArray(emptyList())
        val strokes = metrics["strokes"] as? JsonArray ?: JsonArray(emptyList())
        val foot = metrics["footwork"] as? JsonObject ?: JsonObject(emptyMap())
        val mech = metrics["mechanics"] as? JsonObject ?: JsonObject(emptyMap())
        val pose = metrics["pose_summary"] as? JsonObject ?: JsonObject(emptyMap())
        val p3 = metrics["pose3d_summary"] as? JsonObject ?: JsonObject(emptyMap())

        val findings = ArrayList<JsonObject>()

        // --- Play ---
        if (segments.isNotEmpty()) {
            findings.add(finding("Play", "Rallies", segments.size.toString(), "active stretches of play (≈ rallies)"))
        }
        val hits = (stats["hits"] as? JsonArray)?.size ?: 0
        val bounces = (stats["bounces"] as? JsonArray)?.size ?: 0
        if (hits > 0 || bounces > 0) {
            findings.add(finding("Play", "Contacts / bounces", "$hits / $bounces", "direction reversals of the tracked ball"))
        }
        num(metrics["mean_energy"])?.let { e ->
            val busy = if (e >= 8) "busy" else if (e >= 3) "moderate" else "quiet"
            findings.add(finding("Play", "Activity", busy, "mean energy $e"))
        }

        // --- Player ---
        if (strokes.isNotEmpty()) {
            val left = strokes.count { (it as? JsonObject)?.get("hand")?.toString()?.trim('"') == "left" }
            val right = strokes.count { (it as? JsonObject)?.get("hand")?.toString()?.trim('"') == "right" }
            findings.add(finding("Player", "Strokes", strokes.size.toString(), "$right right-handed, $left left-handed"))
        }
        val lk = num(pose["l_knee_mean"]); val rk = num(pose["r_knee_mean"])
        if (lk != null || rk != null) {
            val avg = listOfNotNull(lk, rk).average()
            val bend = if (avg >= 150) "quite extended" else if (avg >= 120) "moderately bent" else "deeply bent"
            findings.add(finding("Player", "Knee bend", bend, "knees ${lk ?: "?"}° / ${rk ?: "?"}°"))
        }
        val le = num(pose["l_elbow_mean"]); val re = num(pose["r_elbow_mean"])
        if (le != null || re != null) findings.add(finding("Player", "Elbow bend", "${le ?: "?"}° / ${re ?: "?"}°", "left / right"))
        num(p3["torso_lean_mean"])?.let { findings.add(finding("Player", "Torso lean", "${it}°", "from vertical")) }
        num(p3["shoulder_hip_twist_mean"])?.let { findings.add(finding("Player", "Rotation", "${it}°", "shoulder–hip twist")) }
        num(mech["lower_lateral_range"])?.let { lat ->
            val steps = num(mech["lower_direction_changes"])
            val note = "side-to-side travel $lat of the frame" + (steps?.let { ", ~${it.toInt()} changes of direction" } ?: "")
            val verdict = if (lat > 0.15) "moving well around the table" else "mostly stationary"
            findings.add(finding("Player", "Footwork", verdict, note))
        }

        // --- Ball ---
        num(stats["visible_frames"])?.let { findings.add(finding("Ball", "Tracked", "${it.toInt()} frames", "how often the ball was tracked")) }
        num(stats["max_speed"])?.takeIf { it > 0 }?.let { findings.add(finding("Ball", "Pace", "relative", "max $it/s (screen units — not a real speed)")) }
        val xs = num(stats["x_range"]); val ys = num(stats["y_range"])
        if (xs != null || ys != null) findings.add(finding("Ball", "Path extent", "x ${xs ?: "?"}, y ${ys ?: "?"}", "spread of the tracked path"))

        // --- Moments ---
        val moments = ArrayList<JsonObject>()
        segments.forEach { el ->
            num((el as? JsonObject)?.get("start"))?.let { moments.add(moment(it, "active span")) }
        }
        strokes.forEach { el ->
            val o = el as? JsonObject ?: return@forEach
            num(o["t"])?.let { moments.add(moment(it, "${o["hand"]?.toString()?.trim('"') ?: "?"} fast-hand")) }
        }
        moments.sortBy { it["t"]!!.toString().toDouble() }

        return buildJsonObject {
            put("findings", buildJsonArray { findings.forEach { add(it) } })
            put("moments", buildJsonArray { moments.forEach { add(it) } })
        }
    }

    private fun finding(group: String, label: String, value: String, note: String) = buildJsonObject {
        put("group", group); put("label", label); put("value", value); put("note", note)
    }

    private fun moment(t: Double, label: String) = buildJsonObject {
        put("t", Math.round(t * 100.0) / 100.0); put("label", label)
    }

    private fun num(el: JsonElement?): Double? {
        if (el == null) return null
        return el.toString().toDoubleOrNull()
    }
}
