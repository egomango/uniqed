# HANDOVER — state and decisions as of 2026-09-03

Read this after CLAUDE.md and before PLAN.md. It records what was decided in the planning chat so it is not re-litigated.

## Where we are

- Sprint 1, Epic A0 (package alive). Nearly done.
- Install works on Python 3.12 with current numpy/scipy/pandas. No algorithm change was needed.
- Regression tests exist: fast (100 seeds, 3 datasets, ±0.02 of Table 1) and slow (300 published CSVs, ±0.005).
- CI: `test.yml` on push; `publish.yml` on `v*` tags via Trusted Publishing, environment `pypi`, required reviewer set.
- PyPI: owner rights obtained; Trusted Publisher registered for `<owner>/uniqed`, `publish.yml`, env `pypi`.
- Open issue #1: half-sample truncation when (E−1)·τ is odd. Fix in A1, not before.

## Remaining A0 tasks

1. Commit current work (include CLAUDE.md).
2. Update `setup.py` URL and `project_urls` to point at this fork; add Source and Issues links.
3. Bump version to 0.0.3, add CHANGELOG.md ("maintained again; packaging only; no behaviour change").
4. Tag `v0.0.3`, approve the environment gate, confirm the PyPI page updates.
5. Then, and only then, start A1.

## Decisions already made (do not reopen)

- Same algorithm, same outputs through 0.0.3. Behaviour changes start at 0.1.0.
- Package name stays `uniqed`. No rename.
- Existing PyPI releases 0.0.0–0.0.2 are never deleted or re-uploaded.
- Anomaly lengths in simulated datasets are 20–200 (what Table 1 was computed on), not 2–200 as the SI text says.
- Regression tolerance is a hard 0.02 on the mean; do not widen it to the paper's SD.
- Published CSVs are fetched via git-lfs in CI, not vendored.
- The simulated ECG (Ryzhii) generator is not in the repo. Implement it in A1 from SI Eq. 14–25; needed for the E=7, τ=6 check.
- Embedding is forward-looking; score at t uses (E−1)·τ/2 future samples. Documented, not changed.

## Strategy constraints (from PLAN.md, repeated because they shape technical choices)

- First customers have signals at 1 Hz or slower. Runtime is ~4 h per 10⁶ points; do not optimise for high-rate data yet.
- Streaming (Epic D) needs a window cap near 10⁵ points and a one-sided baseline derived from SI Eq. 4–7 over [0, t].
- Pilot metric is event-level recall (block recall), not point-level F1.
- Baselines (LOF, discord) must be tuned with the same effort as TOF in any comparison.
- Not doing: agent-trace monitoring, probability scores, high-rate vibration, SaaS.

## Next sprint stories, in order

- A1: automatic embedding (autocorrelation → delay; intrinsic-dimension saturation → dimension; differential entropy fallback for stochastic data; window-length E·τ chosen first). Fix issue #1 here. Implement Ryzhii ECG generator here.
- A2: defaults for k=4, longest event (asked once, seconds), minimum visits=1, padding w=k/2.
- A3: applicability check (enough periods of lowest frequency; stationarity; refuse with reason).

## Working rules

- Show the diff and wait before every commit.
- One public paragraph per finished story goes in `docs/log.md`: what was tried, the number, what failed.
- If a decision above looks wrong, say so with the evidence and stop; do not silently override it.
