"""A point never counts as its own neighbour (story A-bug, 0.1.1).

`_find_nearest_neighbors` queried k + 1 results and dropped the first, assuming it is the point
itself. With exact twin points cKDTree may return a twin first, and the point stays among its own
neighbours at time distance 0. The tests check properties, not one tie order, since cKDTree's order
among equal distances can change between scipy versions.
"""
import numpy as np
import pytest
from scipy.spatial import cKDTree

from uniqed.models.tof import TOF


def _twin_data(n_twins, n_distinct=40, d=3, seed=0):
    # n_twins identical points among distinct random ones, twins spread through the series
    rng = np.random.default_rng(seed)
    X = rng.random((n_twins + n_distinct, d)) + 1.0
    twin_rows = rng.choice(len(X), size=n_twins, replace=False)
    X[twin_rows] = 0.0
    return X, np.sort(twin_rows)


@pytest.mark.parametrize("k", [2, 3, 4, 6])
@pytest.mark.parametrize("n_twins", [3, 5, 12])
def test_no_point_is_its_own_neighbour(k, n_twins):
    X, _ = _twin_data(n_twins)
    tof = TOF(k=k).fit(X)
    distances, neighbours = tof._find_nearest_neighbors(X, k=k)

    assert neighbours.shape == (len(X), k)
    own = np.arange(len(X)).reshape(-1, 1)
    rows_listing_self = np.where(np.any(neighbours == own, axis=1))[0]
    assert rows_listing_self.size == 0, f"rows listing themselves: {rows_listing_self}"
    for row in neighbours:
        assert len(set(row)) == k


def test_twins_come_back_at_distance_zero():
    k = 3
    X, twin_rows = _twin_data(n_twins=8)
    tof = TOF(k=k).fit(X)
    distances, neighbours = tof._find_nearest_neighbors(X, k=k)

    # 8 twins: each has 7 others at distance 0, so all k neighbours are twins
    assert np.all(distances[twin_rows] == 0.0)
    assert np.all(np.isin(neighbours[twin_rows], twin_rows))


def test_default_k_excludes_self():
    X, _ = _twin_data(n_twins=6)
    tof = TOF().fit(X)
    _, neighbours = tof._find_nearest_neighbors(X)

    assert neighbours.shape[1] == X.shape[1] + 1
    assert not np.any(neighbours == np.arange(len(X)).reshape(-1, 1))


def test_without_twins_neighbours_are_unchanged():
    k = 4
    rng = np.random.default_rng(1)
    X = rng.random((60, 3))
    tof = TOF(k=k).fit(X)
    _, neighbours = tof._find_nearest_neighbors(X, k=k)

    expected = cKDTree(X).query(X, k + 1)[1][:, 1:]
    assert np.array_equal(neighbours, expected)


def test_new_data_keeps_todays_behaviour():
    # scoring new data is out of scope: it keeps dropping the first result
    k = 3
    X, _ = _twin_data(n_twins=5)
    X_new, _ = _twin_data(n_twins=5, seed=7)
    tof = TOF(k=k).fit(X)
    _, neighbours = tof._find_nearest_neighbors(X_new, k=k)

    expected = cKDTree(X).query(X_new, k + 1)[1][:, 1:]
    assert np.array_equal(neighbours, expected)


def test_predict_on_fitted_data_uses_the_fitted_scores():
    # the runner calls predict on the fitted data (runners/tof_run.py); it must see the fix too
    k = 3
    X, _ = _twin_data(n_twins=12)
    tof = TOF(k=k).fit(X)

    assert np.array_equal(tof._compute_outlier_score(X, k), tof.outlier_score_)
