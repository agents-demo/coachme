package com.topspinreview.android.pipeline

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import com.topspinreview.android.data.Report
import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.data.SettingsStore
import com.topspinreview.android.llm.DeepSeekClient
import com.topspinreview.android.llm.Prompts
import com.topspinreview.android.llm.ReportTools
import com.topspinreview.android.llm.ToolCall
import kotlinx.coroutines.flow.first
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.io.File
import kotlin.math.ceil

/**
 * The pipeline: measure → observe → coach (mock-free MVP slice).
 *
 * Renders a contact sheet, does the two vision passes, then runs the report agent loop
 * (tools from [ReportTools]) and returns the saved [Report]. See docs/ANDROID_PLAN.md §7.
 */
class Pipeline(
    private val sampler: Sampler,
    private val client: DeepSeekClient,
    private val tools: ReportTools,
    private val store: ReportStore,
    private val settings: SettingsStore,
    private val json: Json,
) {
    suspend fun analyze(videoPath: String, onStage: (String) -> Unit): Report {
        val cfg = settings.flow.first()

        val stem = File(videoPath).nameWithoutExtension
        tools.runStem = stem

        onStage("Pick frames")
        val frames = sampler.sample(videoPath, cfg.maxFrames)
        require(frames.isNotEmpty()) { "No frames could be extracted." }

        onStage("Measure movement")
        val measured = Metrics.analyze(frames)
        val metrics = measured.json
        val metricsText = Metrics.text(metrics)

        val sheet = contactSheet(frames)
        val sheetB64 = sampler.toJpegBase64(sheet)

        onStage("Render images")
        val artifacts = linkedMapOf<String, String>()
        artifacts["frames"] = store.saveArtifact(stem, "frames", sheet)
        measured.motionMap?.let { artifacts["motion"] = store.saveArtifact(stem, "motion", it) }
        measured.positionMap?.let { artifacts["heatmap"] = store.saveArtifact(stem, "heatmap", it) }

        val windows = try {
            onStage("First look")
            val coarse = client.vision(
                Prompts.VISION_AGENT_SYSTEM,
                Prompts.coarse(frames.size, cfg.sport, cfg.level, cfg.hand, cfg.goal, metricsText, sampler.duration(videoPath)),
                listOf(sheetB64),
            )
            extractJson(coarse)?.jsonObject?.get("attentive_windows")?.jsonArray ?: JsonArray(emptyList())
        } catch (e: Exception) { JsonArray(emptyList()) }

        onStage("Detailed findings")
        val windowLabel = windows.joinToString(", ") {
            val o = it.jsonObject
            "${o["start"]}s-${o["end"]}s"
        }.ifEmpty { "none" }
        val observations = try {
            val fine = client.vision(
                Prompts.VISION_AGENT_SYSTEM,
                Prompts.fine(0, cfg.level, cfg.hand, cfg.goal, metricsText, windowLabel),
                listOf(sheetB64),
            )
            extractJson(fine)?.jsonObject?.get("observations")?.jsonPrimitive?.content.orEmpty()
        } catch (e: Exception) { "" }

        onStage("Write report")
        runReportAgent(cfg.sport, cfg.level, cfg.hand, cfg.goal, frames.size, windowLabel, observations, metricsText)

        val savedStem = tools.lastSavedStem ?: stem
        val loaded = store.load(savedStem)
        val report = (loaded ?: Report(
            date = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date()),
            sport = cfg.sport, summary = observations, source = videoPath,
        )).copy(stem = savedStem, metrics = metrics, artifacts = artifacts)
        store.save(savedStem, report)
        return report
    }

    private suspend fun runReportAgent(
        sport: String, level: String, hand: String, goal: String,
        n: Int, windows: String, observations: String, metricsText: String,
    ) {
        val profileLine = "level $level, $hand-handed, working on $goal"
        val query = Prompts.reportQuery(
            SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date()),
            sport, profileLine, "No previous report.", n, windows, observations, metricsText,
            Prompts.rubric(sport),
        )
        val messages = mutableListOf(
            buildJsonObject { put("role", "system"); put("content", Prompts.REPORT_AGENT_SYSTEM) },
            buildJsonObject { put("role", "user"); put("content", query) },
        )
        repeat(25) {
            val resp = client.chat(buildJsonArray { messages.forEach { add(it) } }, tools.schemas())
            if (resp.toolCalls.isEmpty()) return
            messages.add(assistantToolCallMessage(resp.toolCalls))
            for (tc in resp.toolCalls) {
                val result = tools.execute(tc.name, tc.arguments)
                messages.add(
                    buildJsonObject {
                        put("role", "tool")
                        put("tool_call_id", tc.id)
                        put("content", result)
                    }
                )
            }
            if (tools.lastSavedStem != null) return
        }
    }

    private fun assistantToolCallMessage(calls: List<ToolCall>) = buildJsonObject {
        put("role", "assistant")
        put("content", "")
        put("tool_calls", buildJsonArray {
            calls.forEach { c ->
                add(
                    buildJsonObject {
                        put("id", c.id)
                        put("type", "function")
                        put("function", buildJsonObject { put("name", c.name); put("arguments", c.arguments) })
                    }
                )
            }
        })
    }

    private fun contactSheet(frames: List<Sampler.Frame>): Bitmap {
        val cols = minOf(4, frames.size)
        val rows = ceil(frames.size.toDouble() / cols).toInt()
        val cellW = 384; val cellH = 216
        val bmp = Bitmap.createBitmap(cols * cellW, rows * cellH, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        c.drawColor(Color.rgb(18, 18, 22))
        frames.forEachIndexed { i, f ->
            val r = i / cols; val col = i % cols
            val thumb = Bitmap.createScaledBitmap(f.bitmap, cellW, cellH, true)
            c.drawBitmap(thumb, (col * cellW).toFloat(), (r * cellH).toFloat(), null)
        }
        return bmp
    }

    private fun extractJson(text: String): kotlinx.serialization.json.JsonElement? = runCatching {
        val start = text.indexOf('{'); val end = text.lastIndexOf('}')
        if (start < 0 || end <= start) null else json.parseToJsonElement(text.substring(start, end + 1))
    }.getOrNull()
}
