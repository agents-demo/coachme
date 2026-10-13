package com.topspinreview.android.ui.result

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.media.MediaMetadataRetriever
import android.net.Uri
import androidx.core.content.FileProvider
import androidx.media3.common.MediaItem
import androidx.media3.transformer.Composition
import androidx.media3.transformer.EditedMediaItem
import androidx.media3.transformer.EditedMediaItemSequence
import androidx.media3.transformer.ExportException
import androidx.media3.transformer.ExportResult
import androidx.media3.transformer.Transformer
import com.topspinreview.android.pipeline.GifEncoder
import java.io.File

/** Cut a short clip around a moment (best-effort) and share it. Ported from `integrations/media.py`. */
/** Extract a short range at ~8 fps and encode an animated GIF, then share it. */
fun exportGif(ctx: Context, source: String, startSec: Double, endSec: Double) {
    if (source.isBlank()) return
    val retriever = MediaMetadataRetriever()
    try {
        if (source.startsWith("content:") || source.startsWith("http")) retriever.setDataSource(ctx, Uri.parse(source))
        else retriever.setDataSource(source)
        val fps = 8.0
        val frames = ArrayList<Bitmap>()
        var t = startSec.coerceAtLeast(0.0)
        val end = endSec.coerceAtLeast(t + 0.5)
        while (t <= end && frames.size < 48) {
            retriever.getFrameAtTime((t * 1_000_000).toLong(), MediaMetadataRetriever.OPTION_CLOSEST)?.let { bmp ->
                val w = 320
                val h = (bmp.height * w / bmp.width).coerceAtLeast(2)
                frames.add(Bitmap.createScaledBitmap(bmp, w, h, true))
            }
            t += 1.0 / fps
        }
        if (frames.isEmpty()) return
        val out = File(ctx.cacheDir, "clip_${System.currentTimeMillis()}.gif")
        out.outputStream().use { GifEncoder.encode(frames, (1000 / fps).toInt(), it) }
        val content = FileProvider.getUriForFile(ctx, ctx.packageName + ".fileprovider", out)
        val send = Intent(Intent.ACTION_SEND).apply {
            type = "image/gif"
            putExtra(Intent.EXTRA_STREAM, content)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        ctx.startActivity(Intent.createChooser(send, "Share GIF"))
    } catch (_: Exception) {
    } finally {
        retriever.release()
    }
}

/** Share the original source clip/photo. */
fun shareSource(ctx: Context, source: String) {
    if (source.isBlank()) return
    val uri: Uri = if (source.startsWith("content:") || source.startsWith("http")) Uri.parse(source)
    else FileProvider.getUriForFile(ctx, ctx.packageName + ".fileprovider", File(source))
    val mime = if (source.substringAfterLast('.', "").lowercase() in setOf("png", "jpg", "jpeg", "webp", "gif")) "image/*" else "video/*"
    val send = Intent(Intent.ACTION_SEND).apply {
        type = mime
        putExtra(Intent.EXTRA_STREAM, uri)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    ctx.startActivity(Intent.createChooser(send, "Share clip"))
}

/** Crop to 9:16 and scale to 720×1280, then share (vertical social clip). */
fun exportVertical(ctx: Context, source: String) {
    if (source.isBlank()) return
    val uri: Uri = if (source.startsWith("content:") || source.startsWith("http")) Uri.parse(source) else Uri.fromFile(File(source))
    val edited = EditedMediaItem.Builder(MediaItem.Builder().setUri(uri).build()).setRemoveAudio(true).build()
    val out = File(ctx.cacheDir, "vertical_${System.currentTimeMillis()}.mp4")
    val effects = listOf(
        androidx.media3.effect.Crop(0.34f, 0.34f, 0f, 0f),
        androidx.media3.effect.Presentation.createForHeight(1280),
    )
    val transformer = Transformer.Builder(ctx)
        .setVideoEffects(effects)
        .addListener(object : Transformer.Listener {
            override fun onCompleted(composition: Composition, result: ExportResult) {
                val content = FileProvider.getUriForFile(ctx, ctx.packageName + ".fileprovider", out)
                val send = Intent(Intent.ACTION_SEND).apply {
                    type = "video/mp4"; putExtra(Intent.EXTRA_STREAM, content); addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                ctx.startActivity(Intent.createChooser(send, "Share vertical clip"))
            }
            override fun onError(composition: Composition, result: ExportResult, exception: ExportException) {}
        })
        .build()
    runCatching { transformer.start(edited, out.absolutePath) }
}

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

/** Concatenate up to 3 moments into one highlight reel and share it (`integrations/media.make_reel`). */
fun exportReel(ctx: Context, source: String, times: List<Double>) {
    if (source.isBlank() || times.isEmpty()) return
    val uri: Uri = if (source.startsWith("content:") || source.startsWith("http")) Uri.parse(source) else Uri.fromFile(File(source))
    val clips = times.distinct().take(3).map { t ->
        val startMs = ((t - 1.0) * 1000).toLong().coerceAtLeast(0)
        val endMs = ((t + 2.0) * 1000).toLong().coerceAtLeast(startMs + 500)
        val mi = MediaItem.Builder().setUri(uri)
            .setClippingConfiguration(
                MediaItem.ClippingConfiguration.Builder().setStartPositionMs(startMs).setEndPositionMs(endMs).build(),
            ).build()
        EditedMediaItem.Builder(mi).setRemoveAudio(true).build()
    }
    if (clips.isEmpty()) return
    val out = File(ctx.cacheDir, "reel_${System.currentTimeMillis()}.mp4")
    val sequence = EditedMediaItemSequence(clips)
    val composition: Composition = Composition.Builder(sequence).build()
    val transformer = Transformer.Builder(ctx)
        .addListener(object : Transformer.Listener {
            override fun onCompleted(composition: Composition, result: ExportResult) {
                val content = FileProvider.getUriForFile(ctx, ctx.packageName + ".fileprovider", out)
                val send = Intent(Intent.ACTION_SEND).apply {
                    type = "video/mp4"
                    putExtra(Intent.EXTRA_STREAM, content)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                ctx.startActivity(Intent.createChooser(send, "Share highlight reel"))
            }
            override fun onError(composition: Composition, result: ExportResult, exception: ExportException) {}
        })
        .build()
    runCatching { transformer.start(composition, out.absolutePath) }
}
