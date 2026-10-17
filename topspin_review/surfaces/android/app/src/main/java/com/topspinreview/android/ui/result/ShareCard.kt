package com.topspinreview.android.ui.result

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import androidx.core.content.FileProvider
import com.topspinreview.android.data.Report
import com.topspinreview.android.ui.i18n.tr
import java.io.File

/** Share card (1200×630), ported from `integrations/cards.py`. */
object ShareCard {
    fun render(report: Report, bg: Bitmap? = null): Bitmap {
        val w = 1200; val h = 630
        val bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        c.drawColor(Color.rgb(11, 11, 15))
        if (bg != null) {
            val scale = maxOf(w.toFloat() / bg.width, h.toFloat() / bg.height)
            val scaled = Bitmap.createScaledBitmap(bg, (bg.width * scale).toInt(), (bg.height * scale).toInt(), true)
            val left = (scaled.width - w) / 2; val top = (scaled.height - h) / 2
            val crop = Bitmap.createBitmap(scaled, left.coerceAtLeast(0), top.coerceAtLeast(0), w, h)
            c.drawBitmap(crop, 0f, 0f, Paint().apply { alpha = 110 })
        }
        val title = Paint().apply { color = Color.rgb(236, 236, 242); textSize = 44f; isAntiAlias = true; isFakeBoldText = true }
        val muted = Paint().apply { color = Color.rgb(170, 176, 190); textSize = 28f; isAntiAlias = true }
        val big = Paint().apply { color = Color.rgb(236, 236, 242); textSize = 64f; isAntiAlias = true; isFakeBoldText = true }
        val body = Paint().apply { color = Color.rgb(203, 213, 225); textSize = 32f; isAntiAlias = true }
        val accent = Paint().apply { color = Color.rgb(129, 140, 248); textSize = 28f; isAntiAlias = true }

        c.drawText("Topspin Review", 60f, 90f, title)
        c.drawText("${report.sport} · ${report.date}", 60f, 140f, muted)
        c.drawText("${report.issues.size} thing${if (report.issues.size == 1) "" else "s"} to fix", 60f, 280f, big)
        val focus = report.focus.ifBlank { report.summary }
        wrap(c, focus, body, w - 120).forEachIndexed { i, line -> c.drawText(line, 60f, 360f + i * 44f, body) }
        return bmp
    }

    private fun wrap(c: Canvas, text: String, paint: Paint, maxWidth: Int): List<String> {
        val words = text.split(" "); val out = ArrayList<String>(); var cur = ""
        for (word in words) {
            val trial = if (cur.isEmpty()) word else "$cur $word"
            if (paint.measureText(trial) <= maxWidth || cur.isEmpty()) cur = trial
            else { out.add(cur); cur = word }
            if (out.size >= 4) break
        }
        if (cur.isNotEmpty() && out.size < 4) out.add(cur)
        return out
    }

    fun share(ctx: Context, report: Report) {
        val bmp = render(report)
        val dir = File(ctx.cacheDir, "cards").apply { mkdirs() }
        val f = File(dir, "${report.stem.ifBlank { "session" }}_card.png")
        f.outputStream().use { bmp.compress(Bitmap.CompressFormat.PNG, 100, it) }
        val uri = FileProvider.getUriForFile(ctx, ctx.packageName + ".fileprovider", f)
        val send = Intent(Intent.ACTION_SEND).apply {
            type = "image/png"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        ctx.startActivity(Intent.createChooser(send, tr("Share card")))
    }
}
