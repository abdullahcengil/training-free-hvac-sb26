# Held-out results (pre-registered)

Run info: `{"commit": "ad5946615c746745a243560ae3a681eaf7d19618", "started": "2026-10-16T17:45:36Z"}`

| scenario | zonal | bang_bang | fixed_setpoint | pid | pid_water |
|---|---|---|---|---|---|
| building_7001__atlanta_4 | 0.03102 | 0.19799 | 0.03195 | 0.03265 | 0.03262 |
| building_7001__phoenix_2 | 0.02235 | 0.18494 | 0.02701 | 0.02716 | 0.02703 |
| building_7002__denver_1 | 0.02171 | 0.14374 | 0.07731 | 0.07400 | 0.06888 |
| building_7002__singapore_2 | 0.02570 | 0.22767 | 0.02862 | 0.02992 | 0.02990 |
| building_7003__fairbanks_3 | 0.09021 | 0.22984 | 0.11276 | 0.09832 | 0.04569 |
| building_7003__minneapolis_1 | 0.08700 | 0.20122 | 0.11726 | 0.10650 | 0.07463 |
| building_7007__atlanta_7 | 0.01470 | 0.20324 | 0.02647 | 0.02807 | 0.02516 |
| building_7007__phoenix_7 | 0.01965 | 0.21918 | 0.02275 | 0.02316 | 0.02298 |
| building_7008__denver_4 | 0.02393 | 0.19300 | 0.02286 | 0.02283 | 0.02252 |
| building_7008__singapore_5 | 0.02340 | 0.23662 | 0.03067 | 0.03148 | 0.03148 |
| building_7009__fairbanks_6 | 0.01077 | 0.16808 | 0.02549 | 0.02603 | 0.02539 |
| building_7009__minneapolis_5 | 0.02531 | 0.22796 | 0.02151 | 0.02250 | 0.02230 |
| **score** | **0.03298** | 0.20279 | 0.04539 | 0.04355 | 0.03572 |

- **H1** (score at least 30 % below the best baseline, pid_water): reduction 7.7% -> **FAILED**
- **H2** (better than every baseline in at least 10 of 12 scenarios): 8 of 12 -> **FAILED**
- **H3** (total comfort regret at most 10 % of pid_water's): 56.1% -> **FAILED**
- **H4** (descriptive): zonal / best baseline = 0.588 on the 30 training scenarios (pid_water; shipped baseline returns) and 0.923 held out (pid_water). The training-set run was interrupted at 9 of 30 to give round 2 the machine and finished on 17 Oct with the same frozen file; scored 17 Oct 2026 with `sb/evaluate_prereg.py` (the H1-H3 lines above are unchanged by that run).

Scored 17 Oct 2026, 13:45 (UTC+2), with `sb/evaluate_prereg.py`, after deviations 2 and 3 (`docs/DEVIATIONS.md`). All three pass/fail hypotheses failed. Why, and what was done about it: `docs/TUNING_LOG.md` (round-1 diagnosis) and `docs/PREREGISTRATION_2.md`. v8 on this set is reported separately as post hoc (`results/heldout/v8_posthoc`).
