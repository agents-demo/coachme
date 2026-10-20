"""Translate video-understanding (CV) findings into plain table-tennis readings.

Pure rules, no advice and no model. It takes the measured ``metrics`` and
describes **everything the coach needs** in table-tennis terms, grouped as Play /
Player / Ball, plus the notable **moments** (times to look at) derived from the CV
events. This is interpretation of *what happened*, not coaching.
"""

from __future__ import annotations


def _num(x):
    return x if isinstance(x, (int, float)) else None


def moments(metrics: dict | None) -> list[dict]:
    """Notable times from the CV events: active spans, direction changes, fast-hand moments."""
    m = metrics or {}
    ball = m.get("ball") or {}
    out: list[dict] = []
    for s in ball.get("segments") or []:
        if _num(s.get("start")) is not None:
            out.append({"t": round(float(s["start"]), 2), "label": "active span"})
    for c in ball.get("contacts") or []:
        if _num(c) is not None:
            out.append({"t": round(float(c), 2), "label": "direction change"})
    for s in m.get("strokes") or []:
        if _num(s.get("t")) is not None:
            hand = s.get("hand") or "?"
            out.append({"t": round(float(s["t"]), 2), "label": f"{hand} fast-hand"})
    out.sort(key=lambda o: o["t"])
    deduped: list[dict] = []
    for o in out:
        if deduped and abs(o["t"] - deduped[-1]["t"]) < 0.3:
            continue
        deduped.append(o)
    return deduped


def _finding(group: str, label: str, value, note: str) -> dict:
    return {"group": group, "label": label, "value": value, "note": note}


def summarize(metrics: dict | None) -> dict:
    m = metrics or {}
    ball = m.get("ball") or {}
    stats = ball.get("stats") or {}
    segments = ball.get("segments") or ball.get("rallies") or []
    strokes = m.get("strokes") or []
    foot = m.get("footwork") or {}
    mech = m.get("mechanics") or {}
    pose = m.get("pose_summary") or {}
    p3 = m.get("pose3d_summary") or {}

    findings: list[dict] = []

    # --- Play -----------------------------------------------------------------
    if segments:
        findings.append(_finding("Play", "Rallies", str(len(segments)), "active stretches of play (≈ rallies)"))
        labels = [s.get("label") for s in segments if s.get("label")]
        if labels:
            findings.append(_finding("Play", "Phases", "; ".join(labels), "how each stretch reads"))
    hits = stats.get("hits") or []
    bounces = stats.get("bounces") or []
    if hits or bounces:
        findings.append(_finding("Play", "Contacts / bounces", f"{len(hits)} / {len(bounces)}", "direction reversals of the tracked ball"))
    energy = m.get("mean_energy")
    if energy is not None:
        busy = "busy" if energy >= 8 else "moderate" if energy >= 3 else "quiet"
        findings.append(_finding("Play", "Activity", busy, f"mean energy {energy}"))

    # --- Player ---------------------------------------------------------------
    if strokes:
        left = sum(1 for s in strokes if s.get("hand") == "left")
        right = sum(1 for s in strokes if s.get("hand") == "right")
        findings.append(_finding("Player", "Strokes", str(len(strokes)), f"{right} right-handed, {left} left-handed"))
    lk, rk = _num(pose.get("l_knee_mean")), _num(pose.get("r_knee_mean"))
    if lk is not None or rk is not None:
        vals = [v for v in (lk, rk) if v is not None]
        avg = sum(vals) / len(vals)
        bend = "quite extended" if avg >= 150 else "moderately bent" if avg >= 120 else "deeply bent"
        findings.append(_finding("Player", "Knee bend", bend, f"knees {lk}° / {rk}°"))
    le, re_ = _num(pose.get("l_elbow_mean")), _num(pose.get("r_elbow_mean"))
    if le is not None or re_ is not None:
        findings.append(_finding("Player", "Elbow bend", f"{le}° / {re_}°", "left / right"))
    crouch = _num(pose.get("crouch_mean"))
    if crouch is not None:
        findings.append(_finding("Player", "Stance", "loaded" if crouch > 0.25 else "upright", f"crouch {crouch}"))
    lean = _num(p3.get("torso_lean_mean"))
    if lean is not None:
        findings.append(_finding("Player", "Torso lean", f"{lean}°", "from vertical"))
    tw_s, tw_h = _num(p3.get("shoulder_twist_mean")), _num(p3.get("hip_twist_mean"))
    if tw_s is not None or tw_h is not None:
        findings.append(_finding("Player", "Rotation", f"shoulder {tw_s}°, hip {tw_h}°", "twist range"))
    lat = _num(mech.get("lower_lateral_range"))
    if lat is not None:
        note = f"side-to-side travel {lat} of the frame"
        steps = mech.get("lower_direction_changes")
        if steps is not None:
            note += f", ~{steps} changes of direction"
        elif foot.get("steps") is not None:
            note += f", ~{foot['steps']} steps"
        findings.append(_finding("Player", "Footwork", "moving well around the table" if lat > 0.15 else "mostly stationary", note))

    # --- Ball -----------------------------------------------------------------
    vis = stats.get("visible_frames")
    if vis is not None:
        findings.append(_finding("Ball", "Tracked", f"{vis} frames", "how often the ball was tracked"))
    spd = _num(stats.get("max_speed"))
    if spd:
        findings.append(_finding("Ball", "Pace", "relative", f"max {spd}/s (screen units — not a real speed)"))
    xs, ys = _num(stats.get("x_range")), _num(stats.get("y_range"))
    if xs is not None or ys is not None:
        findings.append(_finding("Ball", "Path extent", f"x {xs}, y {ys}", "spread of the tracked path"))

    text = "; ".join(f"{f['label']}: {f['value']} ({f['note']})" for f in findings) or "no game reading available"
    return {"findings": findings, "moments": moments(metrics), "text": text}
