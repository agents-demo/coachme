"""Share card: a branded PNG teaser for a session (Pillow). Best-effort."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

W, H = 1200, 630


def _font(size: int):
    from PIL import ImageFont

    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    words = str(text or "").split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:4]


def share_card(report: dict) -> bytes | None:
    """Render a 1200x630 PNG teaser for a report. Returns PNG bytes or ``None``."""
    try:
        from PIL import Image, ImageDraw, ImageEnhance
    except Exception:
        return None

    try:
        canvas = Image.new("RGB", (W, H), (11, 11, 15))
        arts = report.get("artifacts") or {}
        bg = arts.get("pose_hero") or arts.get("motion") or arts.get("frames")
        if bg and Path(bg).exists():
            try:
                b = Image.open(bg).convert("RGB")
                scale = max(W / b.width, H / b.height)
                b = b.resize((int(b.width * scale), int(b.height * scale)))
                left, top = (b.width - W) // 2, (b.height - H) // 2
                b = b.crop((left, top, left + W, top + H))
                canvas = ImageEnhance.Brightness(b).enhance(0.42)
            except Exception:
                pass

        draw = ImageDraw.Draw(canvas)
        ink, muted, accent = (236, 236, 242), (170, 176, 190), (129, 140, 248)
        draw.text((60, 60), "CoachMe", font=_font(38), fill=ink)
        draw.text((60, 118), f"{report.get('sport', '')} · {report.get('date', '')}", font=_font(24), fill=muted)

        issues = report.get("issues") or []
        draw.text((60, 210), f"{len(issues)} thing{'s' if len(issues) != 1 else ''} to fix", font=_font(56), fill=ink)

        focus = report.get("focus") or report.get("summary") or ""
        for i, line in enumerate(_wrap(draw, focus, _font(28), W - 120)):
            draw.text((60, 320 + i * 40), line, font=_font(28), fill=(203, 213, 225))

        score = report.get("score")
        if isinstance(score, dict) and score.get("score") is not None:
            draw.text((60, H - 80), f"Report quality {score['score']}/100", font=_font(24), fill=accent)

        bio = BytesIO()
        canvas.save(bio, format="PNG")
        return bio.getvalue()
    except Exception:
        return None
