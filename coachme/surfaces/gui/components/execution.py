"""The Technical tab: usage metrics plus the full execution timeline."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from coachme.surfaces.gui import style
from coachme.surfaces.gui.timeline import build_timeline, summary_stats


def _load_artifact(path_str: str | None):
    if not path_str:
        return None
    try:
        path = Path(path_str)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (OSError, ValueError):
        return None


def render_technical(report: dict) -> None:
    usage = report.get("usage") or {}
    artifacts = report.get("artifacts") or {}
    models = usage.get("models") or {}
    stats = summary_stats(usage)

    style.section("Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Model calls", stats["calls"])
    c2.metric(
        "Tokens billed",
        f"{stats['total_tokens']:,}",
        help=f"{stats['context_tokens']:,} context + {stats['output_tokens']:,} output",
    )
    c3.metric("From cache", f"{stats['cached_tokens']:,}")
    c4.metric("Model time", f"{stats['model_seconds']:.0f}s")
    if models:
        st.caption(
            f"Text model: {models.get('text', '?')} · Vision model: {models.get('vision', '?')} · "
            f"{models.get('provider', '?')} ({models.get('api_base', '')})"
        )

    obs_data = _load_artifact(artifacts.get("observability")) or {}
    calls = obs_data.get("calls") or []
    called_tools = obs_data.get("tools") or []
    if not calls or not called_tools:
        legacy_calls = _load_artifact(artifacts.get("calls"))
        legacy_tools = _load_artifact(artifacts.get("tools"))
        if not calls and isinstance(legacy_calls, list):
            calls = legacy_calls
        if not called_tools and isinstance(legacy_tools, list):
            called_tools = legacy_tools

    timeline = build_timeline(usage, report.get("timings"), calls=calls, tools=called_tools)
    if not timeline:
        return
    st.divider()
    style.section("Execution")
    ordered = any(r.get("seq") for r in timeline if r.get("kind") in ("model", "tool"))
    if ordered:
        st.caption("Ordered by the exact sequence in which each model/tool call started.")
    elif any(r.get("kind") in ("model", "tool") for r in timeline):
        st.caption(
            "⚠ This report predates event timestamps — call order is not guaranteed. Re-analyze for the true sequence."
        )
    if calls or called_tools:
        st.download_button(
            "Download run details (JSON)",
            json.dumps({"calls": calls, "tools": called_tools}, ensure_ascii=False, indent=2),
            file_name="run_details.json",
            mime="application/json",
        )
    evt_index = 0
    event_css: list[str] = []
    prev_tools: list[str] = []
    for row in timeline:
        kind = row.get("kind")
        if kind == "stage":
            st.markdown(
                f"<div class='tl-stage'><span>{row.get('label', '')}</span>"
                f"<span class='badge'>{float(row.get('seconds', 0)):.2f}s</span></div>",
                unsafe_allow_html=True,
            )
        elif kind == "overhead":
            st.markdown(
                f"<div class='tl-note'>agent overhead · {float(row.get('seconds', 0)):.2f}s</div>",
                unsafe_allow_html=True,
            )
        else:
            secs = float(row.get("seconds", 0) or 0)
            evt_index += 1
            key = f"evt_{evt_index}"
            if kind == "tool":
                title = f"Tool · {row.get('name', '')}"
            else:
                model = row.get("model") or ""
                title = "↳ Model call" + (f" · {model}" if model else "")
                if row.get("note"):
                    title += f" · {row['note']}"
                tool_calls = row.get("requested") or row.get("called") or []
                requested_names = [c.get("name", "") for c in tool_calls]
                if requested_names:
                    title += "  →  calls " + ", ".join(requested_names)
            with st.expander(title, key=key):
                if kind == "tool":
                    st.markdown("**Input — arguments passed to the tool**")
                    st.code(str(row.get("arguments") or "{}"), language="json")
                    if row.get("error"):
                        st.error(str(row.get("error")))
                    st.markdown("**Output — result the tool returned**")
                    st.code(str(row.get("result", "")), language="text")
                else:
                    offered = row.get("tools") or []
                    if offered:
                        st.caption("Tools offered to the model: " + ", ".join(offered))
                    requested = row.get("requested") or row.get("called") or []
                    messages = row.get("input") or []
                    st.markdown("**Input — everything sent to the model**")
                    if not messages:
                        st.caption("Input not saved (SAVE_CALL_IO is off) or unavailable.")
                    for message in messages:
                        role = message.get("role", "")
                        content = message.get("content", "")
                        if role == "assistant" and not str(content).strip():
                            content = (
                                "(tool call: " + ", ".join(prev_tools) + ")"
                                if prev_tools
                                else "(no text — the model called a tool here)"
                            )
                        st.markdown(f"*{role}*")
                        st.code(content, language="text")
                    image_paths = [p for p in (row.get("images") or []) if Path(p).exists()]
                    if image_paths:
                        st.markdown(f"*images sent to the model ({len(image_paths)})*")
                        for path in image_paths:
                            st.image(path)
                    prev_tools = [call.get("name", "") for call in requested]
                    st.markdown("**Output — what the model produced**")
                    if requested:
                        for call in requested:
                            st.markdown(f"↳ requested tool `{call.get('name', '')}` with:")
                            params = call.get("arguments")
                            st.code(str(params) if params else "{}", language="json")
                    if row.get("output"):
                        st.code(row["output"], language="text")
                    elif requested:
                        st.caption("No text — the model only requested tool calls on this turn.")
                    elif not messages:
                        st.caption("Output not saved (SAVE_CALL_IO is off).")
            event_css.append(
                f".st-key-{key} summary {{ position: relative; }}"
                f".st-key-{key} summary::after {{ content: '{secs:.2f}s'; position: absolute; "
                f"right: 2.6rem; top: 50%; transform: translateY(-50%); color: var(--muted); "
                f"font-size: 0.68rem; font-weight: 500; letter-spacing: .01em; "
                f"font-variant-numeric: tabular-nums; }}"
            )
    if event_css:
        st.markdown("<style>" + "".join(event_css) + "</style>", unsafe_allow_html=True)
