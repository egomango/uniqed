"""Automatic choice of the time-delay embedding (story A1).

Delay from the autocorrelation, dimension from intrinsic-dimension saturation,
Gautama's entropy ratio as the fallback for stochastic signals.
"""

from uniqed.embedding.delay import autocorrelation, choose_delay
from uniqed.embedding.dimension import choose_dimension, dimension_profile, intrinsic_dimension
from uniqed.embedding.entropy import entropy_ratio, iaaft_surrogate, kl_entropy

__all__ = [
    "autocorrelation",
    "choose_delay",
    "choose_dimension",
    "dimension_profile",
    "entropy_ratio",
    "iaaft_surrogate",
    "intrinsic_dimension",
    "kl_entropy",
]
