"""Language instructions for model prompts."""

from __future__ import annotations


def language_instruction(language: str | None) -> str:
    if (language or "").strip().lower().startswith("zh"):
        return (
            "Write all human-readable text in Simplified Chinese (简体中文). "
            "Keep JSON keys and machine-readable values exactly as specified."
        )
    return "Write all human-readable text in English."
