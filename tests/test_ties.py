"""On the fitted data, neighbours are every point at the k-th nearest distance or closer (story
A-ties, 0.1.2).

Up to 0.1.1 the neighbours were exactly k points, and among points tied at the k-th distance the
search's order chose which ones counted. The tests compare with a brute-force computation that has
no order, so they check the rule, not one tie order.
"""
import numpy as np
import pandas as pd
import pytest
from scipy.spatial import cKDTree

from uniqed.models.tof import TOF
from uniqed.transformers.transformers import TimeDelayEmbedder


def _embed(x, d=3, tau=1):
    return TimeDelayEmbedder(d=d, tau=tau).fit_transform(np.asarray(x, dtype=float))


def _brute_force_score(X, k, q=2, centrality_func=np.mean):
    # every distance; the k-th smallest to another row; every row at or within it
    t = np.arange(len(X))
    scores = np.empty(len(X))
    for i in range(len(X)):
        d = np.sqrt(((X - X[i]) ** 2).sum(axis=1))
        d[i] = np.inf
        kth = np.partition(d, k - 1)[k - 1]
        # equal steps on a decimal grid differ in the last bits (see TIE_SLACK)
        neighbours = t[d <= kth * (1 + 1e-12)]
        scores[i] = 1.0 / centrality_func(np.abs(neighbours - i) ** q) ** (1.0 / q)
    return scores


def _k_nearest_score(tof, X):
    # the 0.1.1 rule: exactly k neighbours
    neighbours = tof._find_nearest_neighbors(X)[1]
    return 1.0 / tof._compute_tof(neighbours, np.arange(len(X)).reshape(-1, 1))


@pytest.mark.parametrize("q, centrality_func", [(2, np.mean), (1, np.median), (3, np.mean)])
def test_tied_data_matches_brute_force(q, centrality_func):
    X = _embed(np.random.default_rng(0).integers(0, 3, 400))
    tof = TOF(cutoff_n=6, q=q, centrality_func=centrality_func).fit(X)
    expected = _brute_force_score(X, 4, q, centrality_func)
    np.testing.assert_allclose(tof.outlier_score_, expected, rtol=1e-12, atol=0)


def test_tied_data_has_ties_at_the_kth_distance():
    # guards the test above: the data must have the ties it is meant to test
    X = _embed(np.random.default_rng(0).integers(0, 3, 400))
    tof = TOF(cutoff_n=6).fit(X)
    assert (tof.neighbourhood_size_ > 4).sum() > len(X) / 2
    assert not np.allclose(tof.outlier_score_, _k_nearest_score(tof, X))


def test_without_ties_scores_equal_the_k_nearest():
    X = np.random.default_rng(1).normal(size=(2000, 3))
    tof = TOF(cutoff_n=6).fit(X)
    np.testing.assert_array_equal(tof.outlier_score_, _k_nearest_score(tof, X))
    assert (tof.neighbourhood_size_ == 4).all()


def _flat_spell(length, n_background=300, start=150, seed=2):
    # identical embedded rows far from continuous background rows
    X = np.random.default_rng(seed).normal(size=(n_background + length, 3))
    X[start : start + length] = 100.0
    return X, np.arange(start, start + length)


def test_flat_spell_neighbourhood_is_the_whole_spell():
    X, spell = _flat_spell(12)
    tof = TOF(cutoff_n=6).fit(X)
    assert (tof.neighbourhood_size_[spell] == 11).all()


@pytest.mark.parametrize("length, flagged", [(8, 8), (16, 0)])
def test_flat_spell_flags_follow_the_threshold(length, flagged):
    # cutoff 6, k = 4: the threshold is an RMS time distance of 4.64 rows; a spell of 8 rows
    # stays under it in every row, a spell of 16 in none
    X, spell = _flat_spell(length)
    tof = TOF(cutoff_n=6).fit(X)
    assert (tof.outlier_score_[spell] > tof.cutoff_).sum() == flagged


def test_sparse_counts_do_not_flag_idle_rows():
    # zeros with single spikes spread over the series: the all-zero rows form one large twin group
    x = np.zeros(2000)
    x[np.random.default_rng(3).choice(2000, 60, replace=False)] = 1.0
    X = _embed(x)
    tof = TOF(cutoff_n=6).fit(X)
    idle = ~X.any(axis=1)
    assert not (tof.outlier_score_[idle] > tof.cutoff_).any()


def test_new_data_keeps_the_k_nearest():
    rng = np.random.default_rng(4)
    X = _embed(rng.integers(0, 3, 400))
    Y = _embed(rng.integers(0, 3, 50))
    tof = TOF(cutoff_n=6).fit(X)
    distances, neighbours = cKDTree(X).query(Y, 5)
    expected = 1.0 / tof._compute_tof(neighbours[:, 1:], np.arange(len(Y)).reshape(-1, 1))
    np.testing.assert_array_equal(tof._compute_outlier_score(Y), expected)


def test_twins_without_a_kth_tie_keep_their_scores_for_fractional_q():
    # fewer than k twins: the 0.1.1 neighbours, up to the order of summation (last bit)
    X = _embed(np.random.default_rng(5).integers(0, 6, 600))
    tof = TOF(cutoff_n=6, q=0.7).fit(X)
    same = tof.neighbourhood_size_ == 4
    np.testing.assert_allclose(tof.outlier_score_[same], _k_nearest_score(tof, X)[same], rtol=1e-12, atol=0)


def test_equal_steps_on_a_decimal_grid_tie():
    # 70.2 - 70.1 and 70.3 - 70.2 differ in floating point; both are one step of 0.1
    X = np.array([70.2, 70.1, 70.3, 70.4, 70.0, 75.0, 75.5, 76.0], dtype=float).reshape(-1, 1)
    assert 70.2 - 70.1 != 70.3 - 70.2
    tof = TOF(k=1).fit(X)
    assert tof.neighbourhood_size_[0] == 2


def test_dataframe_input_with_ties():
    X = _embed(np.random.default_rng(0).integers(0, 3, 200))
    tof = TOF(cutoff_n=6).fit(pd.DataFrame(X))
    np.testing.assert_array_equal(tof.outlier_score_, TOF(cutoff_n=6).fit(X).outlier_score_)


def test_too_few_points_raise():
    with pytest.raises(ValueError, match="more than k"):
        TOF().fit(np.random.default_rng(6).normal(size=(4, 3)))
