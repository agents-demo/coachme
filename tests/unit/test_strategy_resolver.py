"""Regression test: the strategy registry is intact after investigator additions.

This ensures that adding InvestigatorStrategy did not break the existing
deterministic and agentic strategy lookup, and that the resolver behaves
consistently for all three names and for unknown names.
"""
from __future__ import annotations

import pytest

from topspin_review.core.strategies.resolve_strategy import (
    AGENTIC,
    DETERMINISTIC,
    INVESTIGATOR,
    default_name,
    get_strategy,
)


def test_deterministic_is_accessible() -> None:
    strategy = get_strategy(DETERMINISTIC)
    assert strategy.name == "deterministic"
    assert strategy.allow_demo_fallback is True


def test_agentic_is_accessible() -> None:
    strategy = get_strategy(AGENTIC)
    assert strategy.name == "agentic"


def test_investigator_is_accessible() -> None:
    strategy = get_strategy(INVESTIGATOR)
    assert strategy.name == "investigator"
    assert strategy.allow_demo_fallback is False


def test_get_strategy_none_returns_default() -> None:
    # None → configured default (deterministic or agentic, never investigator)
    strategy = get_strategy(None)
    assert strategy.name in (DETERMINISTIC, AGENTIC)


def test_unknown_strategy_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unknown analysis strategy"):
        get_strategy("nonexistent_mode")


def test_default_name_is_not_investigator() -> None:
    # Investigator must never be the automatic default — it is opt-in only.
    assert default_name() in (DETERMINISTIC, AGENTIC)


def test_get_strategy_is_idempotent() -> None:
    # Calling twice for the same name should not raise or return different types.
    s1 = get_strategy(DETERMINISTIC)
    s2 = get_strategy(DETERMINISTIC)
    assert type(s1) is type(s2)

    s3 = get_strategy(INVESTIGATOR)
    s4 = get_strategy(INVESTIGATOR)
    assert type(s3) is type(s4)
