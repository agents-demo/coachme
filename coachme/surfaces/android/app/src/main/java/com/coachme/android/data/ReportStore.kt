package com.coachme.android.data

import android.content.Context
import android.graphics.Bitmap
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

    /** Update display metadata (name, tags, notes) without touching any other field. */
    fun patch(stem: String, name: String, tags: List<String>, notes: String): Report? {
        val current = load(stem) ?: return null
        val updated = current.copy(
            name = name.trim(),
            tags = tags.map { it.trim() }.filter { it.isNotEmpty() }.distinct().take(10),
            notes = notes.trim(),
        )
        save(stem, updated)
        return updated
    }

    /** Persist a session's shape annotations (drawn on the video). */
    fun saveAnnotations(stem: String, annotations: kotlinx.serialization.json.JsonArray) {
        val current = load(stem) ?: return
        file(stem).writeText(json.encodeToString(Report.serializer(), current.copy(annotations = annotations)))
    }

    /** Save a raw JSON string (as returned by the model) under a stem. */
    fun saveRaw(stem: String, rawJson: String) = file(stem).writeText(rawJson)

    fun delete(stem: String) { file(stem).delete() }

    /** Whether a saved report exists for this stem. */
    fun exists(stem: String): Boolean = file(stem).exists()

    /** Save a rendered artifact (PNG) for a stem; returns its absolute path. */
    fun saveArtifact(stem: String, kind: String, bitmap: Bitmap): String {
        val dir = File(context.filesDir, "artifacts").apply { mkdirs() }
        val f = File(dir, "${stem}_$kind.png")
        f.outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        return f.absolutePath
    }

    /** The last N reports as a compact JSON array (for the `recent_reports` tool). */
    fun recentJson(n: Int = 5): String =
        json.encodeToString(
            kotlinx.serialization.builtins.ListSerializer(Report.serializer()),
            list().take(n),
        )

    private fun file(stem: String): File = File(dir, "${stem}_report.json")
}
