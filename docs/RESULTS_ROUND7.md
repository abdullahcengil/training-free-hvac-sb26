# Round 7 (blind, full size, cold): results (runs 31 Oct 2026 03:23-04:21; read 04:21 by `date`)

Plan: docs/PREREGISTRATION_7.md (written 30 Oct 23:43, before the screen's results; frozen copy
`docs/preregistration7/PREREGISTRATION_7_2026-10-31.md` stamped 31 Oct 03:21:35 with its OpenTimestamps proof, after
the screen of docs/CHATTER.md passed), scenarios generated after it (03:22-03:23; manifest
`docs/preregistration7/MANIFEST7_2026-10-31.txt`; seeds 7801 and 7805 rejected by the generator's own check, spares
7807 and 7808 used in order). Runs `results/round7/{v15,chm}`, first 2880 steps (ten days from a Sunday 06:00);
`python -m sb.run_round7 --read`.

| slot | scenario | v15 | chm | change | energy terms | comfort v15 -> chm |
|---|---|---|---|---|---|---|
| 1 | building_7807 duluth_feb19 | 0.03607 | 0.03601 | -0.17 % | -1.25 % | 0.00110 -> 0.00148 |
| 2 | building_7802 helena_feb19 | 0.01725 | 0.01720 | -0.27 % | -0.87 % | 0.00024 -> 0.00034 |
| 3 | building_7803 newyork_jan29 | 0.01545 | 0.01381 | -10.61 % | -4.39 % | 0.00138 -> 0.00036 |
| 4 | building_7804 chicago_dec03 | 0.02868 | 0.02253 | -21.42 % | -8.75 % | 0.00706 -> 0.00281 |
| 5 | building_7808 seattle_nov26 | 0.00484 | 0.00472 | -2.48 % | -2.56 % | 0.00001 -> 0.00001 |
| 6 | building_7806 sanfrancisco_mar05 | 0.00362 | 0.00353 | -2.41 % | -2.59 % | 0.00000 -> 0.00001 |

Loss and its terms are means per step over the ten days.

- **H1 PASS**: mean 0.016301 against 0.017650, -7.64 % (mark: at least 0.5 % lower).
- **H2 PASS**: better in 6 of 6 (mark 4).
- **H3 PASS**: worst building -0.17 % (mark: none more than 2 % worse).
- **H4 PASS**: comfort regret summed over the six 0.00501 against 0.00979, 0.51 times v15's (mark 1.5).

The expectation written in the plan (opinion: a mean of -0.5 to -1.5 %, H1 might fail) was far too low. Most of the
gain sits in two buildings, New York (-10.6 %) and Chicago (-21.4 %), where v15's comfort term was large (0.00138 and
0.00706 per step) and fell by a factor of 2.5-3.8 together with the energy. In the two coldest windows (Duluth,
Helena) the smaller margin saved energy and cost a little comfort, as in the development windows. Why New York and
Chicago changed so much is not yet known: trace dumps of both arms on both buildings are queued
(sb/run_r7_traces.py, after the pid_water runs of docs/BASELINE_R67.md).

Decision (plan): H1, H2 and H3 pass, so chm becomes **v16** (frozen/zonal_v16f.py = zonal_v16dev_ch.py unchanged,
submission/V16_PARAMS.json = V15_PARAMS + cool_hold 2 + margin_heat 0.30); H4 passes too. Next, by the plan:
`bash sb/make_v16_submission.sh` (notebook and its check) and a Kaggle submission, its reading rule written in
docs/RESULTS_EXTERNAL.md before it is sent.

## Why Chicago changed (traces read 31 Oct 05:38 by `date`; sb/run_r7_traces.py, results/round7_diag)

Trace dumps of both arms on building_7804 chicago_dec03 (first 2880 steps; each reproduces its round-7 run):
- Under v15, two of the 54 zones (box order 33 and 47) switched between strong heating (above half their maximum
  heat, 28-33 kW) and strong cooling (above half their maximum cooling, 46-47 kW) within two steps 15 to 66 times on
  every work day (none on the weekend), swinging between about 13 and 28 C. They held 4318 of the building's 4770
  occupied kelvin-person-steps outside the band (90 %). Their planned heat summed to 12193 and 10971 kW-steps, their
  planned cooling to 9839 and 7842: heating and cooling fought each other.
- Under v16 their cooling never exceeded 1.6 kW (the minimum airflow), their planned cooling fell from 17682 to 435
  kW-steps (-97.5 %), and their occupied discomfort from 4318 to 1208 (-72 %). Building total 4770 -> 1719.
- v16 still cycles on heat alone in these zones during the morning recovery (on the last day until about 10:00):
  with no cooling the zone falls back by itself, and the cycle dies out.
- The scan of all 54 zones (`--read`): zones with more than five sign changes of the planned heat per day 14 -> 10;
  heat spent against cooling 12.2 % -> 4.4 % of the heating.
Figure: `sb/fig_round7.py` -> docs/fig/fig_round7.png (paper Appendix K, Figure "fig:r7"). New York's traces follow.

## Why New York changed (traces read 31 Oct 06:02 by `date`)

building_7803 newyork_jan29 (both traces reproduce their round-7 runs exactly):
- Under v15 one of the 123 zones (box order 91, 26.3 m2, the building's smallest room; median 303.9 m2) switched
  between strong heating and strong cooling 65 to 68 times on every work day (none on the weekend). It held 2099 of
  the building's 2190 occupied kelvin-person-steps outside the band (96 %); planned heat 11077, cooling 7807 kW-steps.
- Under v16 its cooling never exceeded 1.0 kW and summed to 69 kW-steps (-99 %); its occupied discomfort fell to 286
  (-86 %), the building's to 405 (-82 %).
In Chicago the two cycling zones are the building's two smallest rooms (20.3 and 27.4 m2; median 372.0 m2). Every
zone has the same 2 m3/s box, so in these rooms one step of heating above 10 kW raises the air by 7-10 K (median per room;
9.8, 7.4 and 8.3 K).

## v16 on the six round-6 buildings (post hoc; runs 31 Oct 06:02-06:30, read 06:30 by `date`)

`python -m sb.run_v16_r6 --read` (sb/run_v16_r6.py; against v15's round-6 runs, results/round6h/ed1), first 2880
steps: identical step for step in the three hot windows (Houston May, Miami July, Dubai September); New York October
-2.50 %, Chicago November -1.56 %, Duluth December (Christmas) +1.79 % with its comfort term 0.00013 -> 0.00041 per
step. Mean -0.14 %. The Duluth window is the first building where v16 is worse by more than 1 %; within the 2 % of
round 7's H3, but post hoc. The smaller heating margin is the likely cause (comfort, not energy); the ablation on the
round-7 buildings (sb/run_r7_ablation.py, next) separates the two changes.

## Which half of v16 won round 7? (post hoc; runs 31 Oct 06:30-07:33, read 07:33 by `date`)

`python -m sb.run_r7_ablation --read` (sb/run_r7_ablation.py): the two changes of v16 one at a time on the six round-7
buildings, first 2880 steps. `ch` = V15 + cool_hold 2, `mh` = V15 + margin_heat 0.30 (policy frozen/zonal_v16f.py,
which with cool_hold 0 computes what v15 computes).

| building | v15 | ch (cool_hold only) | mh (margin only) | chm (v16) |
|---|---|---|---|---|
| 7802 Helena Feb | 0.01725 | 0.01725 (0.00 %) | 0.01720 (-0.27 %) | 0.01720 (-0.27 %) |
| 7803 New York Jan | 0.01545 | 0.01386 (-10.29 %) | 0.01526 (-1.22 %) | 0.01381 (-10.61 %) |
| 7804 Chicago Dec | 0.02868 | 0.02227 (-22.34 %) | 0.02862 (-0.18 %) | 0.02253 (-21.42 %) |
| 7806 San Francisco Mar | 0.00362 | 0.00362 (0.00 %) | 0.00353 (-2.41 %) | 0.00353 (-2.41 %) |
| 7807 Duluth Feb | 0.03607 | 0.03607 (0.00 %) | 0.03601 (-0.17 %) | 0.03601 (-0.17 %) |
| 7808 Seattle Nov | 0.00484 | 0.00484 (0.00 %) | 0.00472 (-2.48 %) | 0.00472 (-2.48 %) |
| mean | 0.017650 | 0.016318 (-7.55 %) | 0.017558 (-0.52 %) | 0.016301 (-7.64 %) |

Reading (descriptive):
- The cool-hold rule carries 7.55 of the 7.64 %, all of it in the two buildings whose smallest rooms cycled (New York,
  Chicago); in the other four it changes nothing (ch equals v15 to five digits, and chm equals mh).
- The smaller margin lowers the loss a little in all six buildings (0.17-2.48 %), by energy, while the comfort term
  rises in the coldest (Helena 0.00024 -> 0.00034, Duluth 0.00110 -> 0.00148 per step). On top of the cool-hold rule
  it costs Chicago 1.2 % (0.02227 -> 0.02253; comfort term 0.00233 -> 0.00281).
- Consistent with the post-hoc round-6 Duluth window (+1.8 %, comfort tripled): the margin, not the cool-hold rule,
  is the likely cause there (not run: ch on round 6).
- v16 stays as frozen and tested. A version with the cool-hold rule alone would have been 0.1 % worse here; no
  evidence of a gain above 1 %, so no new candidate.
