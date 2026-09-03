# Changelog

## 0.0.3 — 2026-09-03

Maintained again. Packaging only; no behaviour change.

- Installs on Python 3.12 with current numpy, scipy, scikit-learn, pandas and matplotlib. No source change was needed.
- Regression tests against Table 1 of the paper: three simulated datasets regenerated over 100 seeds, and the 300 published CSVs (slow, via git-lfs).
- GitHub Actions: tests on push; release to PyPI on `v*` tags via Trusted Publishing.
- Project URLs point at the maintained fork, `egomango/uniqed`.
- The TOF score, the embedding and the kNN search are unchanged from 0.0.2.

## 0.0.2 — 2020-11

Last release by the original authors.
