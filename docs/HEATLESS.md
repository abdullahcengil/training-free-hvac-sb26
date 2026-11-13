# A smaller heating margin? (30 Oct 2026, 18:17 by `date`; written before any run of this screen)

## Why

- At full size, margin_heat 0.30 (v14: 0.3952) lowered v14's loss in both cold development windows where it ran
  (-1.49 % Chicago, -1.66 % New York; docs/FULLSWEEP.md). Heating less (margin 0.30 with glide_safety 0.80) lowered it
  in the first three of six cold full-size windows, in the small-room building most (-1.48, -2.76, -3.30 %;
  docs/SIZEGATE.md), so room size is not what makes it pay.
- The 0.3952 K margin comes from v10's CMA-ES search on six training scenarios (docs/TUNING_LOG.md, 21 Oct), for a
  controller whose first-order zone model predicted six hours ahead with an error of 7.1 K in Fairbanks; v11's slab
  model cut that to 0.9 K. A margin that absorbs prediction error may be larger than v15 needs (opinion).
- glide_safety 0.80 is left out: on the shipped buildings it cost +5.4 % on three of the cold four, +20.7 % in
  fairbanks_8 with comfort 0.00050 -> 0.00375 per step (TUNING_LOG, screen b, 23 Oct).

## Variant

**mh30** = submission/V15_PARAMS.json + margin_heat 0.30, with the frozen v15 file (frozen/zonal_v14f.py); no code
change.

## Screen (`python -m sb.run_screen_m`; starts when the upside check of docs/SIZEGATE.md ends)

- **T:** mh30 on the 30 shipped training scenarios at full length (8640 steps), against v15's recorded runs
  (`results/holiday/ed1_full`).
- **F:** v15 and mh30 on the six cold full-size development windows (bigdev: 7001 and 7005 Chicago, 7002 Helena,
  7003 Duluth, 7007 New York, 7008 Seattle; January 15), first 2880 steps.

## Reading rule (fixed now)

mh30 goes on to a blind round (round 7, with its own plan stamped before its buildings are generated) only if both hold:
- (a) T: the total loss over the 30 is at most 0.1 % above v15's, and no scenario is more than 2 % worse;
- (b) F: the mean loss over the six is at least 1.0 % below v15's, and no window is more than 2 % worse.
Otherwise v15 stays and this line closes; the result goes into the paper's sensitivity appendix either way. Reported
in any case: the change per training climate (Atlanta, Denver, Fairbanks, Phoenix, Singapore) and the split into
comfort and energy. No other margin value is tried on these data.

## Result (runs 30 Oct 18:26-20:47; read 20:47 by `date`): FAIL, v15 stays

`python -m sb.run_screen_m --read` (42 runs, none failed):
- (b) F, six cold full-size windows: mean 0.009235 against v15's 0.009388, **-1.63 %**, better in 6 of 6, worst
  -1.23 % (7005 Chicago). Passes.
- (a) T, 30 training scenarios at full length: mean 0.007173 against 0.007193, -0.27 % (passes the +0.1 % mark),
  better in 17, unchanged in 11 (Phoenix and Singapore without heating), but **building_train_8 atlanta_1 +4.39 %**
  (mark +2 %). Fails.

So mh30 does not go to round 7, and v15 keeps margin_heat 0.3952. By the rule, no other margin value is tried on these
data. `docs/PREREGISTRATION_7.md` was drafted for this case before the result and is not used (not stamped; deleted);
sb/make_round7.py, sb/run_round7.py and sb/make_v16_submission.sh were never run.

Change per climate (summed loss over the six windows of each): Atlanta +0.23 %, Denver -1.19 %, Fairbanks -0.31 %,
Phoenix -0.22 %, Singapore 0.00 %. Comfort regret over the 30 windows: 18.3 -> 23.8 (summed loss terms, x1.30; from
0.98 % to 1.31 % of the summed loss); energy terms fall in every window that heats.

Where atlanta_1 loses (description; per-day sums from the stored per-step terms, scratch script): all of it on one day,
Monday 23 January 2023, the window's first work day (all 30 training windows start on a Sunday at 06:00). Comfort
regret of that day 0.346 -> 1.910 (x5.5), the day's loss 2.315 -> 4.567, from 06:00 to about 16:00, on a mild day (5
to 11 C outside). Every other day changes by at most 0.06 in summed loss, mostly downwards. Over all 30 windows, the
first work day holds 6.3 % of v15's comfort regret and 12.7 % of mh30's (1.16 -> 3.01). Reading (opinion, not
tested): on the first work day each zone model has learned from one day of floating and a first recovery, and a
smaller margin leaves less room for its errors.
