package com.coachme.android.data

import android.content.Context
import org.json.JSONObject
import java.io.File
import java.time.LocalDate

/** Seeds one bundled CoachMe demo session on first launch. */
object DemoSeeder {
    private const val STEM = "Michael-Osher"
    private const val MARKER = ".coachme_demo_seeded_v2"
    private const val LEGACY_MARKER = ".coachme_demo_seeded_v1"
    private val ARTIFACTS = listOf("pose_hero", "pose", "frames", "motion", "heatmap", "ball")

    fun seed(context: Context) {
        val root = context.filesDir
        val marker = File(root, MARKER)
        if (marker.exists()) return

        val reports = File(root, "reports").apply { mkdirs() }
        val report = File(reports, "${STEM}_report.json")
        val legacy = File(root, LEGACY_MARKER)
        val today = LocalDate.now().toString()

        runCatching {
            if (legacy.exists()) {
                // Upgrade the demo installed by v0.1.1 without recreating a deleted session.
                if (report.exists()) updateMetadata(report, today)
            } else if (!report.exists()) {
                val demoDir = File(root, "demo").apply { mkdirs() }
                copyAsset(context, "demo/$STEM.mp4", File(demoDir, "$STEM.mp4"))
                for (kind in ARTIFACTS) {
                    copyAsset(context, "demo/${STEM}_$kind.jpg", File(demoDir, "${STEM}_$kind.jpg"))
                }
                val raw = context.assets.open("demo/${STEM}_report.json")
                    .bufferedReader()
                    .use { it.readText() }
                    .replace("__DEMO_DIR__", demoDir.absolutePath)
                val obj = JSONObject(raw)
                obj.put("date", today)
                obj.put("demo", true)
                report.writeText(obj.toString())
            }
            marker.writeText("1")
        }
    }

    private fun updateMetadata(report: File, today: String) {
        val obj = JSONObject(report.readText())
        obj.put("date", today)
        obj.put("demo", true)
        report.writeText(obj.toString())
    }

    private fun copyAsset(context: Context, asset: String, target: File) {
        if (target.exists() && target.length() > 0) return
        context.assets.open(asset).use { input ->
            target.outputStream().use { output -> input.copyTo(output) }
        }
    }
}
