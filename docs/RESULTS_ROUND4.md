# Round-4 results (pre-registered)

Run info: `{"commit": "24f07c3344ece0087d183cd3bc3a25ba080dece7", "v10_params": {"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.2682, "glide_oat": 291.45, "margin_heat": 0.3952, "margin_cool": 0.4251, "aim_inside": 0.079, "damping": 0.7445, "f_heat_max": 0.2453, "glide_floor": -7.4633, "glide_safety": 0.6606, "sat_econ_max": 295.3467}, "started": "2026-10-21T22:42:40Z"}`

| scenario | v10 | v9 | pid_water |
|---|---|---|---|
| building_7304__phoenix_aug06 | 0.01063 | 0.01241 | 0.07433 |
| building_7306__atlanta_4 | 0.01559 | 0.01557 | 0.03164 |
| building_7308__phoenix_jun25 | 0.01021 | 0.01618 | 0.04211 |
| building_7309__singapore_2 | 0.00487 | 0.00652 | 0.05686 |
| building_7310__atlanta_jul30 | 0.01456 | 0.02024 | 0.04370 |
| building_7313__singapore_5 | 0.01088 | 0.01217 | 0.03862 |
| building_7304__fairbanks_dec | 0.03330 | 0.03376 | 0.13193 |
| building_7306__denver_dec | 0.02907 | 0.02919 | 0.08653 |
| building_7308__fairbanks_3 | 0.00912 | 0.00822 | 0.05088 |
| building_7309__minneapolis_1 | 0.01969 | 0.02013 | 0.08536 |
| building_7310__denver_1 | 0.02735 | 0.02781 | 0.09654 |
| building_7313__minneapolis_2 | 0.05990 | 0.05902 | 0.09216 |
| **warm (6)** | 0.01112 | 0.01385 | 0.04787 |
| **cold (6)** | 0.02974 | 0.02969 | 0.09057 |
| **all (12)** | 0.02043 | 0.02177 | 0.06922 |
| comfort regret (sum, normalised) | -1017.3 | -1048.3 | -7669.4 |

- **R4-H1** (v10 at least 6% below v9 on the warm scenarios): reduction 19.7% -> **PASSED**
- **R4-H2** (v10 better than v9 in at least 5 of 6 warm scenarios): 5 of 6 -> **PASSED**
- **R4-H3** (v10 at least 2% below v9 on the cold scenarios): reduction -0.2% -> **FAILED**
- **R4-H4** (v10 at least 5% below v9 on all 12): reduction 6.1% -> **PASSED**
- **R4-H5** (v10 total comfort regret at most 1.00 x v9's, all 12): -1017.3 vs -1048.3 (ratio 0.97) -> **PASSED** (regret is negative; the ratio compares magnitudes)

Scored 22 Oct 2026 with `sb/evaluate_round4.py` (pass marks copied from the frozen pre-registration). All 36 runs finished without a crash. One deviation, without effect on the numbers: the computer went to sleep from 05:10 to 11:54 during the pid_water runs and the runs resumed after waking (`docs/DEVIATIONS.md`, deviation 4).

Reading:
- The re-tuning transfers where most of its training gain was: warm scenarios -19.7 %, better in 5 of 6 (atlanta_4 is level, 0.01559 vs 0.01557), on six new buildings and three new summer windows. The gain is larger than in training (-12.6 %).
- It does not transfer to the cold scenarios: -0.2 % worse on average. Four of six are slightly better (-0.4 % to -2.2 %), two are worse: building 7308 / fairbanks_3 (+11 %, March) and building 7313 / minneapolis_2 (+1.5 %). In training the cold gain was -5.5 %, so the lower night floor and the smaller margins found by the search fit the training buildings more than they fit cold buildings in general.
- Overall v10 is 6.1 % below v9 and uses less comfort (regret 3 % smaller). Against pid_water, v10 is 70 % lower on all 12 and better in every scenario.
