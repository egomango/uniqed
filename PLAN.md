# TOF Follow-Up: Agile Plan v4

*Changes from v3 are marked [v4].*

## Product goal

A time-series add-on that flags events the system has never (or rarely) shown before, explains what is new about them, and hands a reviewer a short list of likely causes. Sold as a pilot to one customer with slow-sampled signals.

## Strategic facts [v4]

- License: Simplified BSD. Commercial use allowed. No permission needed.
- `uniqed` 0.0.2 on PyPI, last release Nov 2020, unmaintained. Your name is on the author line. Take it over rather than rename; it is the search result and the install channel.
- Runtime: about 4 hours per million points (exponent 1.29). First customers have signals at 1 Hz or slower: process plants, utilities, energy meters, patient monitors. Not high-rate vibration.
- Pitch: one window-length number, an applicability check that can say "not suitable," and a detector that can return zero events. Discord always finds one; LOF needs a hand-set percentage.

## Roles

- Product owner and developer: you.
- Reviewer: a domain person at the pilot customer. Until then, you, on datasets with known answers.

## Definition of Done (every story)

- Tested on data with a known answer; the number is written down.
- Runs from one command with no hand-set parameters unless the story says otherwise.
- Regression tests pass on the paper's four simulated datasets (ROC AUC within 0.02 of Table 1; anomaly lengths 2–200 per SI, not 20–200).
- Baselines (LOF, discord) tuned with the same effort as TOF. The SI hand-picked LOF thresholds per dataset; a buyer's data scientist will check.
- One public paragraph: what was tried, the number, what failed.

## Epics

### Epic A: Trustworthy defaults and a living package (Sprint 1)

**A0 [v4].** As a user, I want `pip install uniqed` to work today, so that I can try it in five minutes.
- Tasks: request PyPI maintainer rights or fork; Python 3.12; current scipy; tests; CI; trusted publishing; release 0.1.0.
- DoD: clean install on a fresh machine; example script from the README runs.

**A1 [v4 rewritten].** As a user, I want the tool to pick the embedding itself, so that I never tune it.
- Tasks: delay from first zero crossing (or first minimum) of autocorrelation; dimension from intrinsic-dimension saturation on deterministic data; differential-entropy method (Gautama 2003) as fallback for stochastic data, since the dimension method failed on LIBOR (Fig. S11–S12); use the Fig. S5 hyperbola: choose window length E·τ first, then split.
- DoD: on Lorenz and Rössler, picked values match known; on the paper's ECG simulation F1 ≥ 0.90 (hand-tuned 0.83, optimum 0.94); LIBOR routes to the entropy method automatically.

**A2 [v4 extended].** As a user, I want sensible defaults for k, longest event, minimum visits, and padding, so that a first run needs one input.
- Tasks: k default 4; longest event asked once, in seconds; minimum visits default 1; padding window w = k/2 after detection (SI step 5); all printed in the report.
- DoD: four paper datasets run with defaults only, ROC AUC within 0.05 of Table 1.

**A3 [v4 new].** As a user, I want the tool to refuse data it cannot handle, so that I do not get confident nonsense.
- Tasks: applicability check per SI step 1: enough periods of the lowest frequency; stationarity test; suggest differencing or band-pass filter; return "not suitable" with the reason.
- DoD: raw LIBOR is refused, differenced LIBOR passes; a pure trend is refused; the paper's ECG passes.

### Epic B: See repeats (Sprint 2)

**B1.** As a maintenance engineer, I want a fault that happens a second time flagged too, so that the tool stays useful after month one.
- Tasks: count separate clusters of neighbour times; expose "visits" beside the unique score; threshold on minimum visits.
- DoD: on Tennessee Eastman (slow-sampled, 20 fault types) a fault appearing twice is flagged both times; unique score still finds the Fig. 2D linear event.
- Kill: visits score does not beat plain kNN density. Ship unique-only.

### Epic C: Many sensors (Sprint 3)

**C1.** As a plant operator, I want all my sensors in at once, so that I see plant-level events.
- Tasks: per-channel scaling and embedding; concatenate; test 3, 10, 52 channels; record where kNN stops helping.
- DoD: on Tennessee Eastman, 3-channel beats best single channel on event-level recall; channel limit documented; report names first channel to move.

### Epic D: Live (Sprint 4)

**D1 [v4 extended].** As an operator, I want flags while the plant runs.
- Tasks: sliding window capped at about 10⁵ points (4 hours per 10⁶ is too slow); kd-tree rebuilt per window; forgetting rule; one-sided baseline from SI Eq. 4–7 integrated over [0, t] only; measure lag.
- DoD: live on a Numenta stream; measured one-sided baseline matches derivation; lag stated as "flagged N samples after onset"; window rebuild under 10 s.

### Epic E: Say what is new (Sprint 5)

**E1.** As a reviewer, I want a one-page fact sheet per flag.
- Tasks: feature deltas vs k nearest past segments (amplitude, frequency, slope, duration); trajectory view (states before and after, dwell time, first channel to move); plain-English template; no LLM.
- DoD: on 30 hand-checked UCR cases the sheet names the true difference in at least half (record the real rate); non-empty for the Fig. 2D event.

### Epic F: Say why (Sprint 6, on pilot data)

**F1.** Join the flag window to one external table. Rehearse on SWaT. DoD: every SWaT attack returns its log entry.

**F2.** LLM returns three ranked hypotheses citing facts, a severity, one action. Hypotheses only. DoD: on 20 SWaT attacks, true cause in top three ≥ 60%; every citation exists in the sheet.

**F3.** Confirmed events go into a library; recurrences are named with their past fix. DoD: a replayed confirmed event matches itself.

### Epic G: Pilot (all sprints)

**G1.** Five asks a week from week 1; free first pilot; call before data; reviewer hours committed up front. Target customers with 1 Hz or slower signals [v4]. DoD: one data dump, one named reviewer.

## Sprint calendar

| Sprint | Epic | Gate |
|---|---|---|
| 1 | A | Package installs; defaults reproduce the paper; LIBOR routed correctly |
| 2 | B | Repeats flagged on TEP |
| 3 | C | Multi-channel beats single on TEP |
| 4 | D | Live on Numenta, one-sided baseline verified |
| 5 | E | Fact sheet non-empty on Fig. 2D |
| 6 (4 wks) | F | Pilot running |
| all | G | 5 asks a week |

## Pilot metrics [v4]

- Events caught (block recall), not points caught. Gravity Spy: precision 1.0, point recall low, block recall 0.9. Point-level F1 will look bad and mislead.
- Flag-to-decision time.
- Share of hypothesis lists accepted unedited.
- Head-to-head against "do nothing" and "ask the LLM," with baselines tuned equally.

## Not doing

- Agent-run monitoring until a task-independent state exists.
- Probability scores (paper only).
- High-rate vibration as first market [v4].
- Event data, activation monitoring, RL exploration, SaaS.

## Known limits, stated in the pitch

- Events shorter than k samples are invisible; pair with LOF.
- Lag of at least k samples into the event.
- The score at time t uses (E−1)·τ/2 future samples (one for E=3, τ=1), so a live detector cannot score t until they arrive; see egomango/uniqed#1 for the half-sample truncation when (E−1)·τ is odd.
- TOF marks part of an event, not all of it.
- One window-length number plus longest event and minimum visits.
- Slow signals only, until runtime improves.
