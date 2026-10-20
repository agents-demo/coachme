package com.coachme.android.data

import android.content.Context
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Fetch a video from a link (YouTube and anything else yt-dlp supports) into a local file,
 * so it can go through the normal on-device pipeline. Backed by the bundled yt-dlp + ffmpeg.
 */
object Youtube {
    private const val PREFS = "coachme.youtube"
    private const val KEY_UPDATED_AT = "ytdlp_updated_at"

    /** YouTube breaks old yt-dlp builds regularly, so refresh the binary now and then. */
    private const val UPDATE_INTERVAL_DAYS = 7L

    private val initLock = Any()

    @Volatile
    private var ready = false

    /** Warm up the (slow, one-off) yt-dlp environment off the main thread. Safe to ignore errors. */
    fun warmUp(context: Context) {
        val app = context.applicationContext
        Thread { runCatching { initBlocking(app) } }.start()
    }

    /**
     * Initialize the bundled yt-dlp **and** ffmpeg, then refresh yt-dlp if it's getting old.
     * Idempotent, and retries if a previous attempt failed (a failed init leaves the library in a
     * "not initialized" state). ffmpeg is required to merge the separate video/audio streams.
     */
    private fun initBlocking(app: Context) {
        if (ready) return
        synchronized(initLock) {
            if (ready) return
            YoutubeDL.getInstance().init(app)
            FFmpeg.getInstance().init(app)
            maybeUpdate(app, force = false)
            ready = true
        }
    }

    private suspend fun ensureInit(context: Context) {
        if (ready) return
        withContext(Dispatchers.IO) {
            try {
                initBlocking(context.applicationContext)
            } catch (e: Exception) {
                error("Couldn't set up the video downloader: ${e.message ?: "unknown error"}")
            }
        }
    }

    /** Download the bundled yt-dlp's latest build when it's been a while (or when a link was blocked). */
    private fun maybeUpdate(app: Context, force: Boolean) {
        val prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val last = prefs.getLong(KEY_UPDATED_AT, 0L)
        val ageDays = if (last == 0L) Long.MAX_VALUE else (System.currentTimeMillis() - last) / 86_400_000L
        if (!force && ageDays < UPDATE_INTERVAL_DAYS) return
        try {
            YoutubeDL.getInstance().updateYoutubeDL(app, YoutubeDL.UpdateChannel.STABLE)
            prefs.edit().putLong(KEY_UPDATED_AT, System.currentTimeMillis()).apply()
        } catch (_: Exception) {
            // Offline or the update is blocked — keep the bundled build and let the download try.
        }
    }

    private fun buildRequest(link: String, dir: File): YoutubeDLRequest {
        val request = YoutubeDLRequest(link)
        request.addOption(
            "-f",
            "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[height<=720]/b",
        )
        request.addOption("--merge-output-format", "mp4")
        request.addOption("-o", File(dir, "%(title).80s-%(id)s.%(ext)s").absolutePath)
        request.addOption("--no-playlist")
        request.addOption("--restrict-filenames")
        return request
    }

    /** Download the best mp4 up to 720p into [dir] and return the saved file. */
    suspend fun download(context: Context, url: String, dir: File): File {
        val link = url.trim()
        require(link.startsWith("http://") || link.startsWith("https://")) { "That doesn't look like a video link." }
        ensureInit(context)
        dir.mkdirs()
        val app = context.applicationContext

        var response = withContext(Dispatchers.IO) { YoutubeDL.getInstance().execute(buildRequest(link, dir)) }
        if (response.exitCode != 0 && isStaleOrBlocked(response.err)) {
            // The classic "HTTP Error 403" / "yt-dlp is older than 90 days": update and retry once.
            withContext(Dispatchers.IO) { maybeUpdate(app, force = true) }
            response = withContext(Dispatchers.IO) { YoutubeDL.getInstance().execute(buildRequest(link, dir)) }
        }
        if (response.exitCode != 0) {
            error(friendlyDownloadError(response.err))
        }
        val out = File(response.out).takeIf { it.isFile }
        if (out != null) return out
        return dir.listFiles()?.maxByOrNull { it.lastModified() }
            ?: error("Could not download that link.")
    }

    private fun isStaleOrBlocked(err: String): Boolean {
        val e = err.lowercase()
        return "403" in e || "forbidden" in e || "older than" in e || "unable to download video data" in e
    }

    private fun friendlyDownloadError(err: String): String {
        val e = err.lowercase()
        return when {
            "403" in e || "forbidden" in e ->
                "YouTube blocked the download (HTTP 403). We updated yt-dlp — please try again."
            "unable to download video data" in e ->
                "YouTube wouldn't send the video data. Try a different link or retry in a moment."
            else -> err.ifBlank { "Could not download that link." }
        }
    }
}
