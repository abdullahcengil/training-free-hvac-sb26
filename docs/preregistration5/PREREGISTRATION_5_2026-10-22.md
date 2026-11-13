# Pre-registration, round 5: does the mass-model controller (v11) transfer?

Frozen 22 Oct 2026, about 21:15 (UTC+2), before any policy was run on a round-5 scenario. A frozen copy and the manifest are timestamped with OpenTimestamps (only their SHA-256 hashes leave the machine).

## Why a fifth round

v10 passed four of five hypotheses in round 4 and scores 0.01092 on the 30 training scenarios at full length. v11 changes the zone model, the core of the controller, and adds three plant-level mechanisms, so it needs a new blind test.

What was found, all on training scenarios only (`docs/TUNING_LOG.md`, section v11):
1. **Zone model.** v10's model relaxes every zone towards a fixed 295 K with a bounded offset. In hot and cold weather the offset sits at its bound (25 % of the time in Fairbanks) and the model's 6-hour prediction error is 7.1 K, because the building has a floor slab about four hours behind the room air. The new model (option `mass_model`) is dT = -lam (T - Tm) + g q[k-1] + c + b (oat - T) + c_cm cm, where Tm follows the room air with a lag of 48 steps, b is an envelope term and c_cm an internal-gain term in comfort mode; five parameters per zone, identified online by recursive least squares with bounds. Offline on training traces it predicts 6 hours ahead to 0.9 K.
2. **Where the energy goes** (device-level traces of the candidate): in cold weather gas is 86-91 % of energy and carbon and the hot-water pump 7-11 %; in hot weather the chiller is 89-95 % and the fans 5-9 %. In hot weather 37-45 % of the energy fell outside occupied hours, because the unoccupied ceiling (eco band 298 K minus the 1 K guard) equalled the comfort ceiling, so the zones were held at about 23.5 °C day and night with the air handlers running 98-99 % of the time.
3. **Mechanisms**, each screened at full length on four cold (fairbanks_8, fairbanks_1, denver_2, fairbanks_2) or four warm (phoenix_4, singapore_7, atlanta_8, phoenix_5) training scenarios:
   - the mass model itself, with three parameters re-chosen on it: a heating cap of 0.45 for zones far below their band (v10's 0.2 was below the normal cap 0.245), a night glide floor of eco - 12 K (was - 7.46 K) and a cooling margin of 0.25 K (was 0.43 K);
   - **hot-water pump pressure reset** (`dp_reset` 2, as in ASHRAE Guideline 36): the lowest pump pressure at which every open reheat coil still reaches its planned discharge temperature, from the coil's water-to-air capacity ratio and the valve Kv (0.108, the same in all 90 generated scenarios), with each valve opened only as far as its coil needs; v10 ran the pump at full pressure whenever any zone was heated. Cold four: -7.8 % against the candidate without it, 4 of 4 better, comfort identical;
   - **cooling glide with the mass model's pull-down rate** (`cool_glide`, `m2_rate`; float ceiling eco + 8 K, safety 0.55): the unoccupied ceiling rises, and falls back towards the comfort target at the rate at which the zone can really be cooled. With v10's first-order model this mechanism had failed at 30 days (phoenix_5 +99 %). With the mass model: warm four -11.6 % (4 of 4), singapore_7 -18.8 %, phoenix_4 -16.4 %, phoenix_5 -10.0 %.
4. Tried and dropped at full length: precooling (+9.5 % warm), a mass-aware recovery start (+0.3 % cold), a self-learning recovery rate (mixed), holiday detection (no gain), a boiler standby setback (+3.3 % in atlanta_8), a night floor of eco - 20 K (comfort worse in fairbanks_1).

## Training check before freezing (30 training scenarios, full length)

v11 (`results/dev11_8640/v11f`, code `frozen/zonal_v11f.py` = commit aa71ade) against v10 (`results/train_8640/v10c`):
- Overall: 0.00744 against 0.01092 (-31.9 %).
- Per scenario: better in 30 of 30. Median change -34.7 %, range -58.6 % to -13.1 %.
- Warm stations (Atlanta, Phoenix, Singapore; 18 scenarios): 0.00585 against 0.00848 (-31.1 %).
- Cold stations (Denver, Fairbanks; 12 scenarios): 0.00983 against 0.01459 (-32.6 %).
- Comfort regret per step: 0.00026 against 0.00294 (-91.2 %).

Eight of the 30 (listed above) were used to screen the mechanisms and parameters; the other 22 were never used to choose anything in v11.

Bit-for-bit check: with the new options off and the v10 parameters, the v11 code gives per-step rewards identical to the v10 training runs on building_train_8 / fairbanks_8 and singapore_7 (2016 steps; `results/bitcheck11/v10params_codeG`).

Disclosure: interim Kaggle notebooks (v11a, v11b) and a notebook with exactly the v11 parameters were prepared on 22 Oct before this file was frozen, at the user's request to use the daily submissions. Their public scores, if known at the time of the freeze, are not used here, and the public leaderboard is never used to choose parameters. v11's parameters were committed (aa71ade, 22 Oct 19:04) before v10's public score (0.01543) was known (recorded 20:08) and before the public leaderboard was read (about 20:50).

## Held-out set 5 (fixed now)

**Buildings.** Six new buildings from the official floor generator, seeds 7401-7406 (spares from 7407 in order if the generator's own check rejects a scaled building), scaled as in rounds 1-4 (`sb/make_heldout.py --round 5`; hashes in `heldout5/MANIFEST.txt`; the scenario files' absolute paths were rewritten to the held-out folder, old and new hashes in `heldout5/MANIFEST_PATHFIX.txt`). The generator rejected 7404 and 7405 (zones below 20 m2), so the six buildings are **7401, 7402, 7403, 7407, 7408 and 7406**. They were built on 22 Oct 2026, 14:41-14:44 (commit d4c11d5), before this file was frozen; no policy has been run on them.

**Weather.** Twelve new 30-day windows (2023), none used in any earlier round. Each overlaps at most about ten days with a training strip of the same station; Minneapolis has no training strip.

| building | cold strip | warm strip |
|---|---|---|
| 7401 | minneapolis_jan29 | phoenix_may14 |
| 7402 | fairbanks_jan22 | singapore_may21 |
| 7403 | denver_feb05 | atlanta_jun18 |
| 7407 | minneapolis_mar12 | singapore_jan01 |
| 7408 | fairbanks_apr16 | phoenix_sep17 |
| 7406 | denver_sep03 | atlanta_sep10 |

"Cold" and "warm" are by station (Denver, Fairbanks and Minneapolis are cold), as in round 4. All episodes run the full 30 days with the runner `sb/run.py`.

## Policies

1. v11: `policies/zonal.py` at the commit recorded in `RUN_INFO.json` (exported to a file before the run), with parameters `docs/preregistration5/V11_PARAMS.json`; every other parameter at its default.
2. v10: the round-4 frozen file (`24f07c3`), with its round-4 parameters.
3. pid_water, the best official baseline, as a reference (descriptive; no hypothesis; it runs last).

## Hypotheses and pass marks

The marks are set about half-way to the training evidence above, so they are clearly passable only if v11's gains transfer to new buildings, a station never used for training (Minneapolis) and new weather windows.

- **R5-H1 (all).** v11's score on all 12 scenarios is at least 15 % lower than v10's.
- **R5-H2 (broadly).** v11 is better than v10 in at least 10 of the 12 scenarios.
- **R5-H3 (cold).** v11's score on the six cold scenarios is at least 15 % lower than v10's.
- **R5-H4 (warm).** v11's score on the six warm scenarios is at least 15 % lower than v10's.
- **R5-H5 (comfort).** v11's total comfort regret over all 12 scenarios is at most 0.55 times v10's.

Each hypothesis is reported as passed or failed, whatever the outcome.

## Rules

- **Order.** Run once: v11, then v10, then pid_water (`sb/heldout5.sh`), with at most four simulations at a time.
- **Scoring.** `sb/evaluate_round5.py` (pass marks copied from this file) writes the scores into `docs/RESULTS_ROUND5.md`, whatever the outcome.
- **Crashes.** Crashes are reported, fixed and labelled, as in rounds 1-4.
- **Kaggle.** The public leaderboard is never used to choose parameters.
