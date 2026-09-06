import numpy as np

MIN_SAMPLES = 10


def autocorrelation(x, max_lag):
    """Biased sample autocorrelation of ``x`` at lags 0..max_lag, via FFT.

    :param numpy.ndarray x: 1D series
    :param int max_lag: largest lag to return
    :return: array of length max_lag + 1 with acf[0] == 1
    :rtype: numpy.ndarray
    """
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    n = len(x)
    n_fft = 1 << int(np.ceil(np.log2(2 * n - 1)))
    spectrum = np.fft.rfft(x, n_fft)
    acov = np.fft.irfft(spectrum * np.conj(spectrum), n_fft)[: max_lag + 1]
    if acov[0] <= 0:
        raise ValueError("series has zero variance")
    return acov / acov[0]


def choose_delay(x, max_lag=None):
    """Embedding delay from the first turning point of the autocorrelation.

    The paper's supplement selects the delay at the first zero crossing of the
    autocorrelation (Fig. S9, polysomnography, lag 5) or at its first local minimum
    (Fig. S10, gravitational wave, lag 8, where the zero crossing sat at 16-17). The
    rule here is the earlier of the two, which is what both examples did. When
    neither exists within ``max_lag`` the delay is 1 and the rule is "none".

    On Lorenz the zero crossing alone lands at 200-400 samples, several oscillations,
    and the reconstruction at that delay is poor; the first minimum at 50-70 gives
    the expected dimension (measured 2026-09-06).

    :param numpy.ndarray x: 1D series
    :param int max_lag: search range (default: a quarter of the series)
    :return: (delay, rule) with rule in "zero-crossing", "first-minimum", "none"
    :rtype: (int, str)
    """
    x = np.asarray(x, dtype=float).ravel()
    if len(x) < MIN_SAMPLES:
        raise ValueError(f"need at least {MIN_SAMPLES} samples, got {len(x)}")
    if max_lag is None:
        max_lag = max(2, len(x) // 4)
    max_lag = min(max_lag, len(x) - 2)
    acf = autocorrelation(x, max_lag)

    candidates = []
    nonpositive = np.flatnonzero(acf[1:] <= 0)
    if len(nonpositive):
        # Linear interpolation between the last positive lag and the first
        # non-positive one, rounded to the nearest integer lag, at least 1.
        after = int(nonpositive[0] + 1)
        before = after - 1
        crossing = before + acf[before] / (acf[before] - acf[after])
        candidates.append((max(1, int(round(crossing))), "zero-crossing"))

    interior = acf[1:-1]
    minima = np.flatnonzero((interior < acf[:-2]) & (interior <= acf[2:]))
    if len(minima):
        candidates.append((int(minima[0] + 1), "first-minimum"))

    if not candidates:
        return 1, "none"
    # Earlier lag wins; on a tie the zero crossing, the paper's primary rule.
    return min(candidates, key=lambda c: (c[0], c[1] != "zero-crossing"))
