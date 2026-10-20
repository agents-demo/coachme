package com.coachme.android.pipeline

import android.graphics.Bitmap
import java.io.ByteArrayOutputStream
import java.io.OutputStream
import kotlin.math.min

/**
 * A minimal GIF89a encoder (global 216-colour palette + LZW). Self-contained — Media3 can't
 * emit animated GIFs. Frames must share the same size.
 */
object GifEncoder {
    fun encode(frames: List<Bitmap>, delayMs: Int, out: OutputStream) {
        require(frames.isNotEmpty())
        val w = frames[0].width
        val h = frames[0].height

        out.write("GIF89a".toByteArray(Charsets.US_ASCII))
        writeShort(out, w); writeShort(out, h)
        out.write(0xF7) // global color table, 256 entries, 8-bit
        out.write(0); out.write(0)
        writePalette(out)

        // Netscape looping extension
        out.write(0x21); out.write(0xFF); out.write(0x0B)
        out.write("NETSCAPE2.0".toByteArray(Charsets.US_ASCII))
        out.write(0x03); out.write(0x01); writeShort(out, 0); out.write(0x00)

        val delay = (delayMs / 10).coerceAtLeast(1)
        for (bmp in frames) {
            val indices = quantize(bmp, w, h)
            // Graphic control extension
            out.write(0x21); out.write(0xF9); out.write(0x04); out.write(0x00)
            writeShort(out, delay); out.write(0x00); out.write(0x00)
            // Image descriptor
            out.write(0x2C); writeShort(out, 0); writeShort(out, 0); writeShort(out, w); writeShort(out, h); out.write(0x00)
            // LZW
            out.write(8)
            val compressed = lzw(indices, 8)
            var off = 0
            while (off < compressed.size) {
                val n = min(255, compressed.size - off)
                out.write(n); out.write(compressed, off, n); off += n
            }
            out.write(0x00)
        }
        out.write(0x3B)
    }

    private fun writeShort(out: OutputStream, v: Int) { out.write(v and 0xFF); out.write((v shr 8) and 0xFF) }

    private fun writePalette(out: OutputStream) {
        for (i in 0 until 256) {
            if (i < 216) {
                out.write(((i / 36) * 51)); out.write((((i / 6) % 6) * 51)); out.write(((i % 6) * 51))
            } else {
                val g = ((i - 216) * 255 / 39)
                out.write(g); out.write(g); out.write(g)
            }
        }
    }

    private fun quantize(bmp: Bitmap, w: Int, h: Int): ByteArray {
        val px = IntArray(w * h); bmp.getPixels(px, 0, w, 0, 0, w, h)
        val out = ByteArray(px.size)
        for (i in px.indices) {
            val p = px[i]
            val r = (p shr 16) and 0xFF; val g = (p shr 8) and 0xFF; val b = p and 0xFF
            val qr = (r * 5) / 255; val qg = (g * 5) / 255; val qb = (b * 5) / 255
            out[i] = (qr * 36 + qg * 6 + qb).toByte()
        }
        return out
    }

    /** Standard GIF LZW; returns the compressed sub-block payload (without block framing). */
    private fun lzw(indices: ByteArray, minCodeSize: Int): ByteArray {
        val clear = 1 shl minCodeSize
        val eoi = clear + 1
        val outBuf = ByteArrayOutputStream()

        var bitBuffer = 0
        var bitCount = 0
        var codeSize = minCodeSize + 1
        var dictSize = eoi + 1
        var dict = HashMap<Int, Int>(1 shl 13)

        fun emit(code: Int) {
            bitBuffer = bitBuffer or (code shl bitCount)
            bitCount += codeSize
            while (bitCount >= 8) {
                outBuf.write(bitBuffer and 0xFF)
                bitBuffer = bitBuffer shr 8
                bitCount -= 8
            }
        }

        emit(clear)
        if (indices.isEmpty()) { emit(eoi); flush(outBuf, bitBuffer, bitCount); return outBuf.toByteArray() }
        var prefix = indices[0].toInt() and 0xFF
        for (i in 1 until indices.size) {
            val c = indices[i].toInt() and 0xFF
            val key = (prefix shl 8) or c
            val existing = dict[key]
            if (existing != null) {
                prefix = existing
            } else {
                emit(prefix)
                dict[key] = dictSize++
                if (dictSize > (1 shl codeSize) - 1) {
                    if (codeSize < 12) codeSize++ else {
                        emit(clear); dict = HashMap(1 shl 13); dictSize = eoi + 1; codeSize = minCodeSize + 1
                    }
                }
                prefix = c
            }
        }
        emit(prefix)
        emit(eoi)
        flush(outBuf, bitBuffer, bitCount)
        return outBuf.toByteArray()
    }

    private fun flush(out: ByteArrayOutputStream, bitBuffer: Int, bitCount: Int) {
        var buf = bitBuffer; var count = bitCount
        while (count > 0) { out.write(buf and 0xFF); buf = buf shr 8; count -= 8 }
    }
}
