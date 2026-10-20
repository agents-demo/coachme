package com.coachme.android.domain

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import com.coachme.android.data.Report
import com.coachme.android.ui.i18n.tr
import java.io.File

/** Markdown / HTML export, ported from `integrations/reporting.py`. */
object Reporting {
    fun toMarkdown(r: Report): String {
        val sb = StringBuilder()
        sb.append("# CoachMe report — ${r.stem.ifBlank { r.source }}\n\n")
        sb.append("- Sport: ${r.sport}\n- Date: ${r.date}\n\n")
        if (r.summary.isNotBlank()) sb.append(r.summary).append("\n\n")
        if (r.strengths.isNotEmpty()) sb.append("## Strengths\n").append(r.strengths.joinToString("\n") { "- $it" }).append("\n\n")
        if (r.issues.isNotEmpty()) {
            sb.append("## Issues\n")
            r.issues.forEach { i ->
                val times = i.evidence_times.joinToString(", ")
                val suffix = if (times.isNotBlank()) "  [t=$times; confidence ${i.confidence}]" else "  [confidence ${i.confidence}]"
                sb.append("- ${i.issue}$suffix\n")
            }
            sb.append("\n")
        }
        if (r.drills.isNotEmpty()) sb.append("## Drills\n").append(r.drills.joinToString("\n") { "- $it" }).append("\n\n")
        if (r.focus.isNotBlank()) sb.append("## Focus next session\n${r.focus}\n\n")
        if (r.progress.isNotBlank()) sb.append("## Progress\n${r.progress}\n\n")
        if (r.limitations.isNotEmpty()) sb.append("## Limitations\n").append(r.limitations.joinToString("\n") { "- $it" }).append("\n")
        return sb.toString()
    }

    fun toHtml(r: Report): String {
        fun esc(s: String) = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        val sb = StringBuilder()
        sb.append("<!doctype html><html><head><meta charset='utf-8'><title>CoachMe report</title>")
        sb.append("<style>body{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.5}</style></head><body>")
        sb.append("<h1>CoachMe report — ${esc(r.stem.ifBlank { r.source })}</h1>")
        sb.append("<p><b>${esc(r.sport)}</b> · ${esc(r.date)}</p>")
        if (r.summary.isNotBlank()) sb.append("<p>${esc(r.summary)}</p>")
        if (r.strengths.isNotEmpty()) sb.append("<h2>Strengths</h2><ul>").append(r.strengths.joinToString("") { "<li>${esc(it)}</li>" }).append("</ul>")
        if (r.issues.isNotEmpty()) {
            sb.append("<h2>Issues</h2><ul>")
            r.issues.forEach { i -> sb.append("<li>${esc(i.issue)} <small>[${i.evidence_times.joinToString(", ")}; ${esc(i.confidence)}]</small></li>") }
            sb.append("</ul>")
        }
        if (r.drills.isNotEmpty()) sb.append("<h2>Drills</h2><ul>").append(r.drills.joinToString("") { "<li>${esc(it)}</li>" }).append("</ul>")
        if (r.focus.isNotBlank()) sb.append("<h2>Focus next session</h2><p>${esc(r.focus)}</p>")
        if (r.progress.isNotBlank()) sb.append("<h2>Progress</h2><p>${esc(r.progress)}</p>")
        if (r.limitations.isNotEmpty()) sb.append("<h2>Limitations</h2><ul>").append(r.limitations.joinToString("") { "<li>${esc(it)}</li>" }).append("</ul>")
        sb.append("</body></html>")
        return sb.toString()
    }

    /** Open the Android print dialog on the HTML report (→ "Save as PDF"). */
    fun printPdf(ctx: Context, r: Report) {
        val webView = android.webkit.WebView(ctx)
        webView.settings.javaScriptEnabled = false
        webView.webViewClient = object : android.webkit.WebViewClient() {
            override fun onPageFinished(view: android.webkit.WebView, url: String?) {
                val printManager = ctx.getSystemService(Context.PRINT_SERVICE) as android.print.PrintManager
                val adapter = view.createPrintDocumentAdapter("CoachMe-${r.stem.ifBlank { "session" }}")
                printManager.print("CoachMe report", adapter, null)
            }
        }
        webView.loadDataWithBaseURL(null, toHtml(r), "text/html", "utf-8", null)
    }

    /** Write the export to cache and share it. */
    fun share(ctx: Context, r: Report, format: String) {
        val content = if (format == "html") toHtml(r) else toMarkdown(r)
        val mime = if (format == "html") "text/html" else "text/markdown"
        val ext = if (format == "html") "html" else "md"
        val dir = File(ctx.cacheDir, "exports").apply { mkdirs() }
        val f = File(dir, "${r.stem.ifBlank { "session" }}_report.$ext")
        f.writeText(content)
        val uri: Uri = FileProvider.getUriForFile(ctx, ctx.packageName + ".fileprovider", f)
        val send = Intent(Intent.ACTION_SEND).apply {
            type = mime
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        ctx.startActivity(Intent.createChooser(send, tr("Share report")))
    }
}
