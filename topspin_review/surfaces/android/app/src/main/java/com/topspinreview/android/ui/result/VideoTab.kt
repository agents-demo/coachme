package com.topspinreview.android.ui.result

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.FileProvider
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.transformer.Composition
import androidx.media3.transformer.EditedMediaItem
import androidx.media3.transformer.ExportException
import androidx.media3.transformer.ExportResult
import androidx.media3.transformer.Transformer
import androidx.media3.ui.PlayerView
import com.topspinreview.android.data.Report
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.io.File

/**
 * Video tab: the player, a freehand telestration overlay (saved as annotations), and a
 * trim-to-mp4 "export & share". GIF / vertical / highlight-reel / share-card are P6.
 */
@Composable
fun VideoTab(report: Report, onSaveAnnotations: (JsonArray) -> Unit) {
    val ctx = LocalContext.current
    val source = report.source
    if (source.isBlank()) {
        Text("No source clip for this session.", Modifier.padding(24.dp))
        return
    }
    val uri: Uri = if (source.startsWith("content:") || source.startsWith("http")) Uri.parse(source) else Uri.fromFile(File(source))

    val exo = remember {
        ExoPlayer.Builder(ctx).build().apply {
            setMediaItem(MediaItem.fromUri(uri)); prepare(); playWhenReady = true
        }
    }
    DisposableEffect(Unit) { onDispose { exo.release() } }

    val strokes = remember { mutableStateListOf<MutableList<Offset>>() } // normalized 0..1
    var status by remember { mutableStateOf("") }

    Column(Modifier.fillMaxWidth().padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Box(
            Modifier.fillMaxWidth().height(240.dp).background(Color.Black),
        ) {
            AndroidView(factory = { PlayerView(it).apply { player = exo; useController = true } }, modifier = Modifier.matchParentSize())
            Canvas(
                Modifier.matchParentSize().pointerInput(Unit) {
                    detectDragGestures(
                        onDragStart = { strokes.add(mutableListOf(it)) },
                        onDrag = { change, _ ->
                            val s = strokes.lastOrNull() ?: return@detectDragGestures
                            s.add(Offset(change.position.x / size.width, change.position.y / size.height))
                        },
                    )
                },
            ) {
                strokes.forEach { s ->
                    for (i in 1 until s.size) {
                        drawLine(
                            Color(0xFFF97316),
                            Offset(s[i - 1].x * size.width, s[i - 1].y * size.height),
                            Offset(s[i].x * size.width, s[i].y * size.height),
                            strokeWidth = 6f,
                        )
                    }
                }
                // existing saved annotations (pen only)
                (report.annotations).forEach { el ->
                    val o = el as? kotlinx.serialization.json.JsonObject ?: return@forEach
                    if (o["type"]?.toString()?.trim('"') != "pen") return@forEach
                    val pts = o["points"] as? JsonArray ?: return@forEach
                    val list = pts.mapNotNull { p ->
                        val a = p as? JsonArray ?: return@mapNotNull null
                        val x = a.getOrNull(0)?.toString()?.toFloatOrNull() ?: return@mapNotNull null
                        val y = a.getOrNull(1)?.toString()?.toFloatOrNull() ?: return@mapNotNull null
                        Offset(x * size.width, y * size.height)
                    }
                    for (i in 1 until list.size) drawLine(Color(0xFFF97316), list[i - 1], list[i], strokeWidth = 6f)
                }
            }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            TextButton(onClick = { exo.seekTo((exo.currentPosition - 33).coerceAtLeast(0L)) }) { Text("−1f") }
            TextButton(onClick = { exo.seekTo(exo.currentPosition + 33) }) { Text("+1f") }
            TextButton(onClick = { exo.setPlaybackSpeed(0.25f) }) { Text("0.25×") }
            TextButton(onClick = { exo.setPlaybackSpeed(0.5f) }) { Text("0.5×") }
            TextButton(onClick = { exo.setPlaybackSpeed(1f) }) { Text("1×") }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TextButton(onClick = { strokes.clear() }) { Text("Clear") }
            Button(onClick = {
                val annots = buildJsonArray {
                    strokes.forEach { s ->
                        add(buildJsonObject {
                            put("type", "pen")
                            put("color", "#f97316")
                            put("points", buildJsonArray {
                                s.forEach { pt -> add(buildJsonArray { add(JsonPrimitive(pt.x.toDouble())); add(JsonPrimitive(pt.y.toDouble())) }) }
                            })
                        })
                    }
                }
                onSaveAnnotations(annots)
                status = "Annotations saved"
            }) { Text("Save drawings") }
        }

        Button(
            onClick = { status = exportAndShare(ctx, exo, uri) },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Trim first 10s → mp4 (then share)") }
        if (status.isNotBlank()) Text(status, style = MaterialTheme.typography.bodySmall)
    }
}

private fun exportAndShare(ctx: android.content.Context, exo: ExoPlayer, uri: Uri): String {
    val endMs = (if (exo.duration > 0) exo.duration else 10_000L).coerceAtMost(10_000L)
    val mediaItem = MediaItem.Builder().setUri(uri)
        .setClippingConfiguration(
            MediaItem.ClippingConfiguration.Builder().setStartPositionMs(0).setEndPositionMs(endMs).build(),
        ).build()
    val out = File(ctx.cacheDir, "trim_${System.currentTimeMillis()}.mp4")
    val transformer = Transformer.Builder(ctx)
        .addListener(object : Transformer.Listener {
            override fun onCompleted(composition: Composition, result: ExportResult) {
                val content = FileProvider.getUriForFile(ctx, ctx.packageName + ".fileprovider", out)
                val send = Intent(Intent.ACTION_SEND).apply {
                    type = "video/mp4"
                    putExtra(Intent.EXTRA_STREAM, content)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                ctx.startActivity(Intent.createChooser(send, "Share clip"))
            }
            override fun onError(composition: Composition, result: ExportResult, exception: ExportException) {
                // best effort
            }
        })
        .build()
    return try {
        transformer.start(EditedMediaItem.Builder(mediaItem).setRemoveAudio(true).build(), out.absolutePath)
        "Exported: ${out.name}"
    } catch (e: Exception) {
        "Export failed: ${e.message}"
    }
}
