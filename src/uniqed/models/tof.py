import numpy as np

from abc import ABCMeta, abstractmethod

from sklearn.base import BaseEstimator, ClassifierMixin, OutlierMixin
from scipy.spatial import cKDTree

# Distances within this relative slack of the k-th distance count as tied. Values on a decimal grid
# do not subtract exactly in floating point (70.2 - 70.1 and 70.3 - 70.2 differ by about 1e-14), so
# without it, equal steps in the data would not tie. Values themselves are compared exactly.
TIE_SLACK = 1e-12
# Rows per radius query, so memory stays bounded when neighbourhoods are large.
CHUNK = 1000
# Time distances held at once per twin-group block, so memory stays bounded for any group size.
BLOCK_ELEMENTS = 1_000_000
# Exact int64 sums of squared time distances hold below this many rows (n**3 / 3 < 2**63).
MAX_ROWS_EXACT = 2_000_000


class TOF(BaseEstimator, ClassifierMixin, OutlierMixin):
    def __init__(self, cutoff_n=1.0, k=None, q=2, centrality_func=np.mean):
        """Constructor for Temporal Outlier Factor detector

        :param int cutoff_n: maximal possible event length in sample points (default: cutoff_n=1)
        :param int k: number of neighbors to use (default: k=None, itt will use k=d+1, where d is the data-dimension)
        :param float q: norm to us (default: q=2 Euclidean norm)
        :param func centrality_func: Centrality-measure to use in the estimation of TOF score
                                     (default: centrality_func=np.mean)
        """
        self.cutoff_n = cutoff_n
        self.k = k
        self.q = q
        self.centrality_func = centrality_func

    def fit(self, X, y=None):
        """Fits the model

        :param X: data (n_dataponts, d) shape
        :param y: None
        :return: self
        """
        self.X_ = X
        self.d_ = X.shape[1]

        self.outlier_score_ = self._compute_outlier_score(X, self.k)
        self.cutoff_ = self._compute_cutoff(self.cutoff_n)
        self.p_value_ = self._compute_p_value(self.outlier_score_)
        return self

    def predict(self, X):
        """Classify the points

        :param numpy.ndarray X: data (n_dataponts, d) shape
        :return: class labels (-1 and 1)
        :rtype: numpy.ndarray
        """
        outliers_bool = self._compute_outlier_score(X, self.k) > self.cutoff_

        if sum(outliers_bool) > (len(outliers_bool) / 2.0):
            outliers_bool = (1 - outliers_bool).astype(bool)

        prediction = np.zeros([X.shape[0], 1])
        prediction[outliers_bool] = 1

        prediction = (2 * prediction.astype(int)) - np.ones([X.shape[0], 1], dtype=int)

        self.y_pred_ = prediction
        self.outliers_inds_ = self._get_outliers_inds(outliers_bool)
        self.outlier_p_values_ = self.p_value_[outliers_bool]
        return prediction

    def _get_outliers_inds(self, outliers_bool):
        """Returns outlier inds from Boolean array

        :param numpy.ndarray of bool outliers_bool: array with truth-values of outlierness
        :return: indices
        :rtype: numpy.ndarray of int
        """
        return np.where(outliers_bool)[0]

    def _find_nearest_neighbors(self, X, k=None):
        """Finds k-nearest neighbor distances and indices by using the cKDTree class

        :param np.ndarray of float X: points
        :param int k: number of neighbors (default: k=None)
        :return: neighbor distances and indices
        :rtype: (numpy.ndarray of float, numpy.ndarray of int)
        """
        if k is None:
            k = self.d_ + 1
        tree = cKDTree(self.X_)
        distances, indicis = tree.query(X, k + 1)
        if X is not self.X_:
            return distances[:, 1:], indicis[:, 1:]

        # with exact twins the point itself need not come first: drop it by index,
        # or drop the last result when more than k twins pushed it out
        is_self = indicis == np.arange(X.shape[0]).reshape([-1, 1])
        is_self[~is_self.any(axis=1), -1] = True
        keep = ~is_self
        return (
            distances[keep].reshape([X.shape[0], k]),
            indicis[keep].reshape([X.shape[0], k]),
        )

    def _compute_cutoff(self, cutoff_n):
        """Computes cutoff threshold for the outlier-score

        :param int cutoff_n: the length of
        :return: cutoff threshold value
        :rtype: float
        """
        if (
            type(cutoff_n) == int
            or type(cutoff_n) == np.float64
            or type(cutoff_n) == float
            or type(cutoff_n) == np.int64
        ):
            if self.k is None:
                k = self.d_ + 1
            else:
                k = self.k
            if cutoff_n < k:
                cutoff_n = k

            neighborinds = np.reshape(np.arange(cutoff_n, cutoff_n - k, -1), [1, k])
            cutoff = self._compute_tof(neighborinds, np.zeros([1, 1]))[0]
            cutoff = 1.0 / cutoff
        else:
            print(type(cutoff_n), cutoff_n)
            raise ValueError("Invalid value for cutoff_n")

        return cutoff

    def _compute_p_value(self, outlier_score):
        p_value = (np.argsort(np.argsort(outlier_score)) + 1) / float(
            len(outlier_score)
        )
        return p_value

    def _compute_outlier_score(self, X, k=None):
        """Computes 1/TOF for X

        On the fitted data the neighbours are every point at the k-th nearest distance or closer,
        ties included; on new data, the k nearest.

        :param numpy.ndarray X: dataset
        :param int k: number of neighbors
        :return: 1/TOF outlier score
        """
        if X is self.X_:
            return 1.0 / self._tie_inclusive_tof(X, self.d_ + 1 if k is None else k)

        embedded_length = X.shape[0]

        # get point indicis, find k-nn and compute
        # the average temporal distance
        indicis = np.arange(0, embedded_length).reshape([embedded_length, 1])
        nearest_indicis = self._find_nearest_neighbors(X, k=k)[1]
        outlier_score_ = 1.0 / self._compute_tof(nearest_indicis, indicis)

        return outlier_score_

    def _tie_inclusive_tof(self, X, k):
        """TOF over every point at the k-th nearest distance or closer, ties included

        A point is never its own neighbour. Points with no tie at their k-th distance get exactly
        the k neighbours of 0.1.1. Sets ``neighbourhood_size_``.

        :param numpy.ndarray X: the fitted data
        :param int k: number of neighbors
        :return: TOF score
        """
        X = np.asarray(X)
        n = X.shape[0]
        if n <= k:
            raise ValueError(f"TOF needs more than k = {k} embedded points, got {n}")
        tree = cKDTree(X)
        # the point itself is among the results at distance 0, so column k is the k-th other point
        distances, indicis = tree.query(X, k + 2)
        kdist = distances[:, k]
        tof = np.empty(n)
        size = np.full(n, k)

        # no tie at the k-th distance: the k + 1 results minus the point itself
        clean = (kdist > 0) & (distances[:, k + 1] > kdist * (1 + TIE_SLACK))
        rows = np.flatnonzero(clean)
        nearest = indicis[rows, : k + 1]
        nearest = nearest[nearest != rows[:, None]].reshape(len(rows), k)
        tof[rows] = self._compute_tof(nearest, rows[:, None])

        # k or more exact twins: the neighbourhood is the whole twin group
        twins = np.flatnonzero(kdist == 0)
        if len(twins):
            _, group = np.unique(X, axis=0, return_inverse=True)
            group = group.ravel()
            for g in np.unique(group[twins]):
                members = np.flatnonzero(group == g)
                tof[members] = self._twin_group_tof(members)
                size[members] = len(members) - 1

        # a tie at the k-th distance between distinct points: every point within that distance
        boundary = np.flatnonzero(~clean & (kdist > 0))
        for start in range(0, len(boundary), CHUNK):
            part = boundary[start : start + CHUNK]
            balls = tree.query_ball_point(X[part], kdist[part] * (1 + TIE_SLACK))
            for i, ball in zip(part, balls):
                neighbours = np.asarray(ball)
                neighbours = neighbours[neighbours != i]
                tof[i] = self._compute_tof(neighbours[None, :], np.array([[i]]))[0]
                size[i] = len(neighbours)

        self.neighbourhood_size_ = size
        return tof

    def _twin_group_tof(self, members):
        """TOF of each member of an exact-twin group over the other members

        :param numpy.ndarray of int members: indices of the group, ascending
        :return: TOF score per member
        """
        m = len(members)
        if self.q == 2 and self.centrality_func is np.mean and members[-1] < MAX_ROWS_EXACT:
            # sum over j of (t_j - t_i)^2, exact in int64
            t = members.astype(np.int64)
            s1, s2 = t.sum(), (t * t).sum()
            return np.sqrt((s2 - 2 * t * s1 + m * t * t) / (m - 1))
        # any other q or centrality: every pair, in blocks; time grows with the group size squared
        out = np.empty(m)
        block = max(1, BLOCK_ELEMENTS // m)
        for start in range(0, m, block):
            rows = members[start : start + block]
            others = np.broadcast_to(members, (len(rows), m))
            others = others[others != rows[:, None]].reshape(len(rows), m - 1)
            out[start : start + block] = self._compute_tof(others, rows[:, None])
        return out

    def _compute_tof(self, nearest_indicis, indicis):
        """Computes TOF score from nearest neighbor indices and the indice list of the actual moment

        :param nearest_indicis: indices of nearestneighbors
        :param indicis: the actual moment
        :return:
        """
        q = self.q
        tof = self.centrality_func(np.abs(nearest_indicis - indicis) ** q, axis=1) ** (
            1.0 / q
        )

        return tof

    def _compute_perc_cutoff(self, cutoff_n):
        """Computes threshold for cutoff value given in per cent

        :param int cutoff_n: per cent value (between 0 and 100)
        :return: threshold value
        :rtype: float
        """
        cutoff_len = int(self.X_.shape[0] * (cutoff_n / 100.0))
        cutoff = np.sort(self.outlier_score_)[-cutoff_len]
        return cutoff
