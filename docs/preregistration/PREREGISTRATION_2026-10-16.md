# Pre-registration: held-out evaluation of the zonal controller

Written 16 Oct 2026, before any held-out scenario was simulated. A frozen copy of this file is timestamped with OpenTimestamps (only its SHA-256 hash leaves the machine). Everything below is fixed; anything decided later is labelled post hoc wherever it is reported.

## Why

The competition scores policies on buildings and weather they have never seen. A controller tuned on the 30 shipped training scenarios can look good there and fail elsewhere. So all development uses the training scenarios only, and the claims of the paper are tested once, on a held-out set built here from the official generator.

## Held-out set (fixed now)

**Buildings.** Six buildings from the official floor generator (`run_floor_generator`), seeds 7001, 7002, 7003, 7004, 7005, 7006, default options (composite shape, materials block). The generator's default footprints are larger than the shipped six (its README says so), and the test buildings are said to come from "the same generator and parameter ranges as the shipped six". So each building's `width`, `height`, `min_room_size` and `max_room_size` are multiplied by one factor `s = min(1, 430/width, 301/height)` (430 and 301 are the largest shipped width and height), rounded to integers. Nothing else is changed. If a scaled building fails the generator's own check (zones below 20 m², which the generator says diverge in simulation and must be fixed by changing the seed), its slot takes the next spare seed, 7007, 7008, … in order. This happened for seeds 7004, 7005 and 7006, so the six buildings are **7001, 7002, 7003, 7007, 7008, 7009**. The scaled files are in `heldout/buildings/`; their SHA-256 hashes, the rejections and the hashes of the 12 scenario configs are in `heldout/MANIFEST.txt`. Script: `sb/make_heldout.py`.

**Weather.** The 10 strips of the five training stations that no training scenario uses (atlanta_4, atlanta_7, denver_1, denver_4, fairbanks_3, fairbanks_6, phoenix_2, phoenix_7, singapore_2, singapore_5), plus minneapolis, a station that ships with the kit but appears in no training scenario.

**Pairing (12 scenarios, each station twice, each held-out strip once):**

| building | strip 1 | strip 2 |
|---|---|---|
| 7001 | atlanta_4 | phoenix_2 |
| 7002 | denver_1 | singapore_2 |
| 7003 | fairbanks_3 | minneapolis_1 |
| 7007 | atlanta_7 | phoenix_7 |
| 7008 | denver_4 | singapore_5 |
| 7009 | fairbanks_6 | minneapolis_5 |

**Episodes.** Full 30-day episodes (8,640 steps), as on the leaderboard.

**Runner.** `sb/run.py`, which steps the environment directly. (The starter kit's `SimulationTracker` advances the occupants' random chains when it logs occupancy, so its returns differ from the Kaggle gateway; reported on the competition forum.)

## Policies compared

1. The zonal controller (`policies/zonal.py`), frozen at the git commit recorded in the results file before the run.
2. The four official reference baselines: `bang_bang`, `fixed_setpoint`, `pid`, `pid_water`, unchanged.

## Metric

The leaderboard metric: for each scenario the mean per-step reward; the score is the mean of its absolute value over scenarios. Lower is better. Per-scenario values and the three reward terms (comfort regret, energy cost, carbon) are reported for every policy.

## Hypotheses and pass criteria

- **H1 (main).** The zonal controller's score on the 12 held-out scenarios is at least 30 % lower than the score of the best of the four baselines on the same 12 scenarios.
- **H2 (robustness).** In at least 10 of the 12 scenarios the zonal controller's mean per-step reward is better than that of every baseline in that scenario.
- **H3 (comfort).** The zonal controller's total comfort regret (sum of the normalised productivity regret over all 12 scenarios) is at most 10 % of `pid_water`'s.
- **H4 (transfer gap, descriptive).** Report the ratio of the zonal controller's score to the best baseline's score on the training scenarios and on the held-out scenarios. No pass mark.

Each hypothesis is reported as passed or failed, whatever the outcome.

## Rules

- The held-out set is run once with the frozen policy. If the policy changes afterwards, the new version is run on the same set, both results are reported, and the later one is labelled post hoc.
- No parameter of the controller is chosen by looking at held-out results.
- The Kaggle public leaderboard is an outside check, not part of this protocol; it is reported separately.
- If a held-out run crashes, the crash is reported and fixed, and the fix and the rerun are labelled.
