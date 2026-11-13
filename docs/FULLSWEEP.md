# One-parameter sensitivity of v14 at full size (30 Oct 2026, 01:48 by `date`; written before any run)

## Why

v14's parameters were tuned on the shipped (scaled) buildings. The hidden buildings appear to be full size
(docs/BIG_BUILDINGS.md), where rooms are two to four times larger for the same box. Every candidate tried at full size
so far changed the code (slab-limited recovery, docs/BIGDEV.md; more heating air in deep cold, docs/V15COLD.md) and
failed. This sweep asks the plainer question first: is v14 still at a local optimum of its own parameters at full
size? Either answer is useful: a parameter that moves is a v15 candidate with no new code; none moving supports the
paper's reading that the full-size loss is the load, not a fault.

## Variants (one parameter each, on top of V14_PARAMS; frozen/zonal_v14f.py, no code change)

| name | parameter | v14 | variant | physical reason to expect a change at full size |
|---|---|---|---|---|
| fhm316 | f_heat_max | 0.2453 | 0.316 | large rooms need more daytime heat; 0.316 is the most a box takes at the 200 Pa pressure floor |
| fhm20 | f_heat_max | 0.2453 | 0.20 | the other side |
| gs50 | glide_safety | 0.6606 | 0.50 | large rooms recover slowly: earlier starts |
| gs80 | glide_safety | 0.6606 | 0.80 | the other side |
| dmp90 | damping | 0.7445 | 0.90 | large rooms move slowly: a faster approach may not overshoot |
| dmp60 | damping | 0.7445 | 0.60 | the other side |
| cs70 | cool_safety | 0.55 | 0.70 | hot nights: later pull-down (comfort is 0.4 % of the hot-weather loss) |
| mh30 | margin_heat | 0.3952 | 0.30 | large rooms drift slowly, so a smaller heating margin may hold |

## Scenarios

Four of the twelve full-size development scenarios (`D:/SmartBuildings_data/bigdev`, docs/BIGDEV.md), first 2880 steps,
reference v14 in `results/bigdev/v14`: building_7001 dubai_jul15 and chicago_jan15, building_7005 lasvegas_jul15,
building_7007 newyork_jan15 (the two largest hot losses and two cold windows from different buildings).

## Reading rule (fixed now)

- A variant is a candidate if its mean loss over the four is at least 1 % below v14's and no scenario is more than 2 %
  worse. Candidates then run on the other eight development scenarios with the same rule over all twelve.
- A candidate that also passes there becomes v15 only after the regression checks of docs/V15COLD.md stage 3 (30
  training scenarios at full length at most 0.3 % above v14) and a blind round on full-size buildings that no run has
  touched, with its own rule written before it is generated.
- If no variant passes, the result goes into the paper as a sensitivity check (each change with its effect), and v14
  stays.

## Deviation (30 Oct 02:21)

The three heating-only variants run first in Dubai in July gave exactly v14's loss (fhm316, fhm20, gs50: 0.03794,
0.00 %). The five heating-only variants (fhm316, fhm20, gs50, gs80, mh30) are therefore not run in Las Vegas in July;
the reading counts them there at v14's loss. The sweep now runs after round 6 and the full-length holiday check
(docs/PREREGISTRATION_6.md, docs/HOLIDAY.md), which come first.

## Result (runs 30 Oct 01:48-09:59; read 10:01 by `date`): no candidate

`python -m sb.run_fullsweep --read` (27 runs; "v14" in Las Vegas means not run, counted at v14's loss): change of
the 10-day loss against v14, in %.

| variant | Dubai Jul | Las Vegas Jul | Chicago Jan | New York Jan | mean of the four | verdict |
|---|---|---|---|---|---|---|
| fhm316 (f_heat_max 0.316) | +0.00 | v14 | +0.01 | -0.04 | -0.00 | no |
| fhm20 (f_heat_max 0.20) | +0.00 | v14 | +0.09 | +0.13 | +0.03 | no |
| gs50 (glide_safety 0.50) | +0.00 | v14 | +1.05 | +2.83 | +0.56 | no |
| gs80 (glide_safety 0.80) | +0.00 | v14 | -0.09 | -1.45 | -0.20 | no |
| dmp90 (damping 0.90) | +1.30 | +1.11 | +2.12 | +2.73 | +1.59 | no |
| dmp60 (damping 0.60) | +0.93 | +0.40 | -1.90 | -2.07 | -0.13 | no |
| cs70 (cool_safety 0.70) | +1.50 | +0.58 | -0.01 | -0.06 | +0.78 | no |
| mh30 (margin_heat 0.30) | +0.00 | v14 | -1.49 | -1.66 | -0.50 | no |

Mark: mean at least 1 % below v14 and no scenario more than 2 % worse. No variant passes, so v14's parameters stay
(v15 shares them), and the result goes into the paper as a sensitivity check.

Split of each change by reward term (summed loss over the run; scratch script sweep_split.py):
- The daytime heating cap (f_heat_max) does not bind at full size in these windows: at most 0.13 % either way.
- In cold weather, each change that heats less (mh30: smaller heating margin; gs80: later recovery start, as the
  glide path assumes 80 % of the identified heating rate; dmp60: a gentler approach, 60 % of the gap closed per step)
  lowers the loss in the January windows by 1.45-2.07 % (gs80 in Chicago only 0.09 %), always the same way: energy
  cost and carbon fall, comfort regret rises (mh30: Chicago 2.48 -> 2.64, New York 0.11 -> 0.16, in summed loss).
  The opposite changes (gs50: earlier start; dmp90: faster approach) raise the loss there by 1.05-2.83 %. Reading: at
  full size the cold-weather optimum lies a little to the energy side of v14's settings, as the size finding would
  suggest (energy is normalised per air handler, comfort per occupant); each single step is worth at most 0.5 % of
  the four-scenario mean.
- In hot weather, cool_safety 0.70 and both damping changes lose 0.4-1.5 %: no change that acts there helps
  (cool_safety was moved one way only).

Not pursued (30 Oct, 10:09 by `date`): a combined heating change would need its own screen, the regression check on
the 30 training scenarios (scaled buildings) and a blind round. The same moves cost at the scaled size in deep cold
(docs/TUNING_LOG.md, screen b, 23 Oct: `glide_safety` 0.80 +5.4 % on three of the cold four, fairbanks_8 +20.7 %), so
a gain at full size would need a rule that knows the building's size, for at most about 0.5 % of the mean here.
v15 stays.
