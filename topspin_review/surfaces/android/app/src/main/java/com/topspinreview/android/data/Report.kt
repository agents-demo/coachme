package com.topspinreview.android.data

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject

/** A finding with the timestamps that support it and a confidence. */
@Serializable
data class Issue(
    val issue: String = "",
    val evidence_times: List<Double> = emptyList(),
    val confidence: String = "low",
)

/**
 * The coaching report. Same shape as the desktop `<stem>_report.json`; complex
 * blocks (`metrics`, `usage`) are kept as raw JSON so the port can evolve.
 */
@Serializable
data class Report(
    val date: String = "",
    val sport: String = "",
    val summary: String = "",
    val focus: String = "",
    val progress: String = "",
    val strengths: List<String> = emptyList(),
    val drills: List<String> = emptyList(),
    val limitations: List<String> = emptyList(),
    val issues: List<Issue> = emptyList(),
    val stem: String = "",
    val source: String = "",
    val metrics: JsonObject = JsonObject(emptyMap()),
    val artifacts: Map<String, String> = emptyMap(),
    val clips: Map<String, String> = emptyMap(),
    val usage: JsonObject = JsonObject(emptyMap()),
    val tt_reading: JsonObject? = null,
    val annotations: JsonArray = JsonArray(emptyList()),
)
