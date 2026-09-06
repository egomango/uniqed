import numpy as np
from scipy.spatial import cKDTree
from scipy.special import digamma, gammaln

from uniqed.transformers.transformers import TimeDelayEmbedder


def kl_entropy(X):
    """Kozachenko-Leonenko differential entropy from nearest-neighbour distances (nats).

    H = psi(n) - psi(1) + ln c_d + (d / n) * sum ln rho_i, with c_d the volume of the
    d-dimensional unit ball and rho_i the distance from point i to its nearest neighbour.

    :param numpy.ndarray X: points, shape (n, d)
    :return: entropy estimate
    :rtype: float
    """
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    n, d = X.shape
    rho = cKDTree(X).query(X, 2)[0][:, 1]
    rho = rho[rho > 0]
    log_unit_ball = (d / 2.0) * np.log(np.pi) - gammaln(d / 2.0 + 1.0)
    return float(digamma(n) - digamma(1) + log_unit_ball + d * np.mean(np.log(rho)))


def iaaft_surrogate(x, rng, n_iter=100):
    """Iterative amplitude-adjusted Fourier transform surrogate (Schreiber & Schmitz 1996).

    Keeps the value distribution of ``x`` exactly and its power spectrum approximately,
    with the phases randomised.

    :param numpy.ndarray x: 1D series
    :param numpy.random.Generator rng: source of the initial shuffle
    :param int n_iter: number of amplitude/spectrum alternations
    :return: surrogate series of the same length
    :rtype: numpy.ndarray
    """
    x = np.asarray(x, dtype=float).ravel()
    sorted_x = np.sort(x)
    target_amplitude = np.abs(np.fft.rfft(x))
    s = rng.permutation(x)
    for _ in range(n_iter):
        spectrum = np.fft.rfft(s)
        phases = np.angle(spectrum)
        s = np.fft.irfft(target_amplitude * np.exp(1j * phases), n=len(x))
        ranks = np.argsort(np.argsort(s))
        s = sorted_x[ranks]
    return s


def _embedded_entropy(x, dim, tau, n_rows):
    X = TimeDelayEmbedder(d=dim, tau=tau).fit_transform(x)[:n_rows]
    return kl_entropy(X)


def entropy_ratio(x, dims=range(2, 9), delays=range(1, 7), n_surrogates=5, seed=0, max_points=4000):
    """Embedding (E, tau) by the entropy-ratio criterion of Gautama, Mandic & Van Hulle (ICASSP 2003).

    I(m, tau) = H(x_{m,tau}) / mean_i H(s_i_{m,tau}) over iAAFT surrogates s_i, and
    R_ent(m, tau) = I(m, tau) * (1 + m ln N / N) with N the number of delay vectors,
    held constant over the grid. The minimum of R_ent is the choice.

    :param numpy.ndarray x: 1D series
    :param iterable dims: embedding dimensions to try
    :param iterable delays: embedding delays to try
    :param int n_surrogates: surrogates per grid point (the paper used 5)
    :param int seed: surrogate seed
    :param int max_points: leading samples used, for runtime
    :return: (dimension, delay, table) with table[i, j] = R_ent(dims[i], delays[j])
    :rtype: (int, int, numpy.ndarray)
    :raises ValueError: when a differential entropy in the grid is not positive
    """
    x = np.asarray(x, dtype=float).ravel()
    dims, delays = list(dims), list(delays)
    if len(x) > max_points:
        x = x[:max_points]
    # The ratio of two differential entropies is not scale invariant; standardise
    # so that comparable signals give comparable tables.
    if x.std() <= 0:
        raise ValueError("series has zero variance")
    x = (x - x.mean()) / x.std()
    n_rows = len(x) - (max(dims) - 1) * max(delays)
    if n_rows < 10 * max(dims):
        raise ValueError("series too short for the requested grid")
    rng = np.random.default_rng(seed)
    surrogates = [iaaft_surrogate(x, rng) for _ in range(n_surrogates)]
    table = np.empty((len(dims), len(delays)))
    for i, dim in enumerate(dims):
        penalty = 1.0 + dim * np.log(n_rows) / n_rows
        for j, tau in enumerate(delays):
            h_signal = _embedded_entropy(x, dim, tau, n_rows)
            h_surr = np.mean([_embedded_entropy(s, dim, tau, n_rows) for s in surrogates])
            if not (h_signal > 0 and h_surr > 0):
                # A non-positive differential entropy flips the sign of the ratio and
                # the minimum stops meaning anything. It happens on thin, deterministic
                # sets, which the saturation rule handles; not on the stochastic
                # signals this fallback is for.
                raise ValueError(
                    f"entropy ratio undefined at E={dim}, tau={tau}: "
                    f"H(signal)={h_signal:.3f}, H(surrogates)={h_surr:.3f}; "
                    "the series is too structured for the entropy-ratio method"
                )
            table[i, j] = (h_signal / h_surr) * penalty
    i, j = np.unravel_index(np.argmin(table), table.shape)
    return dims[i], delays[j], table
