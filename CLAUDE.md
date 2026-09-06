# uniqed — working rules for Claude Code

## Current sprint: Sprint 1, story A1 (automatic embedding)

A0 closed 2026-09-03 with 0.0.3 on PyPI; see `docs/log.md`.

Goal: the tool picks the embedding itself, so the user never tunes it. Behaviour
changes ship as 0.1.0, not as a 0.0.x release.

## Do

- Delay τ from the first zero crossing of the autocorrelation, or the first minimum if it never reaches zero.
- Dimension E from intrinsic-dimension saturation on deterministic data; differential-entropy method
  (Gautama 2003) as fallback for stochastic data, since the dimension method failed on LIBOR (Fig. S11–S12).
- Choose window length E·τ first, then split (Fig. S5 hyperbola).
- Implement the Ryzhii ECG generator from SI Eq. 14–25 and un-skip the sim-ECG-tachy regression row (0.931).
- Fix issue #1 (half-sample truncation when (E−1)·τ is odd) here.
- Definition of done: on Lorenz and Rössler the picked values match the known ones; on the paper's ECG
  simulation F1 ≥ 0.90 (hand-tuned 0.83, optimum 0.94); TEDRATE routes to the entropy method automatically.
- TEDRATE stands in for LIBOR. USD LIBOR was removed from FRED on 2022-01-31 and has no free source; the
  repo holds no copy. TEDRATE (FRED series `TEDRATE`, 3-month LIBOR minus 3-month T-bill, daily,
  1986-01-02 to 2022-01-21, 9,407 observations, no gaps) is the stochastic test series instead. Fetch it
  from `https://fred.stlouisfed.org/graph/fredgraph.csv?id=TEDRATE` at test time, do not vendor it, skip
  the test when offline. The paper's Fig. S11–S12 LIBOR result is cited, not reproduced.
- Keep the A0 regression tests passing with explicit E=3, τ=1. Keep the README example running.

## Do not

- Do not change the TOF score computation or the kNN search.
- Do not rename the package, modules, or public functions. Existing calls with explicit
  `embedding_dimension` and `embedding_delay` must keep working and give the same output.
- Do not start A2 (defaults for k, longest event, minimum visits, padding) or A3 (applicability check) here.
- Do not delete or re-upload existing PyPI releases 0.0.0–0.0.3.
- Do not add report, context-join, or hypothesis code to this repo. Epics E and F live in a separate private repo. See the plan there, "Three tracks".

## Before every commit

- Run the test suite.
- Show me the diff and wait.

## Reference

- Plan: `~/io/uniqed-report/PLAN.md`, private and local-only, moved out of this repo 2026-09-06. Nothing about pricing, outreach, or customers belongs in this public repo.
- Paper: Benkő, Bábel, Somogyvári, Sci. Rep. 12:227 (2022), doi 10.1038/s41598-021-03526-y.

## Publishing workflow (fixed, must match PyPI Trusted Publisher)

- File: `.github/workflows/publish.yml` — this exact path and name.
- Trigger: on push of a tag matching `v*`.
- Publish job: `environment: pypi`, `permissions: id-token: write`, no API token, no secrets.
- Use `pypa/gh-action-pypi-publish` for the upload.
- Build with `python -m build`; run the test suite before the publish job.

## Decisions already made (do not reopen)

Carried over from the planning chat of 2026-09-03 when HANDOVER.md was retired.
Sprint state and history live in `docs/log.md` and the git log.

- Same algorithm, same outputs through 0.0.3 (released 2026-09-03). Behaviour changes start at 0.1.0.
- Package name stays `uniqed`. No rename. Existing PyPI releases 0.0.0–0.0.2 are never deleted or re-uploaded.
- Anomaly lengths in simulated datasets are 20–200 (what Table 1 was computed on), not 2–200 as the SI text says.
- Regression tolerance is a hard 0.02 on the mean; do not widen it to the paper's SD.
- Published CSVs are fetched via git-lfs in CI, not vendored.
- The simulated ECG (Ryzhii) generator is not in the repo. Implement it in A1 from SI Eq. 14–25; needed for the E=7, τ=6 check.
- Embedding is forward-looking; the score at t uses (E−1)·τ/2 future samples, with half-sample truncation when that is odd (issue #1). Documented, not changed. Fix in A1, not before.
- PyPI: Trusted Publisher registered for `egomango/uniqed`, workflow `publish.yml`, environment `pypi`, required reviewer set.
- One public paragraph per finished story goes in `docs/log.md`: what was tried, the number, what failed.
- If a decision above looks wrong, say so with the evidence and stop; do not silently override it.
