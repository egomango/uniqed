# Changelog

## 0.1.0 — 2026-09-06

The package chooses the embedding itself (story A1). First behaviour change since 0.0.2.

- New `uniqed.embedding`: `choose_embedding(x)` returns the dimension, the delay, which rule chose them and the diagnostics. Delay from the first zero crossing of the autocorrelation (first minimum if it never crosses); dimension from where the intrinsic-dimension estimate (median FSA) stops tracking the embedding dimension, with a floor of 3; the entropy-ratio criterion of Gautama, Mandic and Van Hulle (2003) as the fallback for signals with no plateau.
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
