package com.topspinreview.android.ui.result

import android.net.Uri
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import com.topspinreview.android.ui.components.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import coil.compose.AsyncImage
import com.topspinreview.android.data.Report
import com.topspinreview.android.ui.components.MediaImage
import com.topspinreview.android.ui.components.SectionLabel
import com.topspinreview.android.ui.components.TspCard
import com.topspinreview.android.ui.components.TspSegmented
import com.topspinreview.android.ui.theme.Accent
import kotlinx.coroutines.delay
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.io.File
import kotlin.math.hypot

/** One drawn shape (normalized 0..1 coords). */
private data class Shape(val type: String, val pts: List<Offset>)

private val TOOLS = listOf("arrow", "circle", "pen", "angle")
private fun toolLabel(t: String) = t.replaceFirstChar { it.uppercase() }
private fun rateLabel(r: Float) = when (r) {
    0.25f -> "0.25×"
    0.5f -> "0.5×"
    else -> "1×"
}
private fun isPhotoSource(s: String) =
    s.substringAfterLast('.', "").lowercase() in setOf("png", "jpg", "jpeg", "bmp", "webp", "gif")

private fun clockLabel(ms: Long): String {
    val s = (ms / 1000).coerceAtLeast(0)
    return "%d:%02d".format(s / 60, s % 60)
}

/** Angle at [b] from normalized points, corrected for the stage's aspect ratio. */
private fun angleDegrees(a: Offset, b: Offset, c: Offset, aspect: Float): Int {
    val v1x = (a.x - b.x) * aspect; val v1y = a.y - b.y
    val v2x = (c.x - b.x) * aspect; val v2y = c.y - b.y
    val dot = v1x * v2x + v1y * v2y
    val n = hypot(v1x.toDouble(), v1y.toDouble()).toFloat() * hypot(v2x.toDouble(), v2y.toDouble()).toFloat()
    return if (n == 0f) 0 else Math.round(Math.acos((dot / n).coerceIn(-1f, 1f).toDouble()) * 180.0 / Math.PI).toInt()
}

/**
 * Video tab (gui2 parity): a Motion / Frames switch. Motion = the clip (paused), a compact
 * drawing + playback control row, and the motion/segments charts. Frames = the stills read.
 */
@Composable
fun VideoTab(
    report: Report,
    onSaveAnnotations: (JsonArray) -> Unit,
    seekMs: Long? = null,
    onSeekConsumed: () -> Unit = {},
) {
    val ctx = LocalContext.current
    val source = report.source
    if (source.isBlank()) {
        Text("No source clip for this session.", Modifier.padding(24.dp))
        return
    }
    val isPhoto = isPhotoSource(source)
    val framesKind = report.artifacts["frames"]
    var view by remember { mutableStateOf(0) } // 0 Motion, 1 Frames

    val sourceUri: Uri = if (source.startsWith("content:") || source.startsWith("http")) Uri.parse(source) else Uri.fromFile(File(source))
    val stageAspect = remember(source) { mediaAspect(ctx, source) }

    val exo = remember(source) {
        if (isPhoto) null
        else ExoPlayer.Builder(ctx).build().apply {
            setMediaItem(MediaItem.fromUri(sourceUri))
            prepare()
            playWhenReady = false
        }
    }
    DisposableEffect(Unit) { onDispose { exo?.release() } }

    val shapes = remember { mutableStateListOf<Shape>() }
    var tool by remember { mutableStateOf("arrow") }
    var drawMode by remember { mutableStateOf(false) }
    var draft by remember { mutableStateOf<List<Offset>>(emptyList()) }
    var status by remember { mutableStateOf("") }
    var dirty by remember { mutableStateOf(false) }
    remember(report.stem) { shapeListOf(report.annotations).forEach { shapes.add(it) }; dirty = false; true }

    Column(Modifier.fillMaxWidth()) {
        if (framesKind != null) {
            Column(Modifier.padding(horizontal = 16.dp, vertical = 8.dp)) {
                TspSegmented(listOf("Motion", "Frames"), view, { view = it })
            }
        }

        Column(
            Modifier.fillMaxWidth().padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            if (view == 1 && framesKind != null) {
                SectionLabel("Frames read")
                Text(
                    "The exact stills the coach looked at.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                TspCard(modifier = Modifier.fillMaxWidth()) { MediaImage(File(framesKind), "Frames read") }
            } else {
            var trimOpen by remember { mutableStateOf(false) }
            var posMs by remember { mutableStateOf(0L) }
            var playing by remember { mutableStateOf(false) }
            var rate by remember { mutableStateOf(1f) }
            val durationMs = remember(source) { (videoDurationSec(ctx, source) * 1000).toLong().coerceAtLeast(1L) }
            LaunchedEffect(exo) { while (exo != null) { posMs = exo.currentPosition; playing = exo.isPlaying; delay(250) } }
            LaunchedEffect(seekMs) {
                if (seekMs != null && exo != null) {
                    exo.seekTo(seekMs)
                    posMs = seekMs
                    exo.play()
                    onSeekConsumed()
                }
            }
            if (!isPhoto) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    SectionLabel("Clip")
                    Spacer(Modifier.weight(1f))
                    Chip("✂ Trim & export") { trimOpen = true }
                }
                if (trimOpen) TrimDialog(report, onDismiss = { trimOpen = false })
            }

            Box(
                Modifier.fillMaxWidth().aspectRatio(stageAspect)
                    .clip(MaterialTheme.shapes.medium)
                    .border(2.dp, MaterialTheme.colorScheme.outline, MaterialTheme.shapes.medium)
                    .background(Color.Black),
            ) {
                if (isPhoto) {
                    AsyncImage(
                        model = File(source),
                        contentDescription = null,
                        contentScale = ContentScale.Fit,
                        modifier = Modifier.matchParentSize(),
                    )
                } else {
                    AndroidView(
                        factory = { PlayerView(it).apply { player = exo; useController = false } },
                        modifier = Modifier.matchParentSize(),
                    )
                }
                Canvas(
                    Modifier.matchParentSize().then(
                        if (drawMode) {
                            Modifier.pointerInput(tool) {
                                if (tool == "angle") {
                                    detectTapGestures { pos ->
                                        exo?.pause()
                                        val p = Offset(pos.x / size.width, pos.y / size.height)
                                        val d = draft + p
                                        if (d.size >= 3) {
                                            shapes.add(Shape("angle", d.take(3))); draft = emptyList(); dirty = true
                                        } else draft = d
                                    }
                                } else {
                                    detectDragGestures(
                                        onDragStart = { s -> exo?.pause(); draft = listOf(Offset(s.x / size.width, s.y / size.height)) },
                                        onDrag = { change, _ ->
                                            val p = Offset(change.position.x / size.width, change.position.y / size.height)
                                            draft = if (tool == "pen") draft + p else listOf(draft.firstOrNull() ?: p, p)
                                        },
                                        onDragEnd = {
                                            if (tool == "pen" && draft.size > 1) { shapes.add(Shape("pen", draft)); dirty = true }
                                            else if (tool != "pen" && draft.size >= 2) { shapes.add(Shape(tool, draft)); dirty = true }
                                            draft = emptyList()
                                        },
                                    )
                                }
                            }
                        } else if (!isPhoto) {
                            Modifier.pointerInput(Unit) {
                                detectTapGestures { exo?.let { p -> if (p.isPlaying) p.pause() else p.play() } }
                            }
                        } else Modifier
                    ),
                ) {
                    shapes.forEach { drawShape(it, size) }
                    if (draft.isNotEmpty()) drawShape(Shape(tool, draft), size)
                }
            }

            // Transport (video) + Draw toggle share one row so Draw isn't stranded.
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                if (!isPhoto) {
                    Chip(if (playing) "Pause" else "Play") { exo?.let { p -> if (p.isPlaying) p.pause() else p.play() } }
                    Chip("⏮") { exo?.let { p -> p.seekTo((p.currentPosition - 33).coerceAtLeast(0L)) } }
                    Chip("⏭") { exo?.let { p -> p.seekTo(p.currentPosition + 33) } }
                    Spacer(Modifier.weight(1f))
                }
                Chip(if (drawMode) "Drawing" else "Draw", selected = drawMode) {
                    drawMode = !drawMode; draft = emptyList(); if (drawMode) exo?.pause()
                }
            }

            if (!isPhoto) {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        clockLabel(posMs),
                        style = MaterialTheme.typography.labelSmall,
                        fontFamily = FontFamily.Monospace,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    SeekBar(posMs = posMs, durationMs = durationMs, onSeek = { exo?.seekTo(it); posMs = it }, modifier = Modifier.weight(1f))
                    Text(
                        clockLabel(durationMs),
                        style = MaterialTheme.typography.labelSmall,
                        fontFamily = FontFamily.Monospace,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    SpeedControl(rate = rate, onRate = { rate = it; exo?.setPlaybackSpeed(it) })
                }
            }

            if (drawMode) {
                ToolSegments(tool) { tool = it; draft = emptyList() }
                if (tool == "angle") {
                    Text(
                        "Click 3 points — the angle is at the 2nd.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Chip("Undo") { if (shapes.isNotEmpty()) { shapes.removeAt(shapes.size - 1); dirty = true } }
                    Chip("Clear") { shapes.clear(); draft = emptyList(); dirty = true }
                    Spacer(Modifier.weight(1f))
                    if (status.isNotBlank()) {
                        Text(status, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    Chip("Save", enabled = dirty) { onSaveAnnotations(toJson(shapes)); status = "Saved"; dirty = false }
                }
            }

            // Motion items (gui2's Motion sub-view): movement over time + active spans.
            val activity = report.metrics["activity"] as? JsonArray
            if (activity != null && activity.size > 1) {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    SectionLabel("Movement over time")
                    Text(
                        "Energy moment-to-moment — a peak is a burst of action.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    TspCard(modifier = Modifier.fillMaxWidth()) {
                        EnergyChart(activity, playhead = posMs / 1000.0, onSeek = { exo?.seekTo((it * 1000).toLong()) })
                    }
                }
            }
            val segs = (report.metrics["ball"] as? JsonObject)?.get("segments") as? JsonArray
            if (segs != null && segs.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    SectionLabel("Active spans")
                    TspCard(modifier = Modifier.fillMaxWidth()) {
                        SegmentsBar(segs, lastT(activity ?: JsonArray(emptyList())), playhead = posMs / 1000.0, onSeek = { exo?.seekTo((it * 1000).toLong()) })
                    }
                }
            }
            }
        }
    }
}

@Composable
private fun Chip(label: String, selected: Boolean = false, enabled: Boolean = true, onClick: () -> Unit) {
    Box(
        Modifier
            .clip(RoundedCornerShape(8.dp))
            .background(if (selected) Accent.copy(alpha = 0.16f) else Color.Transparent)
            .border(2.dp, if (selected) Accent else MaterialTheme.colorScheme.outline, RoundedCornerShape(8.dp))
            .clickable(enabled = enabled) { onClick() }
            .padding(horizontal = 8.dp, vertical = 4.dp),
    ) {
        Text(
            label,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.SemiBold,
            maxLines = 1,
            color = when {
                !enabled -> MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                selected -> Accent
                else -> MaterialTheme.colorScheme.onSurface
            },
        )
    }
}

/** A slim, tappable/draggable scrubber (no media3 overlay). */
@Composable
private fun SeekBar(posMs: Long, durationMs: Long, onSeek: (Long) -> Unit, modifier: Modifier = Modifier) {
    val track = MaterialTheme.colorScheme.surfaceVariant
    val fill = Accent
    Box(
        modifier
            .height(28.dp)
            .pointerInput(durationMs) {
                detectTapGestures { off -> onSeek(((off.x / size.width).coerceIn(0f, 1f) * durationMs).toLong()) }
            }
            .pointerInput(durationMs) {
                detectDragGestures { change, _ -> onSeek(((change.position.x / size.width).coerceIn(0f, 1f) * durationMs).toLong()) }
            },
    ) {
        Canvas(Modifier.fillMaxSize()) {
            val cy = size.height / 2f
            val trackH = 6f
            val frac = if (durationMs > 0) (posMs.toFloat() / durationMs).coerceIn(0f, 1f) else 0f
            val corner = androidx.compose.ui.geometry.CornerRadius(trackH / 2f)
            drawRoundRect(track, Offset(0f, cy - trackH / 2f), Size(size.width, trackH), corner)
            drawRoundRect(fill, Offset(0f, cy - trackH / 2f), Size(size.width * frac, trackH), corner)
            drawCircle(fill, radius = trackH * 1.4f, center = Offset(size.width * frac, cy))
        }
    }
}

/** A full-width segmented tool picker (Arrow / Circle / Pen / Angle) that always fits. */
@Composable
private fun ToolSegments(tool: String, onTool: (String) -> Unit) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(8.dp)).border(2.dp, MaterialTheme.colorScheme.outline, RoundedCornerShape(8.dp)),
    ) {
        TOOLS.forEach { t ->
            val sel = tool == t
            Box(
                Modifier
                    .weight(1f)
                    .background(if (sel) Accent.copy(alpha = 0.16f) else Color.Transparent)
                    .clickable { onTool(t) }
                    .padding(vertical = 6.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    toolLabel(t),
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    color = if (sel) Accent else MaterialTheme.colorScheme.onSurface,
                )
            }
        }
    }
}

/** A compact segmented speed control (0.25× / 0.5× / 1×) that fits a single row. */
@Composable
private fun SpeedControl(rate: Float, onRate: (Float) -> Unit) {
    Row(
        Modifier.clip(RoundedCornerShape(8.dp)).border(2.dp, MaterialTheme.colorScheme.outline, RoundedCornerShape(8.dp)),
    ) {
        listOf(0.25f, 0.5f, 1f).forEach { r ->
            val sel = rate == r
            Box(
                Modifier
                    .background(if (sel) Accent.copy(alpha = 0.16f) else Color.Transparent)
                    .clickable { onRate(r) }
                    .padding(horizontal = 8.dp, vertical = 4.dp),
            ) {
                Text(
                    rateLabel(r),
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    color = if (sel) Accent else MaterialTheme.colorScheme.onSurface,
                )
            }
        }
    }
}

@Composable
private fun TrimDialog(report: Report, onDismiss: () -> Unit) {
    val ctx = LocalContext.current
    val duration = remember(report.stem) { videoDurationSec(ctx, report.source).coerceAtLeast(1.0) }
    var start by remember { mutableStateOf(0f) }
    var end by remember { mutableStateOf(duration.toFloat()) }
    var gif by remember { mutableStateOf(false) }
    var vertical by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Trim & export") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    "Pick a range and share it as a clip.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text("Start  %.1fs".format(start), style = MaterialTheme.typography.labelSmall)
                Slider(
                    value = start,
                    onValueChange = { start = it.coerceIn(0f, (end - 0.5f).coerceAtLeast(0f)) },
                    valueRange = 0f..duration.toFloat(),
                )
                Text("End  %.1fs".format(end), style = MaterialTheme.typography.labelSmall)
                Slider(
                    value = end,
                    onValueChange = { end = it.coerceIn(start + 0.5f, duration.toFloat()) },
                    valueRange = 0f..duration.toFloat(),
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = gif, onCheckedChange = { gif = it })
                    Text("GIF", style = MaterialTheme.typography.bodyMedium)
                    Spacer(Modifier.width(12.dp))
                    Checkbox(checked = vertical, onCheckedChange = { vertical = it }, enabled = !gif)
                    Text("Vertical 9:16", style = MaterialTheme.typography.bodyMedium)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                trimShare(ctx, report.source, start.toDouble(), end.toDouble(), vertical, gif)
                onDismiss()
            }) { Text("Export") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}

private fun DrawScope.drawShape(shape: Shape, size: Size) {
    val color = Color(0xFFF97316)
    val stroke = Stroke(width = 6f)
    fun o(p: Offset) = Offset(p.x * size.width, p.y * size.height)
    when (shape.type) {
        "pen" -> {
            val path = Path()
            shape.pts.forEachIndexed { i, p -> if (i == 0) path.moveTo(o(p).x, o(p).y) else path.lineTo(o(p).x, o(p).y) }
            drawPath(path, color, style = stroke)
        }
        "line" -> if (shape.pts.size >= 2) drawLine(color, o(shape.pts[0]), o(shape.pts[1]), strokeWidth = 6f)
        "arrow" -> if (shape.pts.size >= 2) {
            val a = o(shape.pts[0]); val b = o(shape.pts[1])
            drawLine(color, a, b, strokeWidth = 6f)
            val ang = Math.atan2((b.y - a.y).toDouble(), (b.x - a.x).toDouble())
            val len = 28.0
            for (d in listOf(ang - 0.5, ang + 0.5)) {
                drawLine(color, b, Offset((b.x - len * Math.cos(d)).toFloat(), (b.y - len * Math.sin(d)).toFloat()), strokeWidth = 6f)
            }
        }
        "circle" -> if (shape.pts.size >= 2) {
            val c = o(shape.pts[0]); val e = o(shape.pts[1])
            drawCircle(color, radius = hypot((e.x - c.x).toDouble(), (e.y - c.y).toDouble()).toFloat(), center = c, style = stroke)
        }
        "angle" -> if (shape.pts.size >= 3) {
            val m = o(shape.pts[1]); val a = o(shape.pts[0]); val c = o(shape.pts[2])
            drawLine(color, m, a, strokeWidth = 6f); drawLine(color, m, c, strokeWidth = 6f)
            drawCircle(color, radius = 5f, center = m)
            val deg = angleDegrees(shape.pts[0], shape.pts[1], shape.pts[2], size.width / size.height)
            val paint = android.graphics.Paint().apply {
                this.color = 0xFFF97316.toInt()
                textSize = (size.height * 0.06f).coerceIn(24f, 64f)
                isAntiAlias = true
                textAlign = android.graphics.Paint.Align.CENTER
                typeface = android.graphics.Typeface.DEFAULT_BOLD
                setShadowLayer(4f, 0f, 0f, android.graphics.Color.BLACK)
            }
            drawContext.canvas.nativeCanvas.drawText("$deg°", m.x, m.y - 22f, paint)
        }
    }
}

private fun toJson(shapes: List<Shape>): JsonArray = buildJsonArray {
    shapes.forEach { s ->
        add(buildJsonObject {
            put("type", s.type)
            put("color", "#f97316")
            when (s.type) {
                "pen", "angle" -> put("points", buildJsonArray {
                    s.pts.forEach { p -> add(buildJsonArray { add(JsonPrimitive(p.x.toDouble())); add(JsonPrimitive(p.y.toDouble())) }) }
                })
                else -> {
                    val a = s.pts.getOrNull(0) ?: Offset.Zero
                    val b = s.pts.getOrNull(1) ?: Offset.Zero
                    put("x1", a.x.toDouble()); put("y1", a.y.toDouble())
                    put("x2", b.x.toDouble()); put("y2", b.y.toDouble())
                }
            }
        })
    }
}

private fun shapeListOf(annots: JsonArray): List<Shape> = annots.mapNotNull { el ->
    val o = el as? JsonObject ?: return@mapNotNull null
    val type = o["type"]?.toString()?.trim('"') ?: return@mapNotNull null
    if (type == "pen" || type == "angle") {
        val pts = (o["points"] as? JsonArray)?.mapNotNull { p ->
            val a = p as? JsonArray ?: return@mapNotNull null
            val x = a.getOrNull(0)?.toString()?.toFloatOrNull() ?: return@mapNotNull null
            val y = a.getOrNull(1)?.toString()?.toFloatOrNull() ?: return@mapNotNull null
            Offset(x, y)
        } ?: emptyList()
        Shape(type, pts)
    } else {
        val x1 = o["x1"]?.toString()?.toFloatOrNull() ?: return@mapNotNull null
        val y1 = o["y1"]?.toString()?.toFloatOrNull() ?: return@mapNotNull null
        val x2 = o["x2"]?.toString()?.toFloatOrNull() ?: return@mapNotNull null
        val y2 = o["y2"]?.toString()?.toFloatOrNull() ?: return@mapNotNull null
        Shape(type, listOf(Offset(x1, y1), Offset(x2, y2)))
    }
}
