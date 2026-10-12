"""Pipeline strategies — the two interchangeable modes, behind a base class + registry."""

from topspin_review.core.strategies.base import Strategy
from topspin_review.core.strategies.resolve_strategy import (
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
