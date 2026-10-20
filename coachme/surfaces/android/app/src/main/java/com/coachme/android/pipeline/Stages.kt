package com.coachme.android.pipeline

/**
 * A progress snapshot the pipeline emits as it advances through a run.
 *
 * [index] is the zero-based position in the run's stage plan, [total] the size of
 * that plan, and [progress] a 0..1 fraction suitable for a progress bar. [next] is
 * the label of the following stage (or null on the last step).
 */
data class StageInfo(
    val name: String,
    val index: Int,
    val total: Int,
    val progress: Float,
    val next: String?,
)

/** A summary of an interrupted run on disk, so the UI can offer to continue it. */
data class PendingRun(
    val videoPath: String,
    val stem: String,
    val isImage: Boolean,
    val region: List<Float>,
    val doneCount: Int,
    val totalCount: Int,
)

/**
 * The canonical, ordered stage plans for each run type. The pipeline emits these
 * names in order and the UI uses the plan to render its step indicator, so the two
 * never drift apart.
 */
object Stages {
    val video = listOf(
        "Pick frames",
        "Measure movement",
        "Estimate pose",
        "Track ball",
        "Render images",
        "First look",
        "Detailed findings",
        "Write report",
        "Double-check",
    )

    val image = listOf(
        "Pick frames",
        "Render images",
        "Review image",
        "Write report",
        "Double-check",
    )

    fun plan(isImage: Boolean): List<String> = if (isImage) image else video
}
