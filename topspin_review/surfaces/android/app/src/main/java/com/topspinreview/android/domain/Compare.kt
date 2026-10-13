package com.topspinreview.android.domain

import com.topspinreview.android.data.Report
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

/** Compare two reports, ported from `domain/compare.py` + `domain/progress.py`. */
object Compare {
    private val THEMES: Map<String, List<String>> = mapOf(
        "footwork" to listOf("foot", "step", "split", "stance", "balance", "weight", "lunge", "shuffle"),
        "stroke" to listOf("swing", "stroke", "forehand", "backhand", "racket", "paddle", "follow-through", "follow through"),
        "preparation" to listOf("preparation", "prep", "backswing", "ready", "set up"),
        "recovery" to listOf("recovery", "recover", "reset", "return", "neutral"),
        "serve" to listOf("serve", "toss", "service"),
    )

    fun classify(text: String): Set<String> {
        val t = text.lowercase()
        return THEMES.filterValues { words -> words.any { t.contains(it) } }.keys
    }

    data class Diff(
        val improved: List<String>,
        val regressed: List<String>,
        val unchanged: List<String>,
        val metricDeltas: Map<String, Double>,
        val text: String,
    )

    fun compare(older: Report, newer: Report): Diff {
        val oldThemes = classify(older.issues.joinToString(" ") { it.issue })
        val newThemes = classify(newer.issues.joinToString(" ") { it.issue })
        val improved = (oldThemes - newThemes).sorted()
        val regressed = (newThemes - oldThemes).sorted()
        val unchanged = (oldThemes intersect newThemes).sorted()

        val oldMech = (older.metrics["mechanics"] as? JsonObject) ?: JsonObject(emptyMap())
        val newMech = (newer.metrics["mechanics"] as? JsonObject) ?: JsonObject(emptyMap())
        val keys = (oldMech.keys + newMech.keys)
        val deltas = keys.associateWith { k ->
            num(newMech[k]) - num(oldMech[k])
        }

        val parts = mutableListOf<String>()
        if (improved.isNotEmpty()) parts.add("improved: ${improved.joinToString(", ")}")
        if (regressed.isNotEmpty()) parts.add("regressed: ${regressed.joinToString(", ")}")
        if (unchanged.isNotEmpty()) parts.add("still open: ${unchanged.joinToString(", ")}")
        return Diff(improved, regressed, unchanged, deltas, parts.joinToString("; ").ifEmpty { "no comparable change." })
    }

    private fun num(el: kotlinx.serialization.json.JsonElement?): Double =
        when (el) {
            null -> 0.0
            is JsonPrimitive -> el.content.toDoubleOrNull() ?: 0.0
            else -> 0.0
        }
}
