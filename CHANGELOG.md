# Changelog

## 0.1.2 — 2026-10-21

On the fitted data, a point's neighbours are every point at the k-th nearest distance or closer, ties included (story A-ties). Scores no longer depend on the order in which the search returns tied points. Changes output only where an embedded point has a tie at its k-th neighbour distance.

- Up to 0.1.1 exactly k neighbours were kept, and among points tied at the k-th distance the search's order chose which counted. On data with many identical values (meters that round, event counts) that order decided which points were flagged: tied points came back in time order, looked close in time, and were flagged. The neighbourhood now includes every tied point (the k-distance neighbourhood of LOF, Breunig et al. 2000), so one run gives one answer.
- The threshold keeps its meaning: every point of a unique event up to `cutoff_n` samples long is still flagged. A stretch of identical values longer than that is flagged only in part or not at all, because its neighbours spread over the whole stretch.
- Values are not rounded. Identical points are found by exact equality. Distances count as tied when they agree within a relative 1e-12: on a decimal grid, equal steps such as 70.2 − 70.1 and 70.3 − 70.2 differ in the last bits of floating point, and would otherwise not tie.
- New attribute `neighbourhood_size_`: the number of neighbours per point, larger than k where ties enlarged it.
- Output elsewhere is identical to 0.1.1 for whole-number q (the default is 2): checked on all 400 published simulation files at E=3, τ=1, k = 2 and 4. For fractional q the neighbours are the same but summed in a different order, so scores can differ in the last bit.
- Fitting fewer than k + 1 points now raises `ValueError`; before it returned scores computed from a missing neighbour.
- With q other than 2 or a centrality other than the mean, a large group of identical points is scored pair by pair: memory stays bounded, but time grows with the group size squared.
- Applies when scoring the fitted data (`fit`, and `predict` on the same array). `predict` on other data keeps the k nearest.
- Dithering is no longer needed to remove the tie order. It remains a choice about how far to trust the last digit of the data: noise as large as the rounding step also blurs neighbouring distinct values.

## 0.1.1 — 2026-10-21

A point never counts as its own neighbour (story A-bug). Changes output only on data with exact twin points after embedding.

- The neighbour search asked for k + 1 results and dropped the first, assuming it was the point itself. With exact twins the search may return a twin first, and the point could stay among its own k neighbours at time distance 0. On a sparse count series with many identical idle points this happened in 4.6% of rows. The point is now dropped by its index; when more than k twins push it out of the results, the last result is dropped.
- Applies when scoring the fitted data (`fit`, and `predict` on the same array). `predict` on other data keeps the old behaviour.
- Output on data without exact twins is identical to 0.1.0: checked on all 400 published simulation files at E=3, τ=1, k = 2 and 4.
- Which twins become neighbours still depends on the search's tie order. Data with many identical values should be dithered before scoring.
  Correction (2026-10-21): one dither seed is not enough. It replaces the search's tie order with the noise's, and the flags move with the seed. Score several noise seeds and report how often each flag appears.

## 0.1.0 — 2026-09-06

The package chooses the embedding itself (story A1). First behaviour change since 0.0.2.

- New `uniqed.embedding`: `choose_embedding(x)` returns the dimension, the delay, which rule chose them and the diagnostics. Delay from the first turning point of the autocorrelation, its zero crossing or its first minimum, whichever comes first (the paper's two examples did one each); dimension from where the intrinsic-dimension estimate (median FSA) stops tracking the embedding dimension, with a floor of 3; the entropy-ratio criterion of Gautama, Mandic and Van Hulle (2003) as the fallback for signals with no plateau.
- `detect_outlier` defaults `embedding_dimension` and `embedding_delay` to `None`, meaning "choose". Either may still be given. The result carries `result.attrs["embedding"]`.
- Explicit `embedding_dimension=3, embedding_delay=1` gives output identical to 0.0.3, checked frame for frame.
- Quantised input (meters, rates quoted to two decimals) is dithered by half its resolution before the estimators run, and the choice records it.
- Odd embedding windows are stamped at the ceiling of half the window instead of being truncated toward zero (issue #1). Live lag is `ceil((E-1)*tau/2)`.
- The simulated-ECG row of Table 1 (AUC 0.931) is now a regression test on the authors' published files. No generator was added.
- The chooser needs 500 embedded rows at the largest dimension it tries (below that, white noise can show a false plateau) and a delay it can support. Shorter series, series whose autocorrelation never turns within that range (too few cycles), and series whose values repeat exactly (an exactly periodic sampled signal) make `choose_embedding` raise a `ValueError` that says to pass the embedding explicitly. Calls that relied on the old silent default of E=3, τ=1 on such series must now pass it.
- Known limit: the entropy-ratio fallback pins the delay well but its dimension drifts to the top of the grid at these sample sizes.

## 0.0.3 — 2026-09-03

Maintained again. Packaging only; no behaviour change.

- Installs on Python 3.12 with current numpy, scipy, scikit-learn, pandas and matplotlib. No source change was needed.
- Regression tests against Table 1 of the paper: three simulated datasets regenerated over 100 seeds, and the 300 published CSVs (slow, via git-lfs).
- GitHub Actions: tests on push; release to PyPI on `v*` tags via Trusted Publishing.
- Project URLs point at the maintained fork, `egomango/uniqed`.
- The TOF score, the embedding and the kNN search are unchanged from 0.0.2.

## 0.0.2 — 2020-11

Last release by the original authors.
