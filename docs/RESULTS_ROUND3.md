# Round-3 results (pre-registered)

Run info: `{"commit": "b7e5ec9d5df75001d3376c5bf7f0ba121a73f19c", "v9_params": {"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.3, "glide_oat": 291.45}, "started": "2026-10-18T02:16:37Z"}`

| scenario | v9 | v8 | pid_water |
|---|---|---|---|
| building_7203__denver_dec | 0.02594 | 0.02897 | 0.06107 |
| building_7204__fairbanks_dec | 0.04767 | 0.05003 | 0.17780 |
| building_7205__minneapolis_dec | 0.02060 | 0.02368 | 0.09455 |
| building_7206__denver_dec | 0.01440 | 0.01680 | 0.08758 |
| building_7208__fairbanks_dec | 0.03950 | 0.04212 | 0.15728 |
| building_7210__minneapolis_dec | 0.04103 | 0.04650 | 0.08790 |
| building_7203__atlanta_6 | 0.01466 | 0.01466 | 0.03925 |
| building_7204__phoenix_8 | 0.00323 | 0.00321 | 0.02457 |
| building_7205__singapore_1 | 0.00630 | 0.00630 | 0.04871 |
| building_7206__atlanta_3 | 0.00585 | 0.00612 | 0.02332 |
| building_7208__phoenix_5 | 0.01730 | 0.01730 | 0.05383 |
| building_7210__singapore_6 | 0.01106 | 0.01106 | 0.03505 |
| **cold (6)** | 0.03152 | 0.03468 | 0.11103 |
| **warm (6)** | 0.00973 | 0.00978 | 0.03745 |
| **all (12)** | 0.02063 | 0.02223 | 0.07424 |
| comfort regret (sum, normalised) | -681.8 | -635.5 | -7607.0 |

- **R3-H1** (v9 at least 5% below v8 on the cold scenarios): reduction 9.1% -> **PASSED**
- **R3-H2** (v9 better than v8 in at least 5 of 6 cold scenarios): 6 of 6 -> **PASSED**
- **R3-H3** (v9 at most 2% worse than v8 on the warm scenarios): change -0.4% -> **PASSED**
- **R3-H4** (v9 total comfort regret at most v8's, all 12): -681.8 vs -635.5 -> **FAILED** (regret is negative; closer to 0 is better)

Scored 18 Oct 2026 with `sb/evaluate_round3.py` (pass marks copied from the frozen pre-registration). All 36 runs finished without a crash; no deviation.

Reading:
- The cold-climate change transfers to six new buildings and three new December strips. v9 is 9.1 % below v8 on the cold scenarios, and better in all six.
- v9 does no harm elsewhere: four of the six warm scenarios are identical (the heating-season gate keeps the glide off), atlanta_3 (April) is better, and phoenix_8 (November-December) is 0.6 % worse.
- The comfort hypothesis failed, as the development runs had warned: total comfort regret is 7 % larger than v8's. So the saving is mostly energy, bought partly with comfort; the score counts both and is lower.
- Against pid_water, the best official baseline, v9 is 72 % lower on all 12 (0.02063 vs 0.07424) and better in every scenario.
