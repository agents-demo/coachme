package com.topspinreview.android.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import java.io.File

/** A sampled frame persisted to disk (its timestamp + the PNG file name in the run dir). */
@Serializable
data class FrameRef(val t: Double = 0.0, val file: String = "")

/** A pose frame's landmarks, in a serializable form (Python-style nested lists). */
@Serializable
data class LandmarkFrame(
    val lm: List<List<Float>>? = null,
    val world: List<List<Float>>? = null,
)

/** One recorded model call, in a serializable form (mirrors [com.topspinreview.android.llm.CallInfo]). */
@Serializable
data class CallRecord(
    val stage: String = "",
    val model: String = "",
    val promptTokens: Int = 0,
    val completionTokens: Int = 0,
    val seconds: Double = 0.0,
)

/**
 * The full state of an in-progress analysis run, written to disk after every pipeline
 * stage. A failed run can be resumed from the first stage whose id is missing from
 * [completed], instead of redoing the local vision work and re-billing the model calls.
 */
@Serializable
data class RunCheckpoint(
    val videoPath: String = "",
    val stem: String = "",
    val isImage: Boolean = false,
    val region: List<Float> = emptyList(),
    val completed: List<String> = emptyList(),
    val frames: List<FrameRef> = emptyList(),
    val measuredJson: JsonObject = JsonObject(emptyMap()),
    val activity: List<List<Double>> = emptyList(),
    val motionFile: String? = null,
    val positionFile: String? = null,
    val pose: List<LandmarkFrame> = emptyList(),
    val ballJson: JsonObject = JsonObject(emptyMap()),
    val metrics: JsonObject = JsonObject(emptyMap()),
    val metricsText: String = "",
    val quality: JsonObject = JsonObject(emptyMap()),
    val ttReading: JsonObject = JsonObject(emptyMap()),
    val sheetB64: String = "",
    val artifacts: Map<String, String> = emptyMap(),
    val windows: JsonArray = JsonArray(emptyList()),
    val windowLabel: String = "none",
    val observations: String = "",
    val savedStem: String? = null,
    val loadedReport: Report? = null,
    val warnings: List<String> = emptyList(),
    val timeline: Map<String, Double> = emptyMap(),
    val calls: List<CallRecord> = emptyList(),
    val toolCalls: JsonArray = JsonArray(emptyList()),
)

/**
 * Persists [RunCheckpoint]s and their binary intermediates under `filesDir/runs/<stem>/`.
 * Bitmaps (sampled frames, motion/position maps) are stored as PNGs next to the JSON.
 */
class RunStore(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = true; isLenient = true; encodeDefaults = true }
    private val root: File = File(context.filesDir, "runs").apply { mkdirs() }

    fun exists(stem: String): Boolean = file(stem).exists()

    /** All interrupted runs on disk, newest first (drives the "Resume" banner on entry). */
    fun list(): List<RunCheckpoint> {
        val dirs = root.listFiles { f -> f.isDirectory } ?: return emptyList()
        return dirs.mapNotNull { d ->
            val f = File(d, "checkpoint.json")
            if (!f.exists()) return@mapNotNull null
            runCatching { json.decodeFromString(RunCheckpoint.serializer(), f.readText()) to f.lastModified() }.getOrNull()
        }.sortedByDescending { it.second }.map { it.first }
    }

    fun load(stem: String): RunCheckpoint? {
        val f = file(stem)
        if (!f.exists()) return null
        return runCatching { json.decodeFromString(RunCheckpoint.serializer(), f.readText()) }.getOrNull()
    }

    fun save(checkpoint: RunCheckpoint) {
        file(checkpoint.stem).writeText(json.encodeToString(RunCheckpoint.serializer(), checkpoint))
    }

    fun clear(stem: String) {
        val d = dir(stem)
        if (d.exists()) d.deleteRecursively()
    }

    /** Write a bitmap as a PNG in the run dir; returns its file name (for [FrameRef] / checkpoint). */
    fun saveBitmap(stem: String, name: String, bitmap: Bitmap): String {
        val f = File(dir(stem), "$name.png")
        f.outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        return f.name
    }

    fun loadBitmap(stem: String, name: String?): Bitmap? {
        if (name.isNullOrBlank()) return null
        val f = File(dir(stem), name)
        return if (f.exists()) BitmapFactory.decodeFile(f.absolutePath) else null
    }

    private fun dir(stem: String): File = File(root, sanitize(stem)).apply { mkdirs() }
    private fun file(stem: String): File = File(dir(stem), "checkpoint.json")

    private fun sanitize(name: String): String =
        name.replace(Regex("[^A-Za-z0-9._-]"), "_").ifBlank { "run" }
}
