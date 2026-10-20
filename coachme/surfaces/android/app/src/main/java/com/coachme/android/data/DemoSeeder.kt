package com.coachme.android.data

import android.content.Context
import java.io.File

/** Seeds one bundled CoachMe demo session on first launch. */
object DemoSeeder {
    private const val STEM = "Michael-Osher"
    private const val MARKER = ".coachme_demo_seeded_v1"
    private val ARTIFACTS = listOf("pose_hero", "pose", "frames", "motion", "heatmap", "ball")

    fun seed(context: Context) {
        val root = context.filesDir
        val marker = File(root, MARKER)
        if (marker.exists()) return

        runCatching {
            val demoDir = File(root, "demo").apply { mkdirs() }
            copyAsset(context, "demo/$STEM.mp4", File(demoDir, "$STEM.mp4"))
            for (kind in ARTIFACTS) {
                copyAsset(context, "demo/${STEM}_$kind.jpg", File(demoDir, "${STEM}_$kind.jpg"))
            }

            val report = File(File(root, "reports").apply { mkdirs() }, "${STEM}_report.json")
            if (!report.exists()) {
                val raw = context.assets.open("demo/${STEM}_report.json")
                    .bufferedReader()
                    .use { it.readText() }
                    .replace("__DEMO_DIR__", demoDir.absolutePath)
                report.writeText(raw)
            }
            marker.writeText("1")
        }
    }

    private fun copyAsset(context: Context, asset: String, target: File) {
        if (target.exists() && target.length() > 0) return
        context.assets.open(asset).use { input ->
            target.outputStream().use { output -> input.copyTo(output) }
        }
    }
}
