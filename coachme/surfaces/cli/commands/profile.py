"""CLI command: set the player profile."""

from __future__ import annotations

from coachme.integrations.storage import store

SPORTS = ["table tennis", "tennis", "badminton", "squash", "padel"]
LEVELS = ["beginner", "intermediate", "advanced"]
HANDS = ["right", "left"]


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def _choose(prompt: str, options: list[str], default: str) -> str:
    print(f"{prompt}:")
    for i, option in enumerate(options, 1):
        print(f"  {i}) {option}")
    answer = input(f"Choose 1-{len(options)} (Enter = {default}): ").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer) - 1]
    return answer if answer in options else default


def run() -> int:
    p = store.get_profile()
    print("Set your profile (Enter keeps the current value).\n")
    sport = _choose("Sport", SPORTS, p.get("sport", "table tennis"))
    level = _choose("Level", LEVELS, p.get("level", "intermediate"))
    hand = _choose("Dominant hand", HANDS, p.get("dominant_hand", "right"))
    goal = _ask("Goal", p.get("goal", "improve"))
    store.set_profile({"sport": sport, "level": level, "dominant_hand": hand, "goal": goal})
    print("\nProfile saved to runtime/data/profile.json.")
    return 0
