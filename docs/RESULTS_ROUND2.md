# Round-2 results (pre-registered)

Run info: `{"commit": "e8dbcd3163f2d0e4ce9006b02ed7067a5f5927bd", "v8_params": {"safety_pred": 2, "dist_obs": 1}, "started": "2026-10-16T22:45:19Z"}`

| scenario | v8 | v7 | bang_bang | fixed_setpoint | pid | pid_water |
|---|---|---|---|---|---|---|
| building_7102__denver_3 | 0.00658 | 0.04025 | 0.23123 | 0.08356 | 0.04041 | 0.02523 |
| building_7102__minneapolis_3 | 0.00746 | 0.03947 | 0.22541 | 0.09164 | 0.05876 | 0.03607 |
| building_7104__minneapolis_6 | 0.00520 | 0.02702 | 0.25010 | 0.01762 | 0.01799 | 0.01793 |
| building_7104__phoenix_1 | 0.00537 | 0.02183 | 0.19407 | 0.07738 | 0.04371 | 0.03530 |
| building_7105__minneapolis_7 | 0.00368 | 0.01535 | 0.18062 | 0.02473 | 0.02486 | 0.02458 |
| building_7105__singapore_3 | 0.01032 | 0.02081 | 0.22999 | 0.02907 | 0.03017 | 0.03015 |
| building_7106__fairbanks_7 | 0.01197 | 0.01806 | 0.18611 | 0.07425 | 0.07444 | 0.06772 |
| building_7106__minneapolis_8 | 0.02178 | 0.02940 | 0.19348 | 0.09995 | 0.08685 | 0.07573 |
| building_7111__atlanta_5 | 0.00967 | 0.05031 | 0.32043 | 0.24546 | 0.09357 | 0.05163 |
| building_7111__minneapolis_2 | 0.03128 | 0.06106 | 0.23325 | 0.19048 | 0.15022 | 0.12117 |
| building_7112__fairbanks_4 | 0.00306 | 0.01561 | 0.19795 | 0.02013 | 0.02039 | 0.01996 |
| building_7112__minneapolis_4 | 0.00552 | 0.02659 | 0.24605 | 0.01918 | 0.02101 | 0.01983 |
| **score** | **0.01016** | 0.03048 | 0.22406 | 0.08112 | 0.05520 | 0.04378 |
| comfort regret (sum, normalised) | -302.0 | -2362.7 | -20469.8 | -8082.4 | -7020.8 | -6000.1 |

- **R2-H1** (v8 score at least 20% below v7's): reduction 66.7% -> **PASSED**
- **R2-H2** (v8 better than v7 in at least 10 of 12): 12 of 12 -> **PASSED**
- **R2-H3** (v8 at least 30% below the best baseline, pid_water): reduction 76.8% -> **PASSED**
- **R2-H4** (v8 total comfort regret at most v7's): -302.0 vs -2362.7 -> **PASSED** (regret is negative; closer to 0 is better)
