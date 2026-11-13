# pid_water on the buildings of rounds 6 and 7 (written 31 Oct 2026, 03:24 by `date`; before any of these runs, while round 7 runs)

## Why

Figure 2a of the paper (`sb/fig_transfer.py`) shows every unseen scenario in which both our frozen version and the
official pid_water baseline ran. Rounds 6 and 7 ran only our versions (their hypotheses compare two of our versions),
so their twelve full-size scenarios are missing from it, although full-size buildings are the closest we have to the
hidden test set (docs/BIG_BUILDINGS.md). The figure's full-size set has 16 scenarios on eight buildings; these runs
would add twelve more buildings.

## What

`python -m sb.run_pid_r67` (restartable, three simulations at most, started only after round 7 has finished) runs
pid_water from the starter kit, unchanged, on the six scenarios of round 6 (`D:/SmartBuildings_data/round6h`) and
the six of round 7 (`D:/SmartBuildings_data/round7`), first 2880 steps, as in the rounds. Results:
`results/round6h/pid_water`, `results/round7/pid_water`; `python -m sb.run_pid_r67 --read` prints each scenario's
loss ratio of our arms to pid_water.

## Rule (fixed now)

Descriptive, no hypothesis. All twelve go into Figure 2a and its counts, whatever they show: round 6 with v15 (the
version frozen for it, arm `ed1`), round 7 with the version that is final after round 7 (chm if H1, H2 and H3 of
docs/PREREGISTRATION_7.md pass, v15 otherwise). The paper's sentence "below the strongest official baseline in all
N unseen scenarios" is rewritten with the new count, and any scenario where ours is not below pid_water is named.

## Result (runs 31 Oct 04:25-05:22; read 05:22 by `date`)

`python -m sb.run_pid_r67 --read`: our version was below pid_water in all twelve scenarios.

| round | scenario | pid_water | ours | ratio |
|---|---|---|---|---|
| 6 (v15) | building_7701 houston_may28 | 0.02712 | 0.00650 | 0.240 |
| 6 (v15) | building_7702 miami_jul02 | 0.03794 | 0.01170 | 0.308 |
| 6 (v15) | building_7703 dubai_sep03 | 0.06779 | 0.02832 | 0.418 |
| 6 (v15) | building_7704 newyork_oct08 | 0.03788 | 0.00312 | 0.082 |
| 6 (v15) | building_7705 chicago_nov19 | 0.09094 | 0.01360 | 0.149 |
| 6 (v15) | building_7706 duluth_dec17 | 0.09512 | 0.01025 | 0.108 |
| 7 (v16) | building_7802 helena_feb19 | 0.11359 | 0.01720 | 0.151 |
| 7 (v16) | building_7803 newyork_jan29 | 0.10141 | 0.01381 | 0.136 |
| 7 (v16) | building_7804 chicago_dec03 | 0.14350 | 0.02253 | 0.157 |
| 7 (v16) | building_7806 sanfrancisco_mar05 | 0.05664 | 0.00353 | 0.062 |
| 7 (v16) | building_7807 duluth_feb19 | 0.11949 | 0.03601 | 0.301 |
| 7 (v16) | building_7808 seattle_nov26 | 0.06637 | 0.00472 | 0.071 |

Means over the six: round 6 pid_water 0.059464, v15 0.012247 (79.4 % below); round 7 pid_water 0.100166, v16
0.016301 (83.7 % below). Figure 2a (`sb/fig_transfer.py`, redrawn 05:22): full size 28 of 28 on 20 buildings (ratio
median 0.171, quartiles 0.121-0.303); since v8, 116 of 116 unseen scenarios below pid_water.
