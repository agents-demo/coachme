"""Pipeline strategies — the two interchangeable modes, behind a base class + registry."""

from coachme.core.strategies.base import Strategy
from coachme.core.strategies.resolve_strategy import (
    AGENTIC,
    DETERMINISTIC,
    STRATEGIES,
    default_name,
    get_strategy,
    resolve,
)

__all__ = [
    "AGENTIC",
    "DETERMINISTIC",
    "STRATEGIES",
    "Strategy",
    "default_name",
    "get_strategy",
    "resolve",
]
