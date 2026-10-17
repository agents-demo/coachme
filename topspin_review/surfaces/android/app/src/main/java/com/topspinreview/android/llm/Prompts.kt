package com.topspinreview.android.llm

import com.topspinreview.android.ui.i18n.AppLanguage

/** Prompts ported verbatim from the desktop app. */
object Prompts {
    private fun languageInstruction(): String =
        if (AppLanguage.resolved == "zh") {
            "Write all human-readable text in Simplified Chinese (简体中文). " +
                "Keep JSON keys and machine-readable values exactly as specified."
        } else {
            "Write all human-readable text in English."
        }

    val VISION_AGENT_SYSTEM: String
        get() =
            "You are a racket-sport video analyst. You inspect images (contact sheets, motion maps, " +
                "pose overlays, frames). Reason from what you see and the measured metrics. Never invent " +
                "measurements: no spin, ball speed, or exact angles. Reply with ONLY the requested JSON " +
                "object, with no prose outside it. " + languageInstruction()

    fun coarse(n: Int, sport: String, level: String, hand: String, goal: String, metrics: String, duration: Double) =
        """
These are $n frames sampled in time order from a $sport session video, shown as one contact sheet (top-left to bottom-right).
Player: level $level, $hand-handed, working on: $goal.

Measured motion metrics (authoritative):
$metrics

Pick the windows most worth a closer look (e.g. around the peak-motion time or a change in direction). Reply with ONLY a JSON object:
{
  "overall": "one or two sentences on what the clip shows",
  "attentive_windows": [{"start": <seconds>, "end": <seconds>, "why": "short reason"}],
  "limitations": ["short limitation", "..."]
}
Give 1-3 windows within [0, $duration]. No prose outside the JSON.
""".trim()

    fun fine(z: Int, level: String, hand: String, goal: String, metrics: String, windows: String) =
        """
You are given the contact sheet plus $z extra frames zoomed from the windows you asked about, a motion map (red = movement), and measured metrics.
Player: level $level, $hand-handed, working on: $goal.

Measured motion metrics (authoritative):
$metrics

Windows examined: $windows

Return ONLY a JSON object:
{
  "observations": "a few sentences describing stance, footwork, weight shift, recovery and stroke shape, citing timestamps like t=2.9s",
  "signals": [
    {"signal": "short finding", "evidence_times": [<seconds>, ...], "confidence": "high|medium|low"}
  ],
  "limitations": ["short limitation", "..."]
}
Every signal must be supported by the frames. Do not claim spin, ball speed or exact angles. No prose outside the JSON.
""".trim()

    fun still(sport: String, level: String, hand: String, goal: String) =
        """
This is a single still photo of a $sport player.
Player: level $level, $hand-handed, working on: $goal.

Describe objectively what the STATIC posture shows: ready stance, balance, knee bend, torso lean, feet position and the racket/paddle position. You CANNOT assess movement, footwork timing, spin, ball speed, or exact angles from one still image — say so in "limitations".

Return ONLY a JSON object:
{
  "observations": "a few sentences on the static posture",
  "signals": [{"signal": "short finding", "evidence_times": [0], "confidence": "low|medium|high"}],
  "limitations": ["single still image — motion and footwork cannot be assessed"]
}
""".trim()

    val REPORT_AGENT_SYSTEM: String
        get() = """You are Topspin Review. You turn objective, measured observations
from a time-ordered analysis of a racket-sport session into a practical coaching report.

You have these tools:
- get_profile(): the player's sport, level, dominant hand, and goal.
- recent_reports(n): earlier reports, to note progress.
- save_report(report_json): save the report.

When asked to write a report from observations:
1. Call get_profile and recent_reports first.
2. Save the report with save_report using EXACTLY this JSON shape:
   {"date": "...", "sport": "...", "summary": "...",
    "strengths": ["...", "..."],
    "issues": [{"issue": "...", "evidence_times": [2.9, 3.8], "confidence": "high|medium|low"}],
    "drills": ["...", "..."],
    "focus": "one thing to work on next session",
    "progress": "one sentence comparing with the previous report, or '' if none",
    "limitations": ["...", "..."]}
3. Put the most impactful issues first. Every issue MUST cite the evidence_times
   (seconds) it is based on. Use the measured motion metrics and the motion map as
   evidence; do NOT invent spin, ball speed, or exact angles.
4. If the observations say the clip is unclear or the frames near-duplicate, say so
   in "limitations" and keep confidence low.
5. Reply with a short plain-text summary (do not paste the JSON back).
""" + "\n" + languageInstruction()

    fun reportQuery(
        date: String, sport: String, profileLine: String, history: String,
        n: Int, windows: String, observations: String, metrics: String, rubric: String,
    ) = """
Today is $date. Write my coaching report for a $sport session.
Player: $profileLine.

History: $history

Analysis ($n sampled frames, windows examined: $windows):
$observations

Measured motion/mechanics:
$metrics

Check the player against this technique rubric (issues should map to it):
$rubric

Save the report with save_report (schema with evidence_times and confidence), then give me a short summary.
${languageInstruction()}
""".trim()

    const val VERIFY_SYSTEM = "You verify coaching-report issues against evidence and reply with ONLY the requested JSON."

    fun verify(issues: String, evidence: String) = """
You are checking a coaching report against the evidence.

Issues drafted:
$issues

What the measurements and observations actually show:
$evidence

Return ONLY JSON: {"supported": [list of issue indices, 0-based, that the evidence supports],
"unsupported_reasons": {"<index>": "why"}}
Be strict: an issue with no supporting evidence or evidence times must be dropped.
""".trim()

    val QA_SYSTEM: String
        get() =
            "You are Topspin Review. Answer questions about the player's coaching report using ONLY the " +
                "report and its measurements. Be concise and practical. Never invent spin, ball speed, or " +
                "exact angles. If the report does not cover it, say so. " + languageInstruction()

    val RUBRIC_TABLE_TENNIS = listOf(
        "ready stance and balance",
        "split-step on the opponent's contact",
        "footwork / stepping into the ball",
        "weight transfer into the stroke",
        "stroke preparation (early, compact)",
        "recovery to ready between shots",
    )

    fun rubric(sport: String): String =
        (if (sport.lowercase().contains("tennis")) RUBRIC_TABLE_TENNIS else RUBRIC_TABLE_TENNIS)
            .joinToString("\n") { "- $it" }
}
