# Empty holidays (30 Oct 2026, 01:55 by `date`; written before any run)

## What the simulator does (code read 30 Oct)

- Occupancy (`randomized_arrival_departure_occupancy.py`, `peek`): nobody comes in on a day that is not a work day, and
  `conversion_utils.is_work_day` excludes US federal holidays (pandas `USFederalHolidayCalendar`).
- The setpoint schedule (`setpoint_schedule.py`) is built with no holidays in the competition's configs, so the comfort
  period (06:00-19:00) and the `comfort_mode_now` observation stay on.
- The comfort term of the reward is the occupancy-weighted mean shortfall over zones, and zero when nobody is in
  (`setpoint_energy_carbon_regret.py`). On a holiday, every kWh spent holding the comfort band buys nothing.
- The controller does not observe the date, but it observes `num_occupants`. Arrivals start at 06:00 with a 1/36
  chance per occupant per 5-minute step and there are two occupants per zone, so with 20 zones the chance that nobody
  has arrived by 07:00 on a work day is 0.71^40, about 1e-6.

How much is at stake (v14's own runs, `results/dev14_8640/of3`, per-step arrays; scratch script holiday_bound.py):
v14's loss from 07:00 to 19:00 on weekday holidays is 2.0 % of the loss of all 70 development windows (30 training,
40 stress); 43 of the 70 windows hold such a holiday, where it is 1.3-8.4 % of the window. That is an upper bound:
floating through the holiday is not free, and the next morning's recovery starts from further away.

## The option (already in the frozen v14 file, off in v14)

`empty_day` 1 with `empty_h` 1.0: if nobody has come in one hour after the comfort period starts, the rest of the day
is run as unoccupied, with the setbacks planning towards the next work day's comfort period. If anybody comes in
later, the comfort period resumes at once. An earlier version (v11 development, 22 Oct, `empty_h` 1.5, together with
an afternoon rule) gained 0.1 % on singapore_7 and lost 0.9 % on fairbanks_1, where the building cooled over a
three-day float; v14's recovery has changed since (slab-aware heating cap, boost, disturbance estimate).

## Screen (rule fixed now)

Frozen `zonal_v14f.py`, V14_PARAMS plus `empty_day` 1, `empty_h` 1.0, shipped size, each run from the window's start
until two days after its first holiday; the reference is v14's own per-step reward in `results/dev14_8640/of3`
(same code, same steps; the steps before the first holiday must match it exactly, as an identity check).
Scenarios (holiday in brackets): train_7 duluth_jan15, train_1 chicago_jan15, train_2 sanfrancisco_jan15, train_8
dubai_jan15 (16 Jan), train_1 fairbanks_1 (2 Jan), train_7 singapore_6 (4 Sep), train_5 fairbanks_5 (19 Jun), train_7
denver_5 (4 Jul), train_2 denver_8 (10 Nov, a Friday), train_2 phoenix_6 (4 Sep).

For each scenario, the change is the difference of summed loss over the run divided by v14's summed loss over the
full 30-day window (what the window's score would change by if nothing after the run changed).
- Promising if the mean change over the ten is at most -0.5 % and no scenario is worse than +1.0 %.
- Promising leads to full-length runs on all 70 development windows (mean at least 0.3 % below v14, none worse than
  +1 %), then a blind round with its own rule written before generation (new seeds, full size, windows chosen to hold
  holidays and windows without), then a Kaggle submission. Otherwise v14 stays and the result goes into the notes.

## Screen result (runs 30 Oct 02:03-02:17; read 02:17): PROMISING

Change of each window's 30-day loss (`python -m sb.run_holiday --read`); identity before every holiday exact (0.0):

| window | holiday | change | holiday day loss | next work day loss |
|---|---|---|---|---|
| train_7 duluth_jan15 | Mon 16 Jan | -1.03 % | 8.256 -> 3.791 | 7.700 -> 8.785 |
| train_1 chicago_jan15 | Mon 16 Jan | -0.90 % | 3.162 -> 1.213 | 2.319 -> 2.935 |
| train_2 sanfrancisco_jan15 | Mon 16 Jan | -2.44 % | 0.932 -> 0.440 | 0.933 -> 0.920 |
| train_8 dubai_jan15 | Mon 16 Jan | -3.39 % | 0.683 -> 0.078 | 1.034 -> 1.133 |
| train_1 fairbanks_1 | Mon 2 Jan | -0.37 % | 7.233 -> 3.829 | 12.679 -> 14.517 |
| train_7 singapore_6 | Mon 4 Sep | -1.71 % | 2.129 -> 0.591 | 2.292 -> 2.933 |
| train_5 fairbanks_5 | Mon 19 Jun | -0.28 % | 0.159 -> 0.050 | 0.524 -> 0.588 |
| train_7 denver_5 | Tue 4 Jul | -1.80 % | 0.976 -> 0.097 | 0.820 -> 0.967 |
| train_2 denver_8 | Fri 10 Nov | -2.63 % | 1.183 -> 0.313 | (Monday) 3.267 -> 3.130 over the rest |
| train_2 phoenix_6 | Mon 4 Sep | -1.47 % | 3.318 -> 2.123 | 3.328 -> 3.581 |

- Mean -1.60 %, worst -0.28 %: better in 10 of 10 (mark: mean at most -0.5 %, none worse than +1.0 %).
- The next work day pays back 30 % of the holiday's saving over the ten (4.593 of 15.506; the recovery starts from
  further away; in deep cold, Fairbanks 2 January, 54 %). Comfort regret over the ten runs 1.09 times v14's (0.956 -> 1.046;
  largest rise singapore_6 0.013 -> 0.042).
- Next (rule above): full-length runs on all 70 development windows and a blind round (docs/PREREGISTRATION_6.md),
  run side by side; the round's rules are fixed before its scenarios are generated.

## Notebook (30 Oct, 03:39)

`submission/zonal_v15_submission.ipynb` (frozen v14 file, V14_PARAMS plus `empty_day` 1, `empty_h` 1.0; only its
PARAMS line differs from v14's notebook). `sb/nbcheck.py` (as `sb.nbcheck_job`, queued in the scheduler) on stress
building_train_7 duluth_jan15, whose first work day (16 January) is a holiday: identical actions for 576 steps, total
reward -7.222664, equal to the first 576 steps of the screen run (`results/holiday/ed1`). Not submitted until the
full-length check above passes.

## Full-length check (runs 30 Oct 03:09-07:49; read 07:50 by `date`): PASS

`python -m sb.run_holiday --read` (all 70 development windows, 8640 steps; frozen v14 file with V14_PARAMS plus
`empty_day` 1, `empty_h` 1.0, in `results/holiday/ed1_full`; reference v14's own runs in `results/dev14_8640/of3`):

- Mean over the 70: 0.007219 against 0.007313 (-1.28 %); better in 43, identical in 27, worse in none (mark: mean at
  least 0.3 % below v14, none worse than +1.0 %).
- The 43 windows with a weekday holiday: summed loss -1.79 % (energy cost -24.904, carbon -32.619, comfort +0.711, in
  summed loss; v14's total 3169.7). Their comfort term rose 1.6 % (43.444 -> 44.154): at full length a holiday weighs
  less than in the ten-day windows of round 6 (1.22 times).
- The 27 without one (7 training windows and the 20 stress windows from 15 July) match v14 step for step (largest
  difference of the per-step reward 0.0), among them the one-occupant buildings train_4 and train_7.
- Training, 30 scenarios: 0.007193 against 0.007328 (-1.85 %; 23 better, 7 identical); stress, 40 windows: 0.007239
  against 0.007302 (-0.86 %; 20 better, 20 identical). Paired statistics in docs/RESULTS_STATS.md.

Decision (docs/PREREGISTRATION_6.md and the screen rule above): round 6's H1, H2 and H4 passed and this check passes,
so **v15 = v14 + `empty_day` 1, `empty_h` 1.0** (`submission/V15_PARAMS.json`). Next: the reading rule in
docs/RESULTS_EXTERNAL.md, then the Kaggle submission (notebook `smartblabla` version 14, already run and checked).

## False alarms on work days (30 Oct, 06:26 by `date`; arithmetic, no runs)

The rule could fire on a real work day if nobody happens to arrive in the first hour. The generator of the shipped
buildings draws one or two occupants per zone (`run_floor_generator.py`, `DEFAULT_RANGES`); 10 of the 30 training
scenarios have one. Occupants (rooms of `zone_map.npy` times `occupants_per_zone`, scratch script occ_counts.py) over
the 43 training and generated buildings on disk: fewest 36 (building_7203, building_train_7), then 37, 38. With n
occupants the chance that nobody has come by 07:00 is (35/36)^(12n): 5e-6 for 36, 1.6e-3 for 19 (a building of 19
rooms with one occupant each, smaller than any we have). If it fires, the comfort period comes back with the first
arrival, on average 12 minutes later for 19 occupants, so the building floats for a few steps on a winter morning.
The 70 full-length development windows include all 10 one-occupant training scenarios; a false alarm there would show
as a change in a window without a holiday.

One assumption (code read 30 Oct, 06:35 by `date`): "somebody has come in" means the occupant count rose above the lowest value seen so
far. An episode that started during working hours, with people already in, would read as empty an hour later and run
the rest of its first day as unoccupied. All 172 scenario configs on disk start at 06:00, and the generator takes the
start from the weather preset (`scenario_generator.py`, `start_timestamp`), so we leave the rule as it is.

The hours the rule relies on (code read 30 Oct, 10:13 by `date`): the generator writes the occupancy window as fixed
numbers into every config (arrivals 6-12, departures 13-19; `scenario_generator.py`, config template) and the comfort
period from a schedule whose defaults are 06:00-19:00 (`morning_start_hour` 6, `evening_start_hour` 19). Every config
on disk uses these values, so a hidden building made by the same generator has them too. If one had a comfort period
starting before the first possible arrival, the rule would fire on work days as well and hand comfort back at the
first arrival, on average a few minutes later in buildings of 36 occupants or more (reasoning, not run).

## v16 development: the gain term on empty days (30 Oct, 04:16 by `date`; written before any run)

On a day run as empty, the comfort-mode flag stays on, so the zone model (Eq. 3 in the paper: gain term times the
comfort flag) expects the occupants' heat and the online fit learns its absence, until the next day. Option
`empty_cmv` 1 (`D:/SmartBuildings_data/frozen/zonal_v16dev.py`, a copy of the v14 file with this option only; off it
is the v14 code): on such a day the model's flag is 0. Screen against v15 (`results/holiday/ed1`) on the same ten
windows and run lengths: worth a full-length check if the mean change of the 30-day loss is at most -0.1 % and no
window is worse than +0.3 %; it runs after the full-length check of v15, and nothing about v15 waits for it.

What follows the screen (30 Oct, 06:38 by `date`; before any v16 run): if it is worth a full check, `empty_cmv` 1 runs
at full length on the 43 development windows with a weekday holiday (the other 27 are identical by construction: the
option acts only on a day run as empty), against v15's runs in `results/holiday/ed1_full`. A blind round, and then a
submission, follow only if the change of the summed loss over all 70 is at most -0.5 % with no window worse than
+0.3 %; a smaller gain goes into the notes as a refinement, and v15 stays.

## v16 screen result (runs 30 Oct 07:45-08:01; read 08:01 by `date`): no

`python -c "from sb import run_holiday; run_holiday.read_v16()"`; change of each window's 30-day loss against v15
(`results/holiday/ed1`), identity with v15 until 07:00 on the holiday exact (0.0) in all ten:

| window | change |
|---|---|
| train_7 duluth_jan15 | -0.025 % |
| train_1 chicago_jan15 | +0.007 % |
| train_2 sanfrancisco_jan15 | +0.030 % |
| train_8 dubai_jan15 | +0.131 % |
| train_1 fairbanks_1 | +0.011 % |
| train_7 singapore_6 | +0.015 % |
| train_5 fairbanks_5 | +0.008 % |
| train_7 denver_5 | +0.056 % |
| train_2 denver_8 | +0.011 % |
| train_2 phoenix_6 | +0.131 % |

Mean +0.038 %, worst +0.131 % (mark: mean at most -0.1 %, none worse than +0.3 %): not worth a full check. Switching
the gain term off on empty days makes things slightly worse in nine of ten windows; the online fit apparently
handles the missing occupant heat well enough on its own. v15 stays; `empty_cmv` stays off.

## Public leaderboard (read 30 Oct, 15:20 by `date`)

v15 scored 0.01035 in public, v14 0.01048: -1.24 % (training -1.85 %). The reading rule written at 07:50
(docs/RESULTS_EXTERNAL.md) expected 1-2 % below v14 if the hidden windows hold weekday holidays about as often as ours,
and reads anything below -0.5 % as confirming the rule there. v15 departs from v14 only on a work day that nobody
enters, and the scoring is deterministic, so the public windows hold such days. In the paper: Section 6.4 (one
sentence) and Appendix C.
