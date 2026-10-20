package com.coachme.android.domain

/** Drill catalog, ported from `domain/drills.py`. Matches a free-text drill to a cue + progression. */
object Drills {
    data class Entry(val name: String, val cue: String, val progression: String)

    private data class Item(val keys: List<String>, val entry: Entry)

    private val CATALOG = listOf(
        Item(
            listOf("split-step", "split step", "timing hop"),
            Entry("Split-step", "Small hop as the opponent contacts; land as the ball leaves their racket.", "Add it to shadow footwork, then to multi-ball."),
        ),
        Item(
            listOf("footwork", "shuffle", "step-and-plant", "step then", "step into"),
            Entry("Footwork", "Step the near foot into the hitting zone before you swing.", "Alternate wide and middle to force a committed step."),
        ),
        Item(
            listOf("recovery", "re-set", "reset"),
            Entry("Recovery", "Re-settle into a balanced ready crouch after every shot.", "Tap a neutral marker between balls."),
        ),
        Item(
            listOf("weight transfer", "load", "crouch", "dip-and-drive", "dip and drive"),
            Entry("Load & drive", "Dip, then drive from the legs — the hips lead the arm.", "Add a visible crouch before each forehand."),
        ),
        Item(
            listOf("shadow", "no ball"),
            Entry("Shadow swings", "Focus purely on the movement pattern.", "Add a small squat load on each landing."),
        ),
        Item(
            listOf("multi-ball", "multiball"),
            Entry("Multi-ball", "High volume to groove the pattern.", "Randomise placement once it's clean."),
        ),
        Item(listOf("serve", "toss"), Entry("Serve", "Consistent toss, full extension.", "Add target zones.")),
        Item(listOf("forehand"), Entry("Forehand", "Compact swing; close the racket early.", "Progress from placement to power.")),
        Item(listOf("backhand"), Entry("Backhand", "Compact; keep the elbow stable.", "Cross-court, then down-the-line.")),
    )

    fun lookup(text: String): Entry? {
        val t = text.lowercase()
        return CATALOG.firstOrNull { item -> item.keys.any { t.contains(it) } }?.entry
    }
}
