# uniqed — working rules for Claude Code

## Current sprint: Sprint 1, story A2 (defaults for k, longest event, minimum visits, padding)

A0 closed 2026-09-03 with 0.0.3; A1 closed 2026-09-06 with 0.1.0. See `docs/log.md`.
The plan for A2 is in `~/io/uniqed-report/PLAN.md`; write the story's rules here before starting it.

## Do

- Keep the A0 regression tests passing with explicit E=3, τ=1. Keep the README example running.
- Keep `choose_embedding` reproducing the paper's procedure; a change to its rules needs the
  numbers in `docs/log.md` (A1) re-measured and written down.

## Do not

- Do not change the TOF score computation or the kNN search.
- Do not rename the package, modules, or public functions. Existing calls with explicit
  `embedding_dimension` and `embedding_delay` must keep working and give the same output.
- Do not delete or re-upload existing PyPI releases 0.0.0–0.1.0.
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

Carried over from the planning chat of 2026-09-03 when HANDOVER.md was retired, and the A1 session of 2026-09-06.
Sprint state and history live in `docs/log.md` and the git log.

- Same algorithm, same outputs through 0.0.3 (released 2026-09-03). Behaviour changes start at 0.1.0.
- Package name stays `uniqed`. No rename. Existing PyPI releases are never deleted or re-uploaded.
- Anomaly lengths in simulated datasets are 20–200 (what Table 1 was computed on), not 2–200 as the SI text says.
- Regression tolerance is a hard 0.02 on the mean; do not widen it to the paper's SD.
- Published CSVs are fetched via git-lfs in CI, not vendored.
- The simulated ECG is tested on the authors' published files (`examples/data/simulations/sim_ecg`, git LFS).
  No generator: decided 2026-09-06 because the files reproduce Table 1 and Fig. S5 C, and the SI omits the
  Ryzhii model's coupling delays.
- Embedding is forward-looking; the score at t uses future samples. Odd windows round toward the past;
  live lag is ceil((E−1)·τ/2). Issue #1, fixed in 0.1.0.
- `choose_embedding` reproduces the paper's procedure (SI Figs. S9–S12) with a dimension floor of 3. Its
  ECG definition of done is "beats the paper's hand-set 0.82", measured 0.86; the Fig. S5 optimum 0.94 is a
  labelled grid-search result no label-free rule reaches. Decided 2026-09-06.
- TEDRATE stands in for LIBOR. USD LIBOR was removed from FRED on 2022-01-31 and has no free source; the
  repo holds no copy. TEDRATE (FRED series `TEDRATE`, 3-month LIBOR minus 3-month T-bill, daily,
  1986-01-02 to 2022-01-21, 9,407 rows of which 554 are empty, 8,853 numeric) is the stochastic test
  series. Fetched from `https://fred.stlouisfed.org/graph/fredgraph.csv?id=TEDRATE` at test time, not
  vendored, skipped offline. The paper's Fig. S11–S12 LIBOR result is cited, not reproduced.
- PyPI: Trusted Publisher registered for `egomango/uniqed`, workflow `publish.yml`, environment `pypi`, required reviewer set.
- One public paragraph per finished story goes in `docs/log.md`: what was tried, the number, what failed.
- If a decision above looks wrong, say so with the evidence and stop; do not silently override it.
