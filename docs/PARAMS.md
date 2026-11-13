# What the controller learns about each zone (written 31 Oct 2026, 03:29 by `date`; before any of these runs)

## Question

The paper says that five numbers per zone, learned online, carry everything building-specific the controller needs
(Section 3.2, Eq. 1; Conclusion). Are they physical? The controller never sees the floor plan. If the heat gain g of
Eq. 1 (kelvin per step per unit of heat) is the inverse of the zone's heat capacity, then within one building it
should fall in proportion to the zone's floor area: log g against log area with slope -1. The relaxation rate lambda
should grow with the zone's share of exterior cells.

## Runs (descriptive; no decision depends on them)

`python -m sb.run_params` (sb/param_dump.py; restartable; three simulations at most; started only after round 7 and
the pid_water runs of docs/BASELINE_R67.md): frozen v15, 2016 steps (one week) from the window's start, on the six
shipped training buildings (building_train_1 fairbanks_1, train_2 fairbanks_2, train_4 denver_2, train_5 denver_3,
train_7 fairbanks_7, train_8 fairbanks_8) and the six full-size buildings of round 7 in their round-7 windows. Each
zone's five numbers are averaged over the last day of the week; its floor area and its number of cells next to an
exterior wall come from the simulator's grid. Results: `results/params/v15/*.json`.

## What is reported (fixed now)

- Within-building slope of log g on log area (one intercept per building), with a bootstrap interval over buildings,
  and the share of zones whose g sits at its bound (`m2_lo`, `m2_hi`), for all twelve buildings and for the shipped
  and full-size groups separately.
- The same for lambda against the exterior share (exterior cells / all cells of the zone).
- Whatever they show goes into the paper's appendix; a sentence in the main text only if the slope's interval
  excludes 0.

## Change of data (31 Oct, 03:35 by `date`): no new runs

The runs above were cancelled before any started (the waiter was stopped at 03:34). The size-gate diagnostic
(docs/SIZEGATE.md, 30 Oct) already traced v15's identified parameters at every step, with each zone's true floor area,
for the first three days of a cold window in 17 buildings: the six shipped training buildings (Fairbanks), six
full-size development buildings and five of them scaled to the shipped size. `python -m sb.params_read` reads those
traces (gain g averaged over day 3). Their rank correlations of 1/g with area (0.63-0.82 in the full-size buildings)
were already in the paper's Appendix I; the slope below is new. The exterior-share question is dropped (the traces
have no exterior cells).

## Result (read 31 Oct, 03:35)

| buildings | zones | at a bound of g | within-building slope of log g on log area (95 % over buildings) | R2 |
|---|---|---|---|---|
| 6 shipped | 323 | 0 | -0.27 (-0.38 to -0.14) | 0.44 |
| 6 full size | 476 | 0 | -0.40 (-0.47 to -0.35) | 0.54 |
| 5 scaled twins | 388 | 0 | -0.25 (-0.40 to -0.16) | 0.40 |
| all 17 | 1187 | 0 | -0.32 (-0.39 to -0.24) | 0.46 |

Every building's own slope is negative (-0.06 to -0.54). Reading: the learned gain falls as the room grows, in every
building, although the controller never sees the floor plan; but it falls far less than in proportion (slope -1),
so g is not simply the inverse of the room's heat capacity over three days (opinion: the room air reaches only part of
the room's mass within a step, and the slab node takes the rest). By the rule above, a sentence may go into the main
text (the interval excludes 0).
