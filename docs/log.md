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

## A1 — the tool picks the embedding (0.1.0, 2026-09-06)

Goal: no hand-set embedding. We implemented the three-step procedure the paper's
supplement describes for its real datasets (Figs. S9–S12): delay from the first turning
point of the autocorrelation (zero crossing or first minimum, whichever comes first, as
the paper's two examples did), dimension from where the median-FSA intrinsic-dimension
estimate stops tracking the embedding dimension, and Gautama's entropy ratio when there
is no plateau. On Lorenz and Rössler it picks E=3; on the differenced TEDRATE series
(the stand-in for LIBOR) it finds no plateau and routes to the entropy method, as the
paper did for LIBOR. The authors' 100 simulated ECG files turned out to be in the repo,
so the Table 1 row (AUC 0.931) is now a regression test and no ECG generator was
written; the supplement also omits the model's coupling delays, so one could not have
been verified anyway. What failed: the paper's own procedure does not reach the paper's
best ECG setting. First deviation gives E=2 and mean F1 0.78 over 15 files; the
hand-set E=3, τ=1 gives 0.82; the Fig. S5 optimum E=7, τ=6 came from a labelled grid
search and gives 0.94. A floor of E=3, which the paper never went below, gives 0.86,
and that is the number we ship. Three more things learned: rounded values (TEDRATE is
quoted to two decimals) collapse both estimators through exact ties, so the router now
dithers by half the resolution; the entropy-ratio criterion pins the delay on a noisy
Hénon map at every noise level from 10% up but its dimension drifts to the top of the
grid at these sample sizes; an exactly periodic sampled signal defeats both
estimators; and below a few hundred embedded rows white noise can show a false plateau
at the top of the grid (1 of 25 seeds at 300 rows, none from 400 up), so the chooser
requires 500 rows, caps the delay search to what the series can support, and on series
too short or with too few cycles raises with advice rather than guess. Also fixed:
issue #1, odd embedding windows now round toward the past. Explicit E=3, τ=1 gives
output identical to 0.0.3, checked frame for frame. Found by CI after the tag: the
first cut took the zero crossing whenever one existed, which on Lorenz lands at 200–400
samples, several oscillations, where the reconstruction is poor and the rule returned
E=4; the first minimum at 50–70 gives E=3 on every seed. The test data had also been
integrated with an adaptive solver, and chaos turned the last-bit differences between
macOS and Linux into different trajectories; the tests now use fixed-step RK4 in plain
arithmetic, bit-identical across platforms.
