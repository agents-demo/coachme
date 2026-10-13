package com.topspinreview.android.pipeline

import android.content.Context
import android.graphics.Bitmap
import android.media.MediaMetadataRetriever
import java.io.ByteArrayOutputStream
import kotlin.math.abs

/**
 * Frame sampling, ported from `core/stages/measure/sampling.py`.
 *
 * The real pipeline probes the clip cheaply and spends the frame budget where the image changes
 * (weighted 0.3 + e/peak, first & last kept). Kept platform-native here (MediaMetadataRetriever).
 */
class Sampler(private val context: Context) {
    data class Frame(val t: Double, val bitmap: Bitmap)

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
