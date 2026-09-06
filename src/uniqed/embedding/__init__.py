"""Automatic choice of the time-delay embedding (story A1).

Delay from the autocorrelation, dimension from intrinsic-dimension saturation,
Gautama's entropy ratio as the fallback for stochastic signals.
"""

from uniqed.embedding.delay import autocorrelation, choose_delay
from uniqed.embedding.dimension import choose_dimension, dimension_profile, intrinsic_dimension

__all__ = [
    "autocorrelation",
    "choose_delay",
    "choose_dimension",
    "dimension_profile",
    "intrinsic_dimension",
]
