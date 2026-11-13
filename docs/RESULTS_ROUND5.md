# Round-5 results (pre-registered)

Run info: `{"commit": "405fc6215f334af2184a5626056e34baac4c37ef", "v11_params": {"safety_pred": 2, "dist_obs": 1, "night_glide": 1, "f_heat_rec": 0.2682, "glide_oat": 291.45, "margin_heat": 0.3952, "margin_cool": 0.25, "aim_inside": 0.079, "damping": 0.7445, "f_heat_max": 0.2453, "glide_floor": -12.0, "glide_safety": 0.6606, "sat_econ_max": 295.3467, "mass_model": 1, "f_heat_safety": 0.45, "dp_reset": 2, "cool_glide": 1, "m2_rate": 1, "cool_safety": 0.55, "cool_ceiling": 8.0}, "started": "2026-10-22T19:12:32Z"}`

| scenario | v11 | v10 | pid_water |
|---|---|---|---|
| building_7401__minneapolis_jan29 | 0.00687 | 0.01067 | 0.06399 |
| building_7402__fairbanks_jan22 | 0.02550 | 0.03079 | 0.11559 |
| building_7403__denver_feb05 | 0.01037 | 0.01585 | 0.07661 |
| building_7406__denver_sep03 | 0.00312 | 0.00488 | 0.02597 |
| building_7407__minneapolis_mar12 | 0.01583 | 0.02167 | 0.09212 |
| building_7408__fairbanks_apr16 | 0.00448 | 0.00755 | 0.05715 |
| building_7401__phoenix_may14 | 0.00567 | 0.00806 | 0.04052 |
| building_7402__singapore_may21 | 0.00624 | 0.00710 | 0.02885 |
| building_7403__atlanta_jun18 | 0.00327 | 0.00550 | 0.05240 |
| building_7406__atlanta_sep10 | 0.00300 | 0.00389 | 0.01865 |
| building_7407__singapore_jan01 | 0.00936 | 0.01093 | 0.03387 |
| building_7408__phoenix_sep17 | 0.00552 | 0.01053 | 0.05651 |
| **cold (6)** | 0.01103 | 0.01524 | 0.07191 |
| **warm (6)** | 0.00551 | 0.00767 | 0.03847 |
| **all (12)** | 0.00827 | 0.01145 | 0.05519 |
| comfort regret (sum, normalised) | -92.9 | -334.4 | -6793.8 |

- **R5-H1** (v11 at least 15% below v10 on all 12): reduction 27.8% -> **PASSED**
- **R5-H2** (v11 better than v10 in at least 10 of 12): 12 of 12 -> **PASSED**
- **R5-H3** (v11 at least 15% below v10 on the cold scenarios): reduction 27.6% -> **PASSED**
- **R5-H4** (v11 at least 15% below v10 on the warm scenarios): reduction 28.2% -> **PASSED**
- **R5-H5** (v11 total comfort regret at most 0.55 x v10's, all 12): -92.9 vs -334.4 (ratio 0.28) -> **PASSED** (regret is negative; the ratio compares magnitudes)

Scored 22 Oct 2026, 23:46 (UTC+2), with `sb/evaluate_round5.py` (pass marks copied from the frozen pre-registration),
as soon as the 12 v10 runs had finished; pid_water (descriptive, no hypothesis) was still running and is added when
it finishes. No crash. One deviation, without effect on the numbers: the run was stopped at 22:22 for an update after
all 12 v11 runs and resumed at 22:27 (`docs/DEVIATIONS.md`, deviation 5).

Reading:
- All five hypotheses pass. v11 is 27.8 % below v10 on six new buildings and twelve new 30-day windows, better in
  12 of 12, by about the same amount in cold (-27.6 %) and warm (-28.2 %) scenarios, with comfort regret 72 % lower.
- The held-out gain is somewhat smaller than the training gain (-31.9 %) on both sides: cold -27.6 % against
  -32.6 %, warm -28.2 % against -31.1 %. The smallest gains are in Singapore (-12 %, -14 %), the largest in
  phoenix_sep17 (-48 %), fairbanks_apr16 and atlanta_jun18 (-41 % each).
- Minneapolis, a station no development run has used, gains -36 % (January) and -27 % (March).
- pid_water (descriptive, added at 01:16 on 23 Oct when its runs finished; the hypotheses above were scored without
  it and are unchanged): v11 is 85 % below pid_water on all 12 (0.00827 against 0.05519) and better in every scenario.
