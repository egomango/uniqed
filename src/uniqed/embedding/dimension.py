import numpy as np
from scipy.spatial import cKDTree

from uniqed.transformers.transformers import TimeDelayEmbedder


def intrinsic_dimension(X, k=10):
    """Median Farahmand-Szepesvari-Audibert estimate of the intrinsic dimension.

    Local estimate at each point: ln 2 / ln(R_2k / R_k), where R_k is the distance
    to the k-th nearest neighbour (Benko et al. 2022, arXiv 2008.03221, Eq. 4).
    The global value is the median of the local estimates (their Theorem 1).

    :param numpy.ndarray X: points, shape (n, d)
    :param int k: neighbourhood size; the estimate uses neighbours k and 2k
    :return: intrinsic dimension estimate
    :rtype: float
    """
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    n = X.shape[0]
    if n <= 2 * k + 1:
        raise ValueError(f"need more than {2 * k + 1} points for k={k}, got {n}")
    distances, _ = cKDTree(X).query(X, 2 * k + 1)
    r_k = distances[:, k]
    r_2k = distances[:, 2 * k]
    valid = (r_k > 0) & (r_2k > r_k)
    local = np.log(2.0) / np.log(r_2k[valid] / r_k[valid])
    return float(np.median(local))


def dimension_profile(x, tau, max_dim=8, k=10, max_points=5000, seed=0):
    """Intrinsic dimension of the delay embedding for E = 1..max_dim (paper Fig. S9 B).

    The same subsample of embedded rows is used for every E so the estimates are
    comparable; the largest embedding fixes how many rows exist.

    :param numpy.ndarray x: 1D series
    :param int tau: embedding delay
    :param int max_dim: largest embedding dimension to evaluate
    :param int k: neighbourhood size passed to :func:`intrinsic_dimension`
    :param int max_points: rows subsampled for speed
    :param int seed: subsample seed
    :return: array of length max_dim, entry i is the estimate at E = i + 1
    :rtype: numpy.ndarray
    """
    x = np.asarray(x, dtype=float).ravel()
    n_rows = len(x) - (max_dim - 1) * tau
    if n_rows <= 2 * k + 1:
        raise ValueError("series too short for max_dim and tau")
    rng = np.random.default_rng(seed)
    rows = np.sort(rng.choice(n_rows, size=min(max_points, n_rows), replace=False))
    profile = np.empty(max_dim)
    for dim in range(1, max_dim + 1):
        X = TimeDelayEmbedder(d=dim, tau=tau).fit_transform(x)[:n_rows][rows]
        profile[dim - 1] = intrinsic_dimension(X, k=k)
    return profile


MIN_DIMENSION = 3


def choose_dimension(x, tau, max_dim=8, k=10, gap=0.5, slope=0.25, profile=None, min_dim=MIN_DIMENSION):
    """Embedding dimension where the intrinsic-dimension estimate leaves the diagonal.

    Rule (paper SI, Fig. S9 B and S10 B): the smallest E such that the estimate is
    at least ``gap`` below E and rises by less than ``slope`` when E grows by one,
    but never below ``min_dim``. Returns None when no such E exists up to
    ``max_dim``: the estimate keeps tracking the embedding dimension, the mark of a
    stochastic signal (Fig. S11), and the caller falls back to the entropy method.

    The floor: the first-deviation E is the smallest dimension that holds the
    attractor, not one that unfolds it; a curve self-intersects in the plane. The
    paper never embedded below three. On its simulated ECG the first-deviation rule
    gives E=2 and F1 0.78; the floor gives E=3 and 0.86, above the paper's hand-set
    0.82 and below its labelled-grid-search optimum 0.94 (docs/log.md, A1).

    :param numpy.ndarray x: 1D series
    :param int tau: embedding delay
    :param int max_dim: largest dimension considered
    :param int k: neighbourhood size for the estimator
    :param float gap: how far below the diagonal the estimate must sit
    :param float slope: largest rise allowed from E to E + 1
    :param numpy.ndarray profile: a precomputed :func:`dimension_profile` of length
                                  at least max_dim + 1, to avoid recomputing it
    :param int min_dim: floor on the returned dimension
    :return: embedding dimension, or None
    """
    if profile is None:
        profile = dimension_profile(x, tau, max_dim=max_dim + 1, k=k)
    if len(profile) < max_dim + 1:
        raise ValueError("profile must cover E = 1..max_dim + 1")
    for dim in range(1, max_dim + 1):
        estimate = profile[dim - 1]
        if dim - estimate >= gap and profile[dim] - estimate < slope:
            return max(dim, min_dim)
    return None
