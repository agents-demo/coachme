package com.topspinreview.android.ui.result

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import androidx.media3.common.MediaItem
import androidx.media3.transformer.Composition
import androidx.media3.transformer.EditedMediaItem
import androidx.media3.transformer.ExportException
import androidx.media3.transformer.ExportResult
import androidx.media3.transformer.Transformer
import java.io.File

/** Cut a short clip around a moment (best-effort) and share it. Ported from `integrations/media.py`. */
fun clipAndShare(ctx: Context, source: String, startSec: Double, endSec: Double) {
    if (source.isBlank()) return
    val uri: Uri = if (source.startsWith("content:") || source.startsWith("http")) Uri.parse(source) else Uri.fromFile(File(source))
    val startMs = (startSec * 1000).toLong().coerceAtLeast(0)
    val endMs = (endSec * 1000).toLong().coerceAtLeast(startMs + 500)
    val out = File(ctx.cacheDir, "clip_${System.currentTimeMillis()}.mp4")
    val mediaItem = MediaItem.Builder().setUri(uri)
        .setClippingConfiguration(
            MediaItem.ClippingConfiguration.Builder().setStartPositionMs(startMs).setEndPositionMs(endMs).build(),
        ).build()
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
            override fun onError(composition: Composition, result: ExportResult, exception: ExportException) {}
        })
        .build()
    runCatching { transformer.start(EditedMediaItem.Builder(mediaItem).setRemoveAudio(true).build(), out.absolutePath) }
}
