import numpy as np
import pytest

from tests.systems import lorenz, rossler
from uniqed.embedding.delay import autocorrelation, choose_delay


def test_autocorrelation_of_sine_crosses_zero_at_quarter_period():
    t = np.arange(4000)
    x = np.sin(2 * np.pi * t / 100)
    acf = autocorrelation(x, max_lag=200)
    assert acf[0] == pytest.approx(1.0)
    assert acf[50] == pytest.approx(-1.0, abs=0.02)
    assert acf[25] == pytest.approx(0.0, abs=0.01)


def test_choose_delay_sine_is_quarter_period_by_zero_crossing():
    t = np.arange(4000)
    x = np.sin(2 * np.pi * t / 100)
    tau, rule = choose_delay(x)
    assert (tau, rule) == (25, "zero-crossing")


def test_choose_delay_falls_back_to_first_minimum_when_acf_stays_positive():
    # AR(1) with rho=0.995 keeps the autocorrelation positive over the search range;
    # a period-40 component of equal spread adds a local minimum near half a period.
    rng = np.random.default_rng(0)
    n = 20000
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.995 * x[i - 1] + rng.normal()
    x = x + np.std(x) * np.cos(2 * np.pi * np.arange(n) / 40)
    tau, rule = choose_delay(x, max_lag=60)
    assert rule == "first-minimum"
    assert 15 <= tau <= 25


def test_choose_delay_white_noise_is_one():
    rng = np.random.default_rng(1)
    tau, rule = choose_delay(rng.normal(size=5000))
    assert tau == 1
    assert rule == "zero-crossing"


def test_choose_delay_rejects_short_or_constant_input():
    with pytest.raises(ValueError):
        choose_delay(np.ones(100))
    with pytest.raises(ValueError):
        choose_delay(np.arange(3.0))


def test_choose_delay_takes_the_earlier_turning_point():
    # Lorenz: the zero crossing sits at 200-400 samples, the first minimum at 50-80.
    for seed in range(4):
        tau, rule = choose_delay(lorenz(10000, seed=seed))
        assert rule == "first-minimum", seed
        assert 50 <= tau <= 80, (seed, tau)
    # Rossler: the zero crossing (29) comes before the first minimum (58).
    tau, rule = choose_delay(rossler(10000))
    assert (tau, rule) == (29, "zero-crossing")
