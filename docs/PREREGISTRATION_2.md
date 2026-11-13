# Pre-registration, round 2: does the v8 fix transfer?

Frozen 17 Oct 2026, about 00:50 (UTC+2), before any policy was run on a round-2 scenario. A frozen copy and the manifest are timestamped with OpenTimestamps (only their SHA-256 hashes leave the machine).

## Why a second round

Round 1 (`docs/PREREGISTRATION.md`) tests the controller frozen on 16 Oct (v7, commit `ad59466`). While round 1 was running, a 30-day training scenario (building 1, Atlanta strip 2; a training scenario, never part of any held-out set) showed a failure the 10-day development set had not shown: on warm days, 21 of 39 zones fell into a four-step limit cycle (for example 16 -> 23 -> 26 -> 24 -> 16 °C). Two causes were found in the per-zone traces (`sb/zone_dump.py`):

1. The safety net fired on the measured temperature, ignoring the heat already in the pipe; full cooling then overshot, the delay-aware planner pre-heated, and the cycle repeated.
2. Where the bounded zone model sat at a parameter bound, it kept predicting a drift that did not happen (for example -1 K per step), so a zone above its band was left uncooled.

v8 adds two options: the safety net fires only if the zone is still far outside its band after the heat in the pipe (`safety_pred`), and predictions add a per-zone disturbance estimate, the smoothed one-step prediction error (`dist_obs`; offset-free MPC in the sense of Muske and Badgwell 2002 and Pannocchia and Rawlings 2003). Both were designed on training scenarios only. Round 1's rule says a changed policy is run on the round-1 set too and labelled post hoc; that run follows this one. A diagnosis on one round-1 building (7003; `docs/TUNING_LOG.md`) explained v7's round-1 failure but set no parameter. Because the v8 changes were made after round-1 results of v7 were seen, round 2 gives v8 a clean test on a set nobody has looked at.

## Held-out set 2 (fixed now)

**Buildings.** Six new buildings from the official floor generator, seeds 7101-7106 (spares 7107-7115 in order if the generator's own check rejects a scaled building), scaled exactly as in round 1. Script: `sb/make_heldout.py --round 2`; hashes in `heldout2/MANIFEST.txt`. The generator rejected seeds 7101, 7107, 7108, 7109, 7110 (slot 1) and 7103 (slot 3) for zones below 20 m², so the six buildings are **7111, 7102, 7112, 7104, 7105, 7106** (7 to 13 air handlers each). Built 17 Oct 2026, about 00:30; no policy has been run on them.

**Weather.** The six Minneapolis strips no run has used (minneapolis_2, 3, 4, 6, 7, 8; Minneapolis is in no training scenario), and six training-period strips never used for development: atlanta_5, denver_3, fairbanks_4, phoenix_1, singapore_3, fairbanks_7. (Every non-Minneapolis strip is now used either by training or by round 1, so fully unseen weather is only possible for Minneapolis.)

| building | strip 1 | strip 2 |
|---|---|---|
| 7111 | minneapolis_2 | atlanta_5 |
| 7102 | minneapolis_3 | denver_3 |
| 7112 | minneapolis_4 | fairbanks_4 |
| 7104 | minneapolis_6 | phoenix_1 |
| 7105 | minneapolis_7 | singapore_3 |
| 7106 | minneapolis_8 | fairbanks_7 |

Full 30-day episodes, runner `sb/run.py`, as in round 1.

## Policies

1. v8: `policies/zonal.py` at the commit recorded in `RUN_INFO.json` (exported to a file before the run) with parameters `{"safety_pred": 2, "dist_obs": 1}` (`docs/preregistration2/V8_PARAMS.json`); every other parameter at its default. Chosen as the best development-set score among the variants finished at freezing time (`docs/TUNING_LOG.md`): v7 0.02305, v8a 0.01962, disturbance estimate only 0.01940, v8a with smoothing 0.05 0.01961, **v8b (cooling-only net fix + disturbance estimate) 0.01893**. Runs still going at freezing time (smoothing 0.2; v8 without delay compensation) are reported as sensitivity checks and cannot change the choice.
2. v7: the round-1 frozen file (`ad59466`, SHA-256 `ed09634e...`).
3. The four official baselines.

## Hypotheses and pass marks

On the development set v8b beat v7 by 18 % and in 6 of 6 scenarios; on one round-1 building with 17 air handlers, by 85 % over 4 days. Round-2 buildings have 7 to 13 air handlers. The marks below are set to be clearly passable only if the fix transfers.

- **R2-H1 (the fix helps).** v8's score is at least 20 % lower than v7's on the 12 round-2 scenarios.
- **R2-H2 (it helps broadly).** v8 is better than v7 in at least 10 of 12 scenarios.
- **R2-H3 (versus the baselines).** v8's score is at least 30 % lower than the best baseline's (round 1's H1 mark).
- **R2-H4 (comfort).** v8's total comfort regret is at most v7's.

Each is reported as passed or failed whatever the outcome.

## Rules

- Run once, in this order: v8, v7, then the baselines (`sb/heldout2.sh`), at most five simulations at a time on this machine (round 1, deviation 2).
- Scored by `sb/evaluate_round2.py` into `docs/RESULTS_ROUND2.md`, whatever the outcome.
- Crashes are reported, fixed and labelled, as in round 1.
- After round 2, v8 is also run on the round-1 set and reported as post hoc.
