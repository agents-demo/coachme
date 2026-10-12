"""The pipeline — stages of analysis, run by two interchangeable strategies.

- :mod:`~topspin_review.core.stages.measure` — stage 1: clip → frames + measurements.
- :mod:`~topspin_review.core.stages.observe` — stage 2: frames → observations.
- :mod:`~topspin_review.core.stages.coach` — stage 3: observations → coaching report.
- :mod:`~topspin_review.core.strategies` — deterministic / agentic modes over the stages.

Import the orchestrator from this package, never a concrete strategy module:

    from topspin_review import core

    strategy = core.resolve(agentic=True)
    result = await strategy.analyze(core.Params(video_path, progress=...))

Side-effect free.
"""

from topspin_review.core.params import Params
from topspin_review.core.stages import STAGES
from topspin_review.core.strategies import (
    AGENTIC,
    DETERMINISTIC,
    STRATEGIES,
    Strategy,
    default_name,
    get_strategy,
    resolve,
)

__all__ = [
    "AGENTIC",
    "DETERMINISTIC",
    "STAGES",
    "STRATEGIES",
    "Params",
    "Strategy",
    "default_name",
    "get_strategy",
    "resolve",
]
