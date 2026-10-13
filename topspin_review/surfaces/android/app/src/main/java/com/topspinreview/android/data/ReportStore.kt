package com.topspinreview.android.data

import android.content.Context
import kotlinx.serialization.json.Json
import java.io.File

/** Reports live in app-private storage: `filesDir/reports/<stem>.json`. */
class ReportStore(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = true; isLenient = true; prettyPrint = true }
    private val dir: File = File(context.filesDir, "reports").apply { mkdirs() }

    fun list(): List<Report> =
        dir.listFiles { f -> f.name.endsWith("_report.json") }
            ?.mapNotNull { runCatching { json.decodeFromString<Report>(it.readText()) }.getOrNull() }
            ?.sortedByDescending { it.date } ?: emptyList()

    fun load(stem: String): Report? {
        val f = file(stem)
        if (!f.exists()) return null
        return runCatching { json.decodeFromString<Report>(f.readText()) }.getOrNull()
    }

    fun save(stem: String, report: Report) = file(stem).writeText(json.encodeToString(Report.serializer(), report))

    /** Save a raw JSON string (as returned by the model) under a stem. */
    fun saveRaw(stem: String, rawJson: String) = file(stem).writeText(rawJson)

    fun delete(stem: String) { file(stem).delete() }

    /** The last N reports as a compact JSON array (for the `recent_reports` tool). */
    fun recentJson(n: Int = 5): String =
        json.encodeToString(
            kotlinx.serialization.builtins.ListSerializer(Report.serializer()),
            list().take(n),
        )

    private fun file(stem: String): File = File(dir, "${stem}_report.json")
}
