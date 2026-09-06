import numpy as np
import pytest

from tests.systems import lorenz
from uniqed.embedding import EmbeddingChoice, choose_embedding, quantisation


def test_lorenz_is_chosen_by_saturation_with_dimension_three():
    choice = choose_embedding(lorenz(10000))
    assert isinstance(choice, EmbeddingChoice)
    assert choice.method == "saturation"
    assert choice.dimension == 3
    assert choice.delay >= 2
    assert choice.window == (choice.dimension - 1) * choice.delay
    assert len(choice.dimension_profile) >= 4


def test_white_noise_routes_to_entropy_ratio():
    rng = np.random.default_rng(3)
    choice = choose_embedding(rng.normal(size=4000), max_dim=6)
    assert choice.method == "entropy-ratio"
    assert choice.delay_rule == "entropy-ratio"  # the grid chose it, not the autocorrelation
    assert 2 <= choice.dimension <= 6


def test_fixed_delay_only_chooses_dimension():
    choice = choose_embedding(lorenz(10000), delay=10)
    assert choice.delay == 10
    assert choice.dimension == 3
    assert choice.delay_rule == "given"


def test_fixed_dimension_only_chooses_delay():
    x = lorenz(10000)
    choice = choose_embedding(x, dimension=4)
    assert choice.dimension == 4
    assert choice.method == "given"
    assert choice.delay == choose_embedding(x).delay


def test_quantisation_detects_a_step_and_ignores_continuous_data():
    rng = np.random.default_rng(0)
    assert quantisation(rng.normal(size=5000)) == 0.0
    assert quantisation(np.round(rng.normal(size=5000), 2)) == 0.01
    assert quantisation(np.round(7.5 * rng.normal(size=5000))) == 1.0


def test_quantised_lorenz_is_dithered_and_still_three():
    x = np.round(lorenz(10000), 1)  # one decimal: about 400 distinct values
    choice = choose_embedding(x)
    assert choice.dithered
    assert choice.resolution == 0.1
    assert choice.dimension == 3
    assert choice.method == "saturation"


def test_quantised_white_noise_routes_to_entropy_ratio_without_error():
    rng = np.random.default_rng(4)
    x = np.round(rng.normal(size=4000), 1)
    choice = choose_embedding(x, max_dim=6)
    assert choice.dithered
    assert choice.method == "entropy-ratio"


def test_exactly_periodic_signal_raises_with_advice():
    # Integer period in samples: 80 distinct phases repeated 75 times, so embedded points
    # coincide and neither estimator is defined. The router must say so, not guess.
    t = np.arange(6000)
    x = np.sin(2 * np.pi * t / 80) + 0.3 * np.sin(4 * np.pi * t / 80)
    with pytest.raises(ValueError, match="pass embedding_dimension and embedding_delay"):
        choose_embedding(x)


def test_short_series_raises_with_advice():
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="too short to choose an embedding"):
        choose_embedding(rng.normal(size=80))
    with pytest.raises(ValueError, match="too short to choose an embedding"):
        choose_embedding(rng.normal(size=400))


def test_short_noise_never_reports_a_plateau():
    # Just above the minimum length: the saturation rule must not mistake the
    # estimator's small-sample bias for a plateau (that is what MIN_ROWS is for).
    for seed in range(5):
        x = np.random.default_rng(seed).normal(size=520)
        choice = choose_embedding(x)
        assert choice.method == "entropy-ratio", (seed, choice)


def test_too_few_cycles_raises_instead_of_guessing():
    # One daily cycle at two-minute sampling: the zero crossing sits at lag 150,
    # beyond the largest delay 1000 samples can support.
    t = np.arange(1000)
    x = np.sin(2 * np.pi * t / 600) + 0.1 * np.random.default_rng(0).normal(size=1000)
    with pytest.raises(ValueError, match="too few cycles"):
        choose_embedding(x)
    # Explicit values still work on the same series.
    choice = choose_embedding(x, dimension=3, delay=150)
    assert (choice.dimension, choice.delay, choice.method) == (3, 150, "given")
