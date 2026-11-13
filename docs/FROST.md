# Frost protection: how cold v16 lets a zone get, and what a 5 C floor costs (rules written 7 Nov 2026, 19:05 by `date`; before any run)

## Why

The simulator has no minimum zone or water temperature and does not model freezing. The hosts (forum 753664, A. Rai,
about 29 Oct): letting pipes freeze "would not be acceptable in a real building. Adding a frost-protection limit to
your policy is a sensible design choice. We would encourage you to describe it in your paper, along with how much it
costs in score." The hosts judge the paper awards.

v16's night glide lets an unoccupied zone float down to the eco band's lower edge plus `glide_floor` (289 K - 16 K =
273 K, -0.15 C). In the round-7 trace of New York (29 Jan, `results/round7_diag/chm__building_7803__newyork_jan29.npz`,
read 7 Nov 18:55) a zone reached -1.05 C; 1.3 % of zone-steps were below 5 C and 0.04 % below 0 C. Chicago (3 Dec):
lowest 2.9 C. So v16 does let zones freeze in deep cold, and the paper should say so with numbers.

## What

`sb/make_v16frost.py` builds `policies/zonal_v16frost.py` = the frozen v16 file plus one option, `frost_min` (K): every
zone's heating floor is at least `frost_min` at all times. With `frost_min` 0 (default) the new line does nothing. It
can bind only in the night glide (the occupied and the non-glide unoccupied floors are 290 K or higher).

Candidate **frost5**: v16's parameters + `frost_min` 278.15 (5 C, a usual frost-protection setpoint).

## Runs (`sb/run_frost.py`; at most 3 at a time)

The 21 cold windows of the tuned check on the shipped simulator (dev 6 cold, round 6: New York 8 Oct, Chicago 19 Nov,
Duluth 17 Dec; rounds 7 and 8: all 6 each), 2880 steps, plus the 6 dev cold windows on the corrected copy (`kit_fixed`).
Hot windows are left out: the glide is off there (24-hour mean outside temperature above 291.45 K), so frost5 equals v16.
Each run also records the lowest true zone temperature and the share of zones below 5 C and 0 C at every step (from
the reward's zone records).

- Arm **v16T**: v16 again with this record, 21 shipped windows.
- Arm **frost5**: 21 shipped + 6 corrected windows.

## Checks and reading rule (fixed now)

- K1: `frost_min` 0 gives v16's actions exactly (288 steps of the first round-7 building).
- K2: arm v16T reproduces the stored v16 rewards step for step in all 21 windows (otherwise its temperatures are not
  v16's).
- F1 (reported as measured): v16's lowest zone temperature over the 21 windows, per window, and the share of zone-steps
  below 0 C and below 5 C.
- F2 (pass/fail): frost5's lowest zone temperature is at least 4.0 C in every window (the one-step lag may let a zone
  dip a little under the floor).
- F3 (reported whatever it is): the cost, frost5's mean loss over v16's, over the 21 shipped windows, over the 6
  corrected ones, and the worst window.

Use: v16, its frozen file and every result in the paper stay as they are. The paper gets a short statement (Limitations
and an appendix paragraph): how cold v16 lets zones get, and what a 5 C frost floor costs in score (F1-F3), as the
hosts asked. The option stays in the repository, off by default. Nothing here goes to the leaderboard.

## Known-answer check K1 (read 7 Nov 2026, 19:08 by the run log)

`frost_min` 0: IDENTICAL to v16, 288 steps (max difference 0). The 42 shipped-simulator runs started 19:08
(`D:/SmartBuildings_data/chain_frost.cmd`, log `frost.log`); the 6 corrected-copy runs follow.

## Result (read 8 Nov 2026, 00:22 by `date`; `python -m sb.run_frost read`)

K2: arm v16T reproduces the stored v16 rewards step for step in all 21 windows ("same").

| set | window | v16 lowest C | v16 zone-steps <5 C | <0 C | frost5 lowest C | frost5 / v16 loss |
|---|---|---:|---:|---:|---:|---:|
| dev | duluth_jan15 | 2.13 | 0.42 % | 0 | 4.76 | 1.0095 |
| dev | chicago_jan15 (7005) | 3.52 | 0.25 % | 0 | 4.82 | 1.0011 |
| r7 | newyork_jan29 | -1.05 | 1.35 % | 0.038 % | 3.29 | 1.0209 |
| r7 | chicago_dec03 | 2.90 | 0.50 % | 0 | 4.39 | 0.9901 |
| r7 | duluth_feb19 | 3.41 | 0.42 % | 0 | 4.64 | 1.0017 |
| r8 | duluth_jan29 | -1.68 | 13.57 % | 2.677 % | 2.93 | 1.0355 |
| r8 | chicago_jan08 | 0.38 | 0.29 % | 0 | 4.36 | 1.0038 |

The other 14 shipped windows never go below 5 C (lowest 5.16 C, Helena 19 Feb), so frost5 equals v16 there (ratio 1.0000).

- F1 (measured): v16's lowest zone temperature over the 21 cold windows is -1.68 C (round 8, Duluth 29 Jan); 7 of 21
  windows go below 5 C and 2 below 0 C; over all windows 0.80 % of zone-steps are below 5 C and 0.129 % below 0 C.
- F2: **FAILED.** frost5's lowest zone is 2.93 C (Duluth 29 Jan) and 3.29 C (New York 29 Jan), under the 4.0 C mark; the
  other 25 windows pass. A floor on the setpoint is not a floor on the temperature in the deepest cold: the lag and the
  limited heating capacity let a zone undershoot. It still lifts every window's minimum above 0 C.
- F3: frost5 costs 0.70 % of loss over the 21 shipped windows (worst 3.55 %, Duluth 29 Jan; one window 1.0 % better) and
  0.12 % over the 6 corrected-simulator windows (worst 0.98 %).

Use (as written): v16 and the paper's results stay. The paper states F1-F3 in Limitations (one sentence) and the
appendix ("Faulty sensors" neighbour), including that the 5 C setpoint floor kept zones above 0 C but not above 4 C.
