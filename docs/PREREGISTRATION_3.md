# Pre-registration, round 3: does the cold-climate change (v9) transfer?

Frozen 18 Oct 2026, about 04:20 (UTC+2), before any policy was run on a round-3 scenario. A frozen copy and the manifest are timestamped with OpenTimestamps (only their SHA-256 hashes leave the machine).

## Why a third round

v8 passed round 2. On the 30 training scenarios at full length it scores 0.0125, but the six Fairbanks scenarios carry 39 % of that loss, and the first Kaggle public score (0.01687, 17 Oct) is in line with that spread. Traces of the worst training scenario showed the loss is mostly gas, not comfort, and that zones were heated to 17 °C all night and all weekend although the reward counts comfort only where people are.

v9 adds one option, `night_glide`. Until comfort time, a zone's heating floor drops to 11 °C. It is never lower than the temperature from which the zone can still reach its comfort target in time, at the heating rate its own identified model predicts at the recovery airflow cap, times 0.7. While unoccupied, the heating airflow cap is 0.3 of the box maximum instead of 0.2. Recovery costs no comfort, and with the simulator's 35 °C discharge cap and 30 % minimum outside air, the gas per kW delivered does not depend on airflow. This is the textbook energy-optimal start (let the zone float, then recover at full rate just in time), done per zone with the online model. The glide acts only in the heating season, while the 24-hour mean outside temperature is below 18.3 °C (the standard heating degree-day base), so in hot weather v9 does exactly what v8 does. The cooling side and everything else are as in v8.

v9 was designed on training scenarios only (`docs/TUNING_LOG.md`, section v9). Four screens on 12-day episodes were run; every variant is listed there. On the union of the cold and mixed screens (10 training scenarios), v9 is 7.9 % below v8 and better in 9 of 10. A higher daytime heating cap was tried and dropped because it made mild climates worse.

Training check before freezing: v9 on all 30 training scenarios at full length (`results/train_8640/v9f`), against v8's runs.
- Overall: 0.01199 against 0.01252 (-4.2 %).
- Per scenario: better in 15, identical in 13 (every Singapore and Phoenix summer strip, where the gate keeps the glide off), worse in 2. The two worse ones are phoenix_8 (+0.3 %) and building_train_8/denver_6 (August, +14.1 %).
- On the six Fairbanks scenarios: -6.5 %, better in 6 of 6.
- Comfort regret per step: 0.00195 against 0.00177, so about 10 % more comfort loss.

Two earlier candidates were stopped during this check, and both are in the log. One had a higher daytime heating cap, which made mild climates worse. The other had no heating-season gate, which made a Phoenix summer strip worse.

## Held-out set 3 (fixed now)

**Buildings.** Six new buildings from the official floor generator, seeds 7201-7206 (spares 7207-7215 in order if the generator's own check rejects a scaled building), scaled exactly as in rounds 1 and 2 (`sb/make_heldout.py --round 3`; hashes in `heldout3/MANIFEST.txt`). The generator rejected 7201, 7207 (slot 1), 7202 and 7209 (slot 2) for zones below 20 m². The six buildings are therefore **7208, 7210, 7203, 7204, 7205 and 7206**, with 4 to 6 air handlers each. They were built on 18 Oct 2026, before this file was frozen; no policy has been run on them.

**Weather.** Every shipped strip has been used by some run, so the cold strips are new 30-day windows, starting 1 December 2023 06:00:
- Fairbanks: mean December temperature -19.7 °C.
- Minneapolis: mean -4.8 °C.
- Denver: mean 0.3 °C.

No shipped strip covers December at Fairbanks or Minneapolis. At Denver, `denver_8` ends on 5 December, so 4 of the 30 days overlap. The strip files are `heldout3/weather/*_dec.yaml`. The warm strips are shipped strips, already seen in training with other buildings: phoenix_5 and phoenix_8, singapore_6 and singapore_1, atlanta_6 and atlanta_3.

| building | cold strip | warm strip |
|---|---|---|
| 7208 | fairbanks_dec | phoenix_5 |
| 7210 | minneapolis_dec | singapore_6 |
| 7203 | denver_dec | atlanta_6 |
| 7204 | fairbanks_dec | phoenix_8 |
| 7205 | minneapolis_dec | singapore_1 |
| 7206 | denver_dec | atlanta_3 |

All episodes run the full 30 days with the runner `sb/run.py`.

## Policies

1. v9: `policies/zonal.py` at the commit recorded in `RUN_INFO.json` (exported to a file before the run), with parameters `docs/preregistration3/V9_PARAMS.json` = `{"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.3, "glide_oat": 291.45}`; every other parameter at its default. At the v8 parameters the v9 code gives bit-for-bit the frozen v8 result (`docs/TUNING_LOG.md`).
2. v8: the round-2 frozen file (`e8dbcd3`), with its round-2 parameters.
3. pid_water, the best official baseline in rounds 1 and 2, as a reference (descriptive; no hypothesis).

## Hypotheses and pass marks

Development evidence for the marks below:
- On the six Fairbanks training scenarios (12 days), v9 is 7.3 % below v8 and better in 5 of 6.
- On the 10-scenario union it is 7.9 % below v8 and better in 9 of 10.
- Comfort regret is about 19 % higher than v8's on the union, and about 10 % higher on the 30 full-length training scenarios.

The marks are set so that they are clearly passable only if the change transfers to new buildings and new cold weather.

- **R3-H1 (cold).** v9's score on the six cold scenarios is at least 5 % lower than v8's.
- **R3-H2 (cold, broadly).** v9 is better than v8 in at least 5 of the 6 cold scenarios.
- **R3-H3 (no harm elsewhere).** v9's score on the six warm scenarios is at most 2 % higher than v8's.
- **R3-H4 (comfort is not what pays).** v9's total comfort regret over all 12 scenarios is at most v8's. The development evidence says this is likely to fail. It is kept because an energy saving bought with comfort would not be the claimed mechanism.

Each hypothesis is reported as passed or failed, whatever the outcome.

## Rules

- **Order.** Run once: v9, then v8, then pid_water (`sb/heldout3.sh`), with at most four simulations at a time.
- **Scoring.** `sb/evaluate_round3.py` writes the scores into `docs/RESULTS_ROUND3.md`, whatever the outcome.
- **Crashes.** Crashes are reported, fixed and labelled, as in rounds 1 and 2.
- **Kaggle.** v9 goes to Kaggle only after round 3 is scored. The public leaderboard is never used to choose parameters.
