"""The analysis-strategy registry and factory.

Callers obtain a strategy here (by name or via :func:`resolve`); they never
import a concrete strategy module. To add a strategy, subclass
:class:`~coachme.core.strategies.base.Strategy` and register an
instance in ``STRATEGIES``.
"""

from __future__ import annotations

from coachme.core import config
from coachme.core.strategies.agentic import AgenticStrategy
from coachme.core.strategies.base import Strategy
from coachme.core.strategies.deterministic import DeterministicStrategy

DETERMINISTIC = "deterministic"
AGENTIC = "agentic"
INVESTIGATOR = "investigator"

STRATEGIES: dict[str, Strategy] = {
    DETERMINISTIC: DeterministicStrategy(),
    AGENTIC: AgenticStrategy(),
}


def default_name() -> str:
    """The configured default strategy name (``AGENTIC_MODE``)."""
    return AGENTIC if config.agentic_mode() else DETERMINISTIC


def get_strategy(name: str | None = None) -> Strategy:
    """Look up a strategy by name, or the configured default when ``name`` is ``None``."""
    resolved = name or default_name()
    if resolved == INVESTIGATOR:
        # Lazy import: investigator pulls in the agent stack and must not slow
        # startup or the deterministic/agentic paths.
        from coachme.core.strategies.investigator import InvestigatorStrategy

        return InvestigatorStrategy()
    try:
        return STRATEGIES[resolved]
    except KeyError:
        known = ", ".join(sorted({*STRATEGIES, INVESTIGATOR}))
        raise ValueError(f"unknown analysis strategy {resolved!r}; known: {known}") from None


def resolve(agentic: bool = False) -> Strategy:
    """The strategy for a request: agentic when requested, else the configured default."""
    return get_strategy(AGENTIC if agentic else default_name())
