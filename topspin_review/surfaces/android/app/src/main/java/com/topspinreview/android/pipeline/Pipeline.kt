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
    private val pose: Pose,
    private val ball: Ball,
    private val client: DeepSeekClient,
    private val tools: ReportTools,
    private val store: ReportStore,
    private val settings: SettingsStore,
    private val json: Json,
) {
    suspend fun analyze(videoPath: String, regionBox: FloatArray? = null, onStage: (String) -> Unit): Report {
        val cfg = settings.flow.first()

        val stem = File(videoPath).nameWithoutExtension
        tools.beginRun(stem)
        client.calls.clear()

        fun since(ns: Long) = (System.nanoTime() - ns) / 1e9
        val timeline = linkedMapOf<String, Double>()

        val isImage = sampler.isImage(videoPath)

        onStage("Pick frames")
        val tFrames = System.nanoTime()
        val frames = if (isImage) listOf(sampler.loadImage(videoPath)) else sampler.sample(videoPath, cfg.maxFrames)
        timeline["sampling frames"] = since(tFrames)
        require(frames.isNotEmpty()) { "No frames could be extracted." }

        val measured = if (isImage) null else {
            onStage("Measure movement")
            val t = System.nanoTime()
            val m = Metrics.analyze(frames, regionBox)
            timeline["measuring motion"] = since(t)
            m
        }

        val poseSeq = if (isImage) emptyList() else {
            onStage("Estimate pose")
            val t = System.nanoTime()
            val p = pose.detect(frames)
            timeline["estimating pose"] = since(t)
            p
        }

        val ballJson = if (isImage || measured == null) JsonObject(emptyMap()) else {
            onStage("Track ball")
            val t = System.nanoTime()
            // Dense pass: spread the ball budget across the whole clip (the ball is on screen briefly).
            val ballFrames = sampler.sampleEven(videoPath, 60)
            val b = if (ballFrames.isNotEmpty())
                ball.process(ballFrames.map { it.t }, ball.detect(ballFrames), Metrics.activityPairs(ballFrames))
            else JsonObject(emptyMap())
            timeline["tracking ball"] = since(t)
            b
        }

        val metrics = if (measured == null) JsonObject(emptyMap()) else JsonObject(
            measured.json + mapOf(
                "pose_summary" to pose.summarize(poseSeq),
                "pose3d_summary" to pose.summarize3d(poseSeq),
                "pose3d" to pose.series3d(poseSeq),
                "pose_angles" to pose.anglesSeries(poseSeq, frames.map { it.t }),
                "strokes" to pose.strokes(poseSeq, frames),
                "footwork" to pose.footwork(poseSeq),
                "ball" to ballJson,
            )
        )
        val metricsText = Metrics.text(metrics)

        val quality = Quality.evaluate(sampler.meta(videoPath), frames.size, metrics)
        val ttReading = com.topspinreview.android.domain.GameReading.summarize(metrics)

        val sheet = contactSheet(frames)
        val sheetB64 = sampler.toJpegBase64(sheet)

        onStage("Render images")
        val motionBmp = measured?.motionMap
        val poseBmp = if (poseSeq.isNotEmpty()) pose.overlay(frames, poseSeq) else null
        val artifacts = linkedMapOf<String, String>()
        artifacts["frames"] = store.saveArtifact(stem, "frames", sheet)
        motionBmp?.let { artifacts["motion"] = store.saveArtifact(stem, "motion", it) }
        measured?.positionMap?.let { artifacts["heatmap"] = store.saveArtifact(stem, "heatmap", it) }
        poseBmp?.let { artifacts["pose"] = store.saveArtifact(stem, "pose", it) }
        if (ballJson.isNotEmpty()) ball.overlay(frames.getOrNull(frames.size / 2)?.bitmap, ballJson)?.let { artifacts["ball"] = store.saveArtifact(stem, "ball", it) }

        val windows: JsonArray
        val observations: String
        var windowLabel = "none"
        if (isImage) {
            onStage("Review image")
            client.stage = "vision: reviewing image"
            windows = JsonArray(emptyList())
            observations = try {
                val out = client.vision(
                    Prompts.VISION_AGENT_SYSTEM,
                    Prompts.still(cfg.sport, cfg.level, cfg.hand, cfg.goal),
                    listOf(sheetB64),
                )
                extractJson(out)?.jsonObject?.get("observations")?.jsonPrimitive?.content.orEmpty()
            } catch (e: Exception) { "" }
        } else {
            windows = try {
                onStage("First look")
                client.stage = "vision: overview"
                val coarse = client.vision(
                    Prompts.VISION_AGENT_SYSTEM,
                    Prompts.coarse(frames.size, cfg.sport, cfg.level, cfg.hand, cfg.goal, metricsText, sampler.duration(videoPath)),
                    listOf(sheetB64),
                )
                extractJson(coarse)?.jsonObject?.get("attentive_windows")?.jsonArray ?: JsonArray(emptyList())
            } catch (e: Exception) { JsonArray(emptyList()) }
            windowLabel = windows.joinToString(", ") {
                val o = it.jsonObject
                "${o["start"]}s-${o["end"]}s"
            }.ifEmpty { "none" }
            val zoomB64 = windows.take(3).flatMap { w ->
                val o = w.jsonObject
                val s = o["start"]?.toString()?.toDoubleOrNull() ?: return@flatMap emptyList()
                val e = o["end"]?.toString()?.toDoubleOrNull() ?: return@flatMap emptyList()
                sampler.sampleRange(videoPath, s, e, 2).map { sampler.toJpegBase64(it.bitmap) }
            }
            observations = try {
                onStage("Detailed findings")
                client.stage = "vision: detail"
                val fine = client.vision(
                    Prompts.VISION_AGENT_SYSTEM,
                    Prompts.fine(zoomB64.size, cfg.level, cfg.hand, cfg.goal, metricsText, windowLabel),
                    listOf(sheetB64) + listOfNotNull(
                        motionBmp?.let { sampler.toJpegBase64(it) },
                        poseBmp?.let { sampler.toJpegBase64(it) },
                    ) + zoomB64,
                )
                extractJson(fine)?.jsonObject?.get("observations")?.jsonPrimitive?.content.orEmpty()
            } catch (e: Exception) { "" }
        }

        onStage("Write report")
        runReportAgent(cfg.sport, cfg.level, cfg.hand, cfg.goal, frames.size, windowLabel, observations, metricsText)

        val savedStem = tools.lastSavedStem ?: stem
        var loaded = store.load(savedStem)
        loaded?.let { rep ->
            if (rep.issues.isNotEmpty()) {
                onStage("Double-check")
                client.stage = "verifying"
                val issuesText = rep.issues.mapIndexed { i, it -> "$i: ${it.issue} (t=${it.evidence_times.joinToString(",")})" }.joinToString("\n")
                val evidence = observations + "\n\n" + metricsText
                runCatching {
                    val resp = client.text(Prompts.VERIFY_SYSTEM, Prompts.verify(issuesText, evidence))
                    val supported = extractJson(resp)?.jsonObject?.get("supported")?.jsonArray?.mapNotNull { it.toString().toIntOrNull() }?.toSet()
                    if (supported != null) {
                        val kept = rep.issues.filterIndexed { i, _ -> i in supported }
                        if (kept.size != rep.issues.size) loaded = rep.copy(issues = kept)
                    }
                }
            }
        }
        val callsJson = buildJsonArray {
            client.calls.forEach { c ->
                add(buildJsonObject {
                    put("stage", c.stage); put("model", c.model)
                    put("prompt_tokens", c.promptTokens); put("completion_tokens", c.completionTokens)
                    put("seconds", c.seconds)
                })
            }
        }
        val usageJson = buildJsonObject {
            put("calls", client.calls.size)
            put("total_tokens", client.calls.sumOf { it.promptTokens + it.completionTokens })
        }
        val timelineJson = buildJsonArray {
            timeline.forEach { (s, secs) -> add(buildJsonObject { put("stage", s); put("seconds", secs) }) }
            client.calls.forEach { add(buildJsonObject { put("stage", it.stage); put("seconds", it.seconds) }) }
        }
        val toolsJson = buildJsonArray { tools.toolCalls.forEach { add(it) } }
        val report = (loaded ?: Report(
            date = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date()),
            sport = cfg.sport, summary = observations, source = videoPath,
        )).copy(
            stem = savedStem, metrics = metrics, artifacts = artifacts,
            usage = usageJson, calls = callsJson, tools = toolsJson, timeline = timelineJson,
            quality = quality, tt_reading = ttReading,
        )
        store.save(savedStem, report)
        return report
    }

    private suspend fun runReportAgent(
        sport: String, level: String, hand: String, goal: String,
        n: Int, windows: String, observations: String, metricsText: String,
    ) {
        client.stage = "agent writing report"
        val profileLine = "level $level, $hand-handed, working on $goal"
        val history = store.list().take(3)
            .joinToString(" | ") { "${it.date}: focus ${it.focus}; ${it.issues.size} issue(s)" }
            .ifEmpty { "No previous report." }
        val query = Prompts.reportQuery(
            SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date()),
            sport, profileLine, history, n, windows, observations, metricsText,
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
