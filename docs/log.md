# Log

One public paragraph per finished story: what was tried, the number, what failed.

## A0 — package alive (0.0.3, 2026-09-03)

Goal: `pip install uniqed` works today, same algorithm, same outputs. The 2020 code
installed and ran unchanged on Python 3.12 with numpy 2.5, scipy 1.18, pandas 3.0 and
scikit-learn 1.9; no source change was needed. To pin "same outputs" we added two
regression tests against Table 1 of the paper (E=3, τ=1, k=2/6/30). The authors' 300
published simulation files, fetched via git-lfs, give mean ROC AUC 0.939 / 0.994 / 0.987
against the published 0.939 / 0.994 / 0.988, asserted within 0.005. Datasets regenerated
from the SI recipe over 100 seeds give 0.944 / 0.995 / 0.983, asserted within 0.02.
Anomaly lengths follow the published files (20–200), not the SI text (2–200). What
failed or was left out: the simulated ECG row (0.931) has no generator in the repo, so
it is skipped until A1; the first build produced a 31 MB sdist because the manifest
grafted the LFS data and local PDFs, fixed by pruning (154 KB); and the embedding turned
out to use (E−1)·τ/2 future samples with a half-sample truncation when that is odd,
filed as issue #1 and documented rather than changed. Released 0.0.3 through GitHub
Actions with PyPI Trusted Publishing; a fresh venv install from PyPI runs the README
example unchanged.
