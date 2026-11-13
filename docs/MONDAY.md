# First work day after a weekend or holiday (rules written 8 Nov 2026, 00:58 by `date`; before any run)

For the second, public-tuned Kaggle selection only (docs/LEADERBOARD_PROBE.md); not part of the paper.

## Why (measured, `python -m sb.where_c8 c8`, 30 windows of the tuned check, read 8 Nov 2026, 00:58)

Against v16, the tuned line c8 (deep night float, late recovery start, smaller heating margin) saves energy on ordinary
work days (net -15.1e-5 of mean loss per step) and on weekends (-16.6e-5), but on the first work day after a weekend
it is net worse (+6.5e-5: comfort +14.2e-5, energy -7.7e-5). Per day, its extra comfort loss on such days is about
five times that of other work days: after 60 hours of float the slab is cold, and the late, shallow-margin recovery
does not get the rooms into the band by 06:00 or keep them there.

## What

`sb/make_v16mon.py` builds `policies/zonal_v16mon.py` = the frozen v16 file plus `mon_mode`: when nobody has been
in for more than 24 hours, the night before the next comfort period and that comfort period use `mon_safety`,
`mon_floor` and `mon_margin` in place of glide_safety, glide_floor and margin_heat. It reads only the building's
occupant total, which is observed.

## Runs (`sb/run_mon.py`, after the skip screen, at most 3 at a time)

The 6 cold full-size development windows of the tuned check, 2880 steps. Reference B = c8fhm40 (from the skip screen,
`results/burst/B`).
- M1 = B + mon_mode 1 with v16's settings for those days (safety 0.6606, floor -16, margin 0.30).
- M2 = B + mon_mode 1 with intermediate settings (safety 0.80, floor -20, margin 0.25).
(Hot windows: the night glide is off above a 24-hour mean of 18.3 C, so only margin_heat could differ there; checked
after a pass, before any submission.)

## Reading rule (fixed now)

- K1: mon_mode 0 gives v16's rewards exactly (288 steps of the first round-7 building).
- An arm goes to the leaderboard if (1) its mean loss over the 6 cold windows is at least 0.7 % below B's, (2) its
  comfort term is not above B's, and (3) it is worse than B in at most 1 of the 6. If both pass, the lower goes, then
  the other if a slot is free.

## Result (read 08 Nov 05:11, `python -m sb.run_mon read`; runs 04:09-05:10)

| window (cold, full size) | B (c8fhm40) | M1 / B | M2 / B |
|---|---|---|---|
| building_7001 chicago_jan15 | 0.01609 | 0.9835 | 0.9858 |
| building_7002 helena_jan15 | 0.00857 | 1.0082 | 1.0030 |
| building_7003 duluth_jan15 | 0.00474 | 1.0331 | 1.0192 |
| building_7005 chicago_jan15 | 0.01149 | 1.0050 | 1.0014 |
| building_7007 newyork_jan15 | 0.00940 | 1.0250 | 1.0118 |
| building_7008 seattle_jan15 | 0.00296 | 1.0431 | 1.0250 |
| mean loss | 0.00888 | 0.00894 (+0.72 %) | 0.00889 (+0.17 %) |
| comfort term vs B | | 0.58x | 0.71x |
| worse than B in | | 5 of 6 | 5 of 6 |

K1 passed (identical, 04:09). **Both arms fail rules (1) and (3)**: the first-work-day settings cut the comfort term
by 29-42 %, as intended, but the extra heating on the night before and during that day costs more energy than the
comfort it buys, in five of six windows (only the coldest Chicago window gains). Same lesson as docs/ADAPT_START.md:
under this reward a late Monday morning costs less than the gas of a shallower weekend night. Neither arm goes to the
leaderboard.
