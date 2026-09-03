# uniqed — working rules for Claude Code

## Current sprint: Sprint 1 (Epic A0 only)

Goal: same algorithm, same outputs, modern packaging. Release 0.0.3.

## Do

- Make `pip install -e .` work on Python 3.12 with current numpy, scipy, pandas.
- Fix only what breaks. Prefer the smallest change.
- Add regression tests: the four simulated datasets from the paper, ROC AUC within 0.02 of Table 1
  (logmap-tent 0.939, logmap-linear 0.994, sim-ECG-tachy 0.931, randwalk-linear 0.988).
- Add a GitHub Actions workflow: test on push; publish to PyPI via Trusted Publishing on tag.
- Keep the README example running unchanged.

## Do not

- Do not change any function that computes the TOF score, the embedding, or the kNN search.
- Do not rename the package, modules, or public functions.
- Do not add new features, parameters, or defaults. Those are Sprint 1 stories A1–A3, later.
- Do not delete or re-upload existing PyPI releases 0.0.0–0.0.2.

## Before every commit

- Run the test suite.
- Show me the diff and wait.

## Reference

- Plan: PLAN.md in this repo.
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
