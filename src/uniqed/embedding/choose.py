from dataclasses import dataclass

import numpy as np

from uniqed.embedding.delay import choose_delay
from uniqed.embedding.dimension import choose_dimension, dimension_profile
from uniqed.embedding.entropy import entropy_ratio


@dataclass(frozen=True)
class EmbeddingChoice:
    """The embedding the package chose, and how.

    ``window`` is (dimension - 1) * delay: the paper's Fig. S5 shows that near-optimal
    (E, tau) pairs share a window length, so it is reported for the user to compare
    across signals. It is not used to pick the pair: delay and dimension already fix it,
    and choosing a window first would need a labelled F1 surface the user does not have.
    """

    dimension: int
    delay: int
    method: str
    delay_rule: str
    dimension_profile: tuple
    window: int
    resolution: float = 0.0
    dithered: bool = False


def _choice(dimension, delay, method, delay_rule, profile, resolution=0.0, dithered=False):
    return EmbeddingChoice(
        int(dimension),
        int(delay),
        method,
        delay_rule,
        tuple(float(v) for v in profile),
        int((dimension - 1) * delay),
        float(resolution),
        bool(dithered),
    )


SIGNIFICANT_DIGITS = 10
TIE_FRACTION = 0.5
# Embedded rows the intrinsic-dimension profile needs. Below this, white noise can
# show a false plateau at the top of the grid from the estimator's small-sample bias
# (measured 2026-09-06 over 25 seeds: 4 of 8 at 100 rows, 1 of 25 at 300, 0 of 25 at
# 400, 500, 600 and 800). 500 leaves a margin.
MIN_ROWS = 500


def quantisation(x):
    """Smallest step between distinct values of ``x``, ignoring floating-point dust.

    :return: the step, or 0.0 when the values look continuous
    :rtype: float
    """
    x = np.asarray(x, dtype=float).ravel()
    scale = np.max(np.abs(x))
    if scale == 0:
        return 0.0
    rounded = np.round(x / scale, SIGNIFICANT_DIGITS) * scale
    unique = np.unique(rounded)
    if len(unique) >= TIE_FRACTION * len(x):
        return 0.0
    step = float(np.min(np.diff(unique)))
    return float(f"{step:.6g}")


def dither(x, resolution, seed=0):
    """Add uniform noise of +-resolution/2 so tied values become distinct.

    The intrinsic-dimension and differential-entropy estimators assume continuous
    values; on quantised data (meters, historians, rates quoted to two decimals)
    tied points give zero neighbour distances and the estimates collapse.
    """
    rng = np.random.default_rng(seed)
    return x + rng.uniform(-resolution / 2.0, resolution / 2.0, size=len(x))


def choose_embedding(x, dimension=None, delay=None, max_dim=8):
    """Pick the time-delay embedding of ``x`` (paper SI, Figs. S9-S12).

    Delay: first zero crossing of the autocorrelation, else its first minimum.
    Dimension: where the intrinsic-dimension estimate stops tracking the embedding
    dimension (deterministic signals). When it never does, the signal is treated as
    stochastic and both values come from Gautama's entropy ratio (Fig. S12).
    Either value may be given by the caller; only the other is chosen.
    Quantised input (fewer distinct values than half the samples) is dithered by
    half its resolution before the estimators run; the choice records it.
    The series must leave at least ``MIN_ROWS`` embedded rows at the largest
    dimension tried; shorter series, and series whose autocorrelation never turns
    within the delays they can support, raise a ValueError that says to pass the
    embedding explicitly. Nothing is guessed.

    :raises ValueError: too short a series, no usable delay, or values that repeat exactly

    :param numpy.ndarray x: 1D series
    :param int dimension: fixed embedding dimension, or None to choose
    :param int delay: fixed embedding delay, or None to choose
    :param int max_dim: largest dimension the saturation rule looks at
    :return: the choice with its diagnostics
    :rtype: EmbeddingChoice
    """
    x = np.asarray(x, dtype=float).ravel()

    if dimension is not None and delay is not None:
        return _choice(dimension, delay, "given", "given", ())

    # The profile embeds up to max_dim + 1 dimensions, losing max_dim * delay rows.
    max_lag = (len(x) - MIN_ROWS) // max_dim
    if max_lag < 1:
        raise ValueError(
            f"series too short to choose an embedding: {len(x)} samples, need at least "
            f"{MIN_ROWS + max_dim}. Pass embedding_dimension and embedding_delay explicitly."
        )

    if delay is None:
        delay, delay_rule = choose_delay(x, max_lag=max_lag)
        if delay_rule == "none":
            raise ValueError(
                "could not choose a delay: the autocorrelation neither reaches zero nor "
                f"has a minimum within {max_lag} lags, the largest delay {len(x)} samples "
                "can support. The series holds too few cycles of its slowest rhythm; "
                "supply more history or pass embedding_dimension and embedding_delay explicitly."
            )
    else:
        delay_rule = "given"
        if delay > max_lag:
            raise ValueError(
                f"delay {delay} leaves fewer than {MIN_ROWS} embedded rows in {len(x)} samples; "
                "pass embedding_dimension as well."
            )

    if dimension is not None:
        return _choice(dimension, delay, "given", delay_rule, ())

    resolution = quantisation(x)
    dithered = resolution > 0
    if dithered:
        x = dither(x, resolution)

    profile = dimension_profile(x, delay, max_dim=max_dim + 1)
    chosen = choose_dimension(x, delay, max_dim=max_dim, profile=profile)
    if chosen is not None:
        return _choice(chosen, delay, "saturation", delay_rule, profile, resolution, dithered)

    if delay_rule == "given":
        delays = [delay]
    else:
        delays = range(1, min(6, max_lag) + 1)
        delay_rule = "entropy-ratio"
    try:
        dimension, delay, _ = entropy_ratio(x, dims=range(2, max_dim + 1), delays=delays)
    except ValueError as err:
        raise ValueError(
            "could not choose an embedding: the intrinsic dimension never reached a "
            "plateau and the entropy ratio is undefined. The series may repeat values "
            "exactly (an exactly periodic or block-repeated signal); pass "
            "embedding_dimension and embedding_delay explicitly. "
            f"Profile for E=1..{max_dim + 1}: {np.round(profile, 2).tolist()}"
        ) from err
    return _choice(dimension, delay, "entropy-ratio", delay_rule, profile, resolution, dithered)
