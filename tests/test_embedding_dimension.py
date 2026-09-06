import numpy as np
import pytest

from tests.systems import lorenz, rossler
from uniqed.embedding.delay import choose_delay
from uniqed.embedding.dimension import choose_dimension, dimension_profile, intrinsic_dimension


def test_intrinsic_dimension_of_uniform_cube_is_its_dimension():
    rng = np.random.default_rng(0)
    for d in (1, 2, 3):
        X = rng.uniform(size=(4000, d))
        assert intrinsic_dimension(X, k=10) == pytest.approx(d, abs=0.35)
    # Edge effects bias the estimate downward on hypercubes as d grows
    # (Benko et al. 2022 fit a correction for it; we do not apply one).
    X = rng.uniform(size=(4000, 5))
    assert intrinsic_dimension(X, k=10) == pytest.approx(5, abs=0.6)


def test_intrinsic_dimension_of_a_curve_in_3d_is_one():
    t = np.linspace(0, 20, 4000)
    X = np.stack([np.cos(t), np.sin(t), 0.1 * t], axis=1)
    assert intrinsic_dimension(X, k=10) == pytest.approx(1.0, abs=0.2)


def test_dimension_profile_of_lorenz_saturates_near_two():
    x = lorenz(10000)
    tau, _ = choose_delay(x)
    profile = dimension_profile(x, tau, max_dim=6)
    assert profile[0] == pytest.approx(1.0, abs=0.15)
    assert 1.8 <= profile[2] <= 2.5  # E = 3
    assert abs(profile[5] - profile[2]) < 0.4  # flat from E = 3 to E = 6


def test_choose_dimension_lorenz_and_rossler_are_three():
    for system in (lorenz, rossler):
        x = system(10000)
        tau, _ = choose_delay(x)
        assert choose_dimension(x, tau) == 3, system.__name__


def test_choose_dimension_white_noise_has_no_plateau():
    rng = np.random.default_rng(2)
    x = rng.normal(size=6000)
    assert choose_dimension(x, tau=1, max_dim=8) is None


def test_choose_dimension_floor_lifts_a_curve_to_three():
    # A periodic signal is a closed curve: intrinsic dimension 1, first deviation at E=2.
    # Two unrelated periods would trace a torus (dimension 2) and not test the floor; an
    # integer period in samples would repeat values exactly and defeat the estimator.
    t = np.arange(6000)
    x = np.sin(2 * np.pi * t / 80.37) + 0.3 * np.sin(4 * np.pi * t / 80.37)
    tau, _ = choose_delay(x)
    assert choose_dimension(x, tau, min_dim=1) == 2
    assert choose_dimension(x, tau) == 3
