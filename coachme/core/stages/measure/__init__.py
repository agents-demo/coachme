"""Stage: measure the clip (frame sampling + motion/ball/quality measurement)."""

from coachme.core.stages.measure import ball, quality, sampling
from coachme.core.stages.measure.measure import Measurement, measure

__all__ = ["Measurement", "ball", "measure", "quality", "sampling"]
