package com.topspinreview.android.pipeline

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import com.topspinreview.android.data.CallRecord
import com.topspinreview.android.data.FrameRef
import com.topspinreview.android.data.LandmarkFrame
import com.topspinreview.android.data.Report
import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.data.RunCheckpoint
import com.topspinreview.android.data.RunStore
import com.topspinreview.android.data.SettingsStore
import com.topspinreview.android.llm.CallInfo
import com.topspinreview.android.llm.DeepSeekClient
import com.topspinreview.android.llm.Prompts
import com.topspinreview.android.llm.ReportTools
import com.topspinreview.android.llm.ToolCall
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.first
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
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

private const val CAVEAT_VISION_IMAGE = "The vision pass failed, so this photo's report may be less specific."
private const val CAVEAT_VISION_OVERVIEW = "The overview pass failed, so findings are based on motion data only."
private const val CAVEAT_VISION_DETAIL = "The detail pass failed, so the findings may be thinner than usual."
private const val CAVEAT_VERIFY = "The double-check pass was skipped, so an issue may be flagged in error."

/**
 * The pipeline: measure → observe → coach (mock-free MVP slice).
 *
 * Renders a contact sheet, does the two vision passes, then runs the report agent loop
 * (tools from [ReportTools]) and returns the saved [Report]. See docs/ANDROID_PLAN.md §7.
 *
 * Every stage checkpoints its outputs to a [RunStore]; pass `resume = true` to continue a
 * previously interrupted run from the first unfinished stage instead of starting over.
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
    private val runStore: RunStore,
) {
    /** Whether an interrupted run exists for this clip (drives the "Resume" affordance). */
    fun hasCheckpoint(videoPath: String): Boolean = runStore.exists(File(videoPath).nameWithoutExtension)

    /** The newest interrupted run whose source still exists and has no report yet (the entry banner). */
    fun pendingRun(): PendingRun? =
        runStore.list()
            .firstOrNull { File(it.videoPath).exists() && !store.exists(it.stem) }
            ?.let { toPendingRun(it) }

    /** A specific interrupted run by stem (used when resuming from the Sessions screen). */
    fun pendingRunFor(stem: String): PendingRun? =
        runStore.load(stem)?.takeIf { File(it.videoPath).exists() }?.let { toPendingRun(it) }

    private fun toPendingRun(cp: RunCheckpoint): PendingRun {
        val plan = Stages.plan(cp.isImage)
        return PendingRun(
            videoPath = cp.videoPath,
            stem = cp.stem,
            isImage = cp.isImage,
            region = cp.region,
            doneCount = plan.count { it in cp.completed },
            totalCount = plan.size,
        )
    }

    /** Forget an interrupted run (the "Discard" action). */
    fun discardRun(stem: String) = runStore.clear(stem)

    suspend fun analyze(
        videoPath: String,
        regionBox: FloatArray? = null,
        onStage: (StageInfo) -> Unit = {},
        onWarning: (String) -> Unit = {},
        resume: Boolean = false,
    ): Report {
        val cfg = settings.flow.first()

        val stem = File(videoPath).nameWithoutExtension
        val cp = if (resume) runStore.load(stem) else null
        if (!resume && cp == null) runStore.clear(stem)
        val done = (cp?.completed ?: emptyList()).toMutableSet()

        tools.beginRun(stem)
        client.calls.clear()
        cp?.let { c ->
            client.restoreCalls(c.calls.map { CallInfo(it.stage, it.model, it.promptTokens, it.completionTokens, it.seconds) })
            tools.restoreToolCalls(c.toolCalls.mapNotNull { it as? JsonObject })
        }

        fun since(ns: Long) = (System.nanoTime() - ns) / 1e9
        val timeline = linkedMapOf<String, Double>()
        cp?.timeline?.let { timeline.putAll(it) }

        val isImage = cp?.isImage ?: sampler.isImage(videoPath)
        val plan = Stages.plan(isImage)
        fun emit(name: String) {
            val idx = plan.indexOf(name).coerceAtLeast(0)
            onStage(StageInfo(name, idx, plan.size, (idx + 1f) / plan.size, plan.getOrNull(idx + 1)))
        }

        val warnings = (cp?.warnings ?: emptyList()).toMutableList()
        fun warn(message: String) {
            if (message !in warnings) {
                warnings += message
                onWarning(message)
            }
        }

        // Reflect already-completed progress in the UI when resuming.
        plan.lastOrNull { it in done }?.let { emit(it) }
        warnings.forEach { onWarning(it) }

        // --- run state (restored from the checkpoint where available) -------------
        var frames: List<Sampler.Frame> =
            cp?.frames?.mapNotNull { ref -> runStore.loadBitmap(stem, ref.file)?.let { Sampler.Frame(ref.t, it) } } ?: emptyList()
        if (frames.isEmpty() && done.contains("frames")) done.remove("frames")

        var frameRefs: List<FrameRef> = cp?.frames ?: emptyList()
        var motionFile: String? = cp?.motionFile
        var positionFile: String? = cp?.positionFile

        var measured: Measured? = cp?.let { c ->
            if (c.measuredJson.isEmpty()) null
            else Measured(
                json = c.measuredJson,
                motionMap = runStore.loadBitmap(stem, c.motionFile),
                positionMap = runStore.loadBitmap(stem, c.positionFile),
                activity = c.activity.map { it.getOrElse(0) { 0.0 } to it.getOrElse(1) { 0.0 } },
            )
        }

        var poseSeq: List<Pose.PoseFrame> = cp?.pose?.map { it.toPoseFrame() } ?: emptyList()
        var ballJson: JsonObject = cp?.ballJson ?: JsonObject(emptyMap())
        var metrics: JsonObject = cp?.metrics ?: JsonObject(emptyMap())
        var metricsText: String = cp?.metricsText ?: ""
        var quality: JsonObject = cp?.quality ?: JsonObject(emptyMap())
        var ttReading: JsonObject = cp?.ttReading ?: JsonObject(emptyMap())
        var sheetB64: String = cp?.sheetB64 ?: ""
        var sheetBitmap: Bitmap? = null
        var artifacts: LinkedHashMap<String, String> = LinkedHashMap(cp?.artifacts ?: emptyMap())
        var windows: JsonArray = cp?.windows ?: JsonArray(emptyList())
        var windowLabel: String = cp?.windowLabel ?: "none"
        var observations: String = cp?.observations ?: ""
        var savedStem: String? = cp?.savedStem
        var loaded: Report? = cp?.loadedReport

        fun persist() {
            runStore.save(
                RunCheckpoint(
                    videoPath = videoPath,
                    stem = stem,
                    isImage = isImage,
                    region = regionBox?.toList() ?: emptyList(),
                    completed = done.toList(),
                    frames = frameRefs,
                    measuredJson = measured?.json ?: JsonObject(emptyMap()),
                    activity = measured?.activity?.map { listOf(it.first, it.second) } ?: emptyList(),
                    motionFile = motionFile,
                    positionFile = positionFile,
                    pose = poseSeq.map { it.toLandmarkFrame() },
                    ballJson = ballJson,
                    metrics = metrics,
                    metricsText = metricsText,
                    quality = quality,
                    ttReading = ttReading,
                    sheetB64 = sheetB64,
                    artifacts = artifacts,
                    windows = windows,
                    windowLabel = windowLabel,
                    observations = observations,
                    savedStem = savedStem,
                    loadedReport = loaded,
                    warnings = warnings.toList(),
                    timeline = timeline,
                    calls = client.calls.map { CallRecord(it.stage, it.model, it.promptTokens, it.completionTokens, it.seconds) },
                    toolCalls = buildJsonArray { tools.toolCalls.forEach { add(it) } },
                ),
            )
        }

        // --- stages ----------------------------------------------------------------
        if (!done.contains("frames")) {
            emit("Pick frames")
            val tFrames = System.nanoTime()
            val f = if (isImage) listOf(sampler.loadImage(videoPath)) else sampler.sample(videoPath, cfg.maxFrames)
            timeline["sampling frames"] = since(tFrames)
            require(f.isNotEmpty()) { "No frames could be extracted." }
            frames = f
            frameRefs = f.mapIndexed { i, fr -> FrameRef(fr.t, runStore.saveBitmap(stem, "frame_$i", fr.bitmap)) }
            done += "frames"
            persist()
        }

        if (!isImage && !done.contains("measure")) {
            emit("Measure movement")
            val t = System.nanoTime()
            val m = Metrics.analyze(frames, regionBox)
            timeline["measuring motion"] = since(t)
            measured = m
            motionFile = m.motionMap?.let { runStore.saveBitmap(stem, "motion_map", it) }
            positionFile = m.positionMap?.let { runStore.saveBitmap(stem, "position_map", it) }
            done += "measure"
            persist()
        }

        if (!isImage && !done.contains("pose")) {
            emit("Estimate pose")
            val t = System.nanoTime()
            poseSeq = pose.detect(frames)
            timeline["estimating pose"] = since(t)
            done += "pose"
            persist()
        }

        if (!isImage && measured != null && !done.contains("ball")) {
            emit("Track ball")
            val t = System.nanoTime()
            // Dense pass: spread the ball budget across the whole clip (the ball is on screen briefly).
            val ballFrames = sampler.sampleEven(videoPath, 60)
            ballJson = if (ballFrames.isNotEmpty())
                ball.process(ballFrames.map { it.t }, ball.detect(ballFrames), Metrics.activityPairs(ballFrames))
            else JsonObject(emptyMap())
            timeline["tracking ball"] = since(t)
            done += "ball"
            persist()
        }

        if (!done.contains("inputs")) {
            val m = measured
            metrics = if (m == null) JsonObject(emptyMap()) else JsonObject(
                m.json + mapOf(
                    "pose_summary" to pose.summarize(poseSeq),
                    "pose3d_summary" to pose.summarize3d(poseSeq),
                    "pose3d" to pose.series3d(poseSeq),
                    "pose_angles" to pose.anglesSeries(poseSeq, frames.map { it.t }),
                    "strokes" to pose.strokes(poseSeq, frames),
                    "footwork" to pose.footwork(poseSeq),
                    "ball" to ballJson,
                ),
            )
            metricsText = Metrics.text(metrics)
            quality = Quality.evaluate(sampler.meta(videoPath), frames.size, metrics)
            (quality["warnings"] as? JsonArray)?.forEach { el ->
                val text = el.toString().trim('"')
                if (text.isNotBlank()) warn(text)
            }
            ttReading = com.topspinreview.android.domain.GameReading.summarize(metrics)
            val sheet = contactSheet(frames)
            sheetBitmap = sheet
            sheetB64 = sampler.toJpegBase64(sheet)
            done += "inputs"
            persist()
        }

        if (!done.contains("render")) {
            emit("Render images")
            val m = measured
            val sheet = sheetBitmap ?: contactSheet(frames)
            sheetBitmap = sheet
            if (sheetB64.isBlank()) sheetB64 = sampler.toJpegBase64(sheet)
            val poseOverlay = if (poseSeq.isNotEmpty()) pose.overlay(frames, poseSeq) else null
            artifacts = linkedMapOf()
            artifacts["frames"] = store.saveArtifact(stem, "frames", sheet)
            m?.motionMap?.let { artifacts["motion"] = store.saveArtifact(stem, "motion", it) }
            m?.positionMap?.let { artifacts["heatmap"] = store.saveArtifact(stem, "heatmap", it) }
            poseOverlay?.let { artifacts["pose"] = store.saveArtifact(stem, "pose", it) }
            if (ballJson.isNotEmpty()) ball.overlay(frames.getOrNull(frames.size / 2)?.bitmap, ballJson)?.let { artifacts["ball"] = store.saveArtifact(stem, "ball", it) }
            done += "render"
            persist()
        }

        val motionBmp: Bitmap? = loadPath(artifacts["motion"])
        val poseBmp: Bitmap? = loadPath(artifacts["pose"])

        if (!done.contains("vision")) {
            warnings.remove(CAVEAT_VISION_IMAGE)
            warnings.remove(CAVEAT_VISION_OVERVIEW)
            warnings.remove(CAVEAT_VISION_DETAIL)
            var visionOk = true
            if (isImage) {
                emit("Review image")
                client.stage = "vision: reviewing image"
                windows = JsonArray(emptyList())
                observations = try {
                    val out = client.vision(
                        Prompts.VISION_AGENT_SYSTEM,
                        Prompts.still(cfg.sport, cfg.level, cfg.hand, cfg.goal),
                        listOf(sheetB64),
                    )
                    extractJson(out)?.jsonObject?.get("observations")?.jsonPrimitive?.content.orEmpty()
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                visionOk = false
                warn(CAVEAT_VISION_IMAGE)
                ""
            }
            } else {
                windows = try {
                    emit("First look")
                    client.stage = "vision: overview"
                    val coarse = client.vision(
                        Prompts.VISION_AGENT_SYSTEM,
                        Prompts.coarse(frames.size, cfg.sport, cfg.level, cfg.hand, cfg.goal, metricsText, sampler.duration(videoPath)),
                        listOf(sheetB64),
                    )
                    extractJson(coarse)?.jsonObject?.get("attentive_windows")?.jsonArray ?: JsonArray(emptyList())
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                visionOk = false
                warn(CAVEAT_VISION_OVERVIEW)
                JsonArray(emptyList())
            }
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
                    emit("Detailed findings")
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
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                visionOk = false
                warn(CAVEAT_VISION_DETAIL)
                ""
            }
            }
            if (visionOk) done += "vision"
            persist()
        }

        if (!done.contains("report")) {
            emit("Write report")
            runReportAgent(cfg.sport, cfg.level, cfg.hand, cfg.goal, frames.size, windowLabel, observations, metricsText)
            savedStem = tools.lastSavedStem ?: stem
            loaded = store.load(savedStem)
            done += "report"
            persist()
        }

        if (!done.contains("verify")) {
            warnings.remove(CAVEAT_VERIFY)
            var verifyOk = true
            loaded?.let { rep ->
                if (rep.issues.isNotEmpty()) {
                    emit("Double-check")
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
                    }.onFailure { e ->
                        if (e is CancellationException) throw e
                        verifyOk = false
                        warn(CAVEAT_VERIFY)
                    }
                }
            }
            if (verifyOk) done += "verify"
            persist()
        }

        val finalStem = savedStem ?: stem
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
            stem = finalStem, source = videoPath, metrics = metrics, artifacts = artifacts,
            usage = usageJson, calls = callsJson, tools = toolsJson, timeline = timelineJson,
            quality = quality, tt_reading = ttReading, warnings = warnings.toList(),
        )
        store.save(finalStem, report)
        // If a supplementary stage still needs a retry, keep the checkpoint so the run can be
        // resumed from that exact step; otherwise the run is complete — clean up.
        val required = buildList {
            add("frames")
            if (!isImage) { add("measure"); add("pose"); add("ball") }
            add("inputs"); add("render"); add("vision"); add("report"); add("verify")
        }
        if (required.all { it in done }) runStore.clear(stem)
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

    private fun loadPath(path: String?): Bitmap? {
        if (path.isNullOrBlank()) return null
        val f = File(path)
        return if (f.exists()) BitmapFactory.decodeFile(f.absolutePath) else null
    }

    private fun extractJson(text: String): kotlinx.serialization.json.JsonElement? = runCatching {
        val start = text.indexOf('{'); val end = text.lastIndexOf('}')
        if (start < 0 || end <= start) null else json.parseToJsonElement(text.substring(start, end + 1))
    }.getOrNull()

    private fun Pose.PoseFrame.toLandmarkFrame() = LandmarkFrame(
        lm = lm?.map { it.toList() },
        world = world?.map { it.toList() },
    )

    private fun LandmarkFrame.toPoseFrame() = Pose.PoseFrame(
        lm = lm?.map { it.toFloatArray() },
        world = world?.map { it.toFloatArray() },
    )
}
