package com.coachme.android.pipeline

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import java.io.ByteArrayOutputStream
import kotlin.math.abs
import kotlin.math.min

/**
 * Frame sampling, ported from `core/stages/measure/sampling.py`.
 *
 * The real pipeline probes the clip cheaply and spends the frame budget where the image changes
 * (weighted 0.3 + e/peak, first & last kept). Kept platform-native here (MediaMetadataRetriever).
 */
class Sampler(private val context: Context) {
    data class Frame(val t: Double, val bitmap: Bitmap)
    data class Meta(val fps: Double, val duration: Double, val width: Int, val height: Int)

    fun meta(path: String): Meta {
        val r = MediaMetadataRetriever()
        return try {
            r.setDataSource(path)
            fun s(k: Int): String? = r.extractMetadata(k)
            Meta(
                fps = s(MediaMetadataRetriever.METADATA_KEY_CAPTURE_FRAMERATE)?.toDoubleOrNull() ?: 30.0,
                duration = (s(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0L) / 1000.0,
                width = s(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH)?.toIntOrNull() ?: 0,
                height = s(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT)?.toIntOrNull() ?: 0,
            )
        } catch (e: Exception) {
            Meta(30.0, 0.0, 0, 0)
        } finally { r.release() }
    }

    /** A single still image as one frame (posture-only analysis). */
    fun loadImage(path: String): Frame {
        val bmp = BitmapFactory.decodeFile(path) ?: throw IllegalArgumentException("Could not read the image")
        val max = 1000
        val scale = min(max.toFloat() / bmp.width, max.toFloat() / bmp.height)
        val scaled = if (scale < 1f) Bitmap.createScaledBitmap(bmp, (bmp.width * scale).toInt(), (bmp.height * scale).toInt(), true) else bmp
        return Frame(0.0, scaled)
    }

    fun isImage(path: String): Boolean =
        path.substringAfterLast('.', "").lowercase() in setOf("png", "jpg", "jpeg", "bmp", "webp", "gif")

    /** Cheap pre-flight facts + a poster frame, shown on the confirm screen before analysis. */
    data class ClipInspection(
        val durationSec: Double = 0.0,
        val width: Int = 0,
        val height: Int = 0,
        val fps: Double = 0.0,
        val poster: Bitmap? = null,
        val warnings: List<String> = emptyList(),
    )

    fun inspect(path: String): ClipInspection {
        val m = meta(path)
        val poster = if (isImage(path)) runCatching { loadImage(path).bitmap }.getOrNull() else posterFrame(path)
        val warnings = ArrayList<String>()
        if (m.height in 1 until 480) warnings.add("Low resolution — pose detail may be limited.")
        if (m.fps > 0.1 && m.fps < 25) warnings.add("Low frame rate (${m.fps.toInt()} fps) — fast footwork may be missed.")
        if (m.duration > 0.1 && m.duration < 3) warnings.add("Very short clip — a few rallies work better.")
        return ClipInspection(m.duration, m.width, m.height, m.fps, poster, warnings)
    }

    private fun posterFrame(path: String): Bitmap? {
        val r = MediaMetadataRetriever()
        return try {
            r.setDataSource(path)
            r.getFrameAtTime(500_000L, MediaMetadataRetriever.OPTION_CLOSEST_SYNC)
                ?: r.getFrameAtTime(0L, MediaMetadataRetriever.OPTION_CLOSEST)
        } catch (e: Exception) {
            null
        } finally {
            r.release()
        }
    }

    fun duration(path: String): Double {
        val r = MediaMetadataRetriever()
        return try {
            r.setDataSource(path)
            (r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0L) / 1000.0
        } finally { r.release() }
    }

    fun sample(path: String, maxFrames: Int, probeBudget: Int = 64): List<Frame> {
        val r = MediaMetadataRetriever()
        try {
            r.setDataSource(path)
            val durMs = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0L
            val duration = durMs / 1000.0
            if (duration <= 0.0) return emptyList()

            val probes = minOf(probeBudget, 64).coerceAtLeast(2)
            val probeTimes = (0 until probes).map { it * duration / (probes - 1) }
            val probeGray = probeTimes.map { grayOf(frameAt(r, it)) }
            val energies = (1 until probes).map { meanAbsDiff(probeGray[it], probeGray[it - 1]) }
            val counts = allocate(maxFrames, energies)
            val chosen = sortedSetOf<Double>()
            counts.forEachIndexed { i, c ->
                val start = probeTimes[i]; val end = probeTimes[i + 1]
                for (j in 0 until c) chosen.add(start + (j + 1) * (end - start) / (c + 1))
            }
            chosen.add(0.0); chosen.add(duration)

            return chosen.sorted().mapNotNull { t ->
                frameAt(r, t)?.let { Frame(t, it) }
            }
        } finally { r.release() }
    }

    /** Up to [count] frames spread evenly inside a single time window. */
    fun sampleRange(path: String, start: Double, end: Double, count: Int): List<Frame> {
        if (count <= 0 || end <= start) return emptyList()
        val r = MediaMetadataRetriever()
        return try {
            r.setDataSource(path)
            (0 until count).mapNotNull { i ->
                val t = start + (end - start) * i / count
                frameAt(r, t)?.let { Frame(t, it) }
            }
        } catch (e: Exception) {
            emptyList()
        } finally { r.release() }
    }

    /** Up to [count] frames spread evenly across the whole clip (the ball pass). */
    fun sampleEven(path: String, count: Int): List<Frame> {
        val r = MediaMetadataRetriever()
        try {
            r.setDataSource(path)
            val durMs = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0L
            val duration = durMs / 1000.0
            if (duration <= 0.0 || count <= 0) return emptyList()
            return (0 until count).mapNotNull { i ->
                val t = duration * i / maxOf(1, count - 1)
                frameAt(r, t)?.let { Frame(t, it) }
            }
        } finally { r.release() }
    }

    private fun frameAt(r: MediaMetadataRetriever, t: Double): Bitmap? =
        r.getFrameAtTime((t * 1_000_000).toLong(), MediaMetadataRetriever.OPTION_CLOSEST)

    private fun grayOf(bmp: Bitmap?): FloatArray {
        if (bmp == null) return FloatArray(160 * 90)
        val s = Bitmap.createScaledBitmap(bmp, 160, 90, true)
        val px = IntArray(160 * 90); s.getPixels(px, 0, 160, 0, 0, 160, 90)
        return FloatArray(px.size) { i ->
            val p = px[i]
            (0.299f * ((p shr 16) and 0xff) + 0.587f * ((p shr 8) and 0xff) + 0.114f * (p and 0xff))
        }
    }

    private fun meanAbsDiff(a: FloatArray, b: FloatArray): Float {
        var s = 0.0
        for (i in a.indices) s += abs(a[i] - b[i])
        return (s / a.size).toFloat()
    }

    /** Split a budget across intervals, weighted 0.3 + energy/peak (never starve an interval). */
    private fun allocate(count: Int, energies: List<Float>): IntArray {
        val k = energies.size
        if (k == 0 || count <= 0) return IntArray(k)
        val peak = (energies.maxOrNull() ?: 0f).takeIf { it > 0f } ?: 1f
        val weights = energies.map { 0.3f + it / peak }
        val total = weights.sum()
        val raw = weights.map { count * it / total }
        val counts = IntArray(k) { raw[it].toInt() }
        var remainder = count - counts.sum()
        val order = raw.indices.sortedByDescending { raw[it] - counts[it] }
        var i = 0
        while (remainder > 0) { counts[order[i % k]]++; remainder--; i++ }
        return counts
    }

    fun toJpegBase64(bitmap: Bitmap, quality: Int = 82): String {
        val out = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, quality, out)
        return android.util.Base64.encodeToString(out.toByteArray(), android.util.Base64.NO_WRAP)
    }
}
