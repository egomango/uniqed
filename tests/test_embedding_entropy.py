import numpy as np
import pytest

from uniqed.embedding.entropy import entropy_ratio, iaaft_surrogate, kl_entropy


def test_kl_entropy_of_gaussian_matches_closed_form():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(20000, 2))
    expected = 2 * 0.5 * np.log(2 * np.pi * np.e)  # two independent unit normals
    assert kl_entropy(X) == pytest.approx(expected, abs=0.1)


def test_iaaft_surrogate_keeps_values_and_spectrum():
    rng = np.random.default_rng(0)
    t = np.arange(2048)
    x = np.sin(2 * np.pi * t / 64) + 0.3 * rng.normal(size=t.size)
    s = iaaft_surrogate(x, np.random.default_rng(1))
    assert np.allclose(np.sort(s), np.sort(x))
    px, ps = np.abs(np.fft.rfft(x)), np.abs(np.fft.rfft(s))
    assert np.corrcoef(px, ps)[0, 1] > 0.99
    assert not np.allclose(s, x)


def test_entropy_ratio_finds_delay_of_a_noisy_delayed_henon_map():
    # Henon map with delay d (Gautama 2003, Sec. 3, Eq. 5): x[n] = 1 - 1.4 x[n-d]^2 + 0.3 x[n-2d],
    # random initial history, plus 10% observation noise so the differential entropy is
    # positive (the regime the fallback is for). The delay must come out as d. The dimension
    # is weakly determined by the MDL term at this sample size and drifts upward; it is only
    # asserted to stay inside the grid.
    d = 3
    n = 2000
    rng = np.random.default_rng(0)
    x = np.zeros(n + 2 * d)
    x[: 2 * d] = rng.uniform(-0.1, 0.1, size=2 * d)
    for i in range(2 * d, n + 2 * d):
        x[i] = 1.0 - 1.4 * x[i - d] ** 2 + 0.3 * x[i - 2 * d]
    x = x[2 * d :]
    x = x + 0.1 * x.std() * rng.normal(size=n)
    dim, tau, table = entropy_ratio(x, dims=range(2, 6), delays=range(1, 7))
    assert tau == d
    assert 2 <= dim <= 5
    assert table.shape == (4, 6)
    assert np.all(np.isfinite(table))


def test_entropy_ratio_refuses_a_thin_deterministic_set():
    # A long Henon series has negative differential entropy in two dimensions: the
    # ratio is undefined and the function must say so instead of returning a minimum.
    rng = np.random.default_rng(0)
    x = np.zeros(6000)
    x[:2] = rng.uniform(-0.1, 0.1, size=2)
    for i in range(2, 6000):
        x[i] = 1.0 - 1.4 * x[i - 1] ** 2 + 0.3 * x[i - 2]
    with pytest.raises(ValueError, match="too structured"):
        entropy_ratio(x, dims=range(2, 4), delays=range(1, 3))
