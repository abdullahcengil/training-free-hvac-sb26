# v15 candidates for full-size buildings (25 Oct 2026, about 21:40; written before any candidate run)

## Diagnosis 2: cold weather on full-size buildings (docs/BIG_BUILDINGS.md)

v14 on building 7407 in Chicago, full size (`results/bigbld_diag/v14_7407_chicago_full_d8.npz`, Sunday 06:00 to
Monday 12:00 of the second week): the comfort loss of that scenario sits almost all on the Monday morning after the
weekend (day 8: 0.0099 of comfort loss per step against 0.0005 on the scaled building; worst step -0.52 at 05:55).
The zones that miss are the largest rooms (847-887 m2, against 222 m2 mean in the scaled building), all with the same
2 m3/s box. They float to 9.9-11.4 C over the weekend, start recovering at about 00:40 on Monday and reach only
16.3 C by 06:00 and 20.6 C by noon.
- The night glide (Eq. 2 in the paper) assumes the zone's one-step heating rate at the recovery airflow, clipped to
  3 K/h, times 0.66: 2 K/h. In these rooms the one-step rate of the model is 1 K/step (the air jumps), but the
  sustained rate is set by the slab: the air settles about (g q + c + b (T_oa - T_m)) / (lam + b) = 3.7 K above the
  slab and the slab follows at a 48-step lag, about 0.08 K/step by the model and 0.056 K/step observed (0.7 K/h).
  The recovery therefore starts about three times too late.
- The model's gain sits at its lower bound (`m2_lo` g = 0.05) in the two largest rooms (g falls with room area,
  correlation -0.65 over the 36 zones), so the model also overrates what the box can do there.
- In the training buildings the sustained rate is above the 3 K/h clip (boxes are large for their rooms), which is
  why no training run showed this; earlier screens found that starting recoveries earlier everywhere costs more
  energy than the comfort it buys (`start_learn`, `glide_safety`; docs/TUNING_LOG.md, 23 Oct).

## Candidates (one or two options on top of v14; v14 is option-off bit for bit)

- **A, `glide_sus` 1**: the night glide uses the slower of the zone's one-step rate and its slab-limited sustained
  rate, lam / (lam + b) x (T_eq - T_m) / mass_n with T_eq - T_m = (g q + c + b (T_oa - T_m) + dhat) / (lam + b) at the
  recovery airflow, whenever the target lies above T_eq (the zone cannot get there on the fast air dynamics alone).
  The cooling glide gets the same rule with the pull-down airflow. Zones whose box is large for the room are unchanged.
- **B, `m2_lo` g 0.02** (from 0.05): the gain's lower bound; a parameter, no code.
- **C = A + B.**
- **D = A + a 48-hour glide horizon** (`glide_h` 48; v14: 24): a slab-limited zone can need more than a day after a
  weekend float; zones whose rate is at the clip keep the deepest floor, so only slow zones change.

## Screen (rule fixed now)

Full-size development set `D:/SmartBuildings_data/bigdev` (`sb/make_bigdev.py`): the raw round-1 YAMLs unscaled
(7001, 7002, 7003, 7005, 7007, 7008; 7009 and 7004 are rejected at full size by the generator's own check), each in
one cold and one hot stress window, 12 scenarios, first 2880 steps; reference v14 (`results/bigdev/v14`).
- A candidate passes if its mean loss over the 12 is at least 1 % below v14's and no scenario is more than 2 % worse.
- Of the passing candidates the lowest mean goes on; a simpler one (fewer options) is preferred if within 0.3 % of it.

## Full check (rule fixed now)

The chosen candidate becomes v15 only if all three hold:
1. 30 training scenarios, full length: mean at most 0.3 % above v14's 0.007328;
2. 40 stress scenarios, full length: mean not above v14's 0.007302;
3. a full-size held-out set, frozen before any run (round-2 raw YAMLs at full size, new windows, written down and
   timestamped before it is generated): mean below v14's.
Then `sb/nbcheck.py` on its notebook, and it is submitted.

## The full-size held-out set (fixed 25 Oct, 21:47, before it is generated or any run)

`sb/make_bigtest.py`, out `D:/SmartBuildings_data/bigtest`: the raw round-2 YAMLs at full size (round 2 was opened on
17 Oct; its buildings have never been simulated unscaled), each in one cold and one hot stress window, first 2880
steps (10 days), v14 against the chosen candidate:

| building | cold | hot |
|---|---|---|
| 7111 | duluth_jan15 | dubai_jul15 |
| 7102 | chicago_jan15 | houston_jul15 |
| 7112 | helena_jan15 | miami_jul15 |
| 7104 | newyork_jan15 | lasvegas_jul15 |
| 7105 | seattle_jan15 | newyork_jul15 |
| 7106 | chicago_jan15 | seattle_jul15 |

A building the generator rejects at full size is replaced by the next spare in this order: 7101, 7103, 7107, 7108,
7109, 7110 (same windows). Reading (item 3 of the full check): the candidate's mean over the 12 must be below v14's;
also reported, not used for the decision: better/worse count, cold and hot means, comfort.

Frozen copy of this plan as committed at 21:47 (58c47e6): `docs/preregistration6/BIGDEV_2026-10-25.md`, its
OpenTimestamps proof next to it (two calendars; only the hash left the machine). The two clock times in the
headings were corrected afterwards (they had been written 15-20 minutes ahead).

## Stopped 25 Oct, 21:58 (the PC is off overnight)

Nothing of the screen has run yet. Done: v15 candidate file `frozen/zonal_v15dev_a.py` (built by `sb/make_v15f.py`;
defaults are v14; the slab-limited rate reproduces the hand value 0.0373 K/step for the 887 m2 room and leaves a
training-size room at the 0.25 clip); the held-out set generated and hashed (`docs/preregistration6/BIGTEST_MANIFEST.txt`);
v14 on 2 of the 12 development scenarios (7001 chicago_jan15 0.01714, 7008 seattle_jan15 0.00342). Runs that were
cut off wrote nothing and are redone. To continue: `bash sb/resume_v15.sh` (v14 reference, then the screen read by
`sb/v15_screen_eval.py`, then the full check by `sb/v15_full.sh`; estimated 12-14 hours of machine time in all).

## Resumed 27 Oct, 11:19 (`sb/run_1027.sh`, three simulations at a time)

One queue: v14's reference on the development set, the screen, its reading, the held-out set, then (only if item 3
passes) the training and stress runs, then the rest of the tank measurement. A procedural change written before any
candidate result exists: the screen applies its 2 % rule as results come in (`sb/jobs_screen.py`); once one scenario
of a candidate is more than 2 % worse than v14, its remaining scenarios are skipped, since it can no longer pass. The
held-out set runs before the training and stress sets, and those run only if the candidate passes item 3.

## 27 Oct, 11:44: jobs start by free memory (`sb/pipeline_v15.py`, `sb/memsched.py`)

Three full-size simulations did not fit in memory: the queue of 11:19 was stopped when free commit memory fell to
1.6 GB (runs cut off wrote nothing, so nothing was lost or half-written). Measured alone (peak commit after loading):
7002 3.13 GB, 7003 4.04, 7007 4.68, 7105 6.38, i.e. about 0.86 GB + 5.1 kB per interior grid cell; with the other
programs open about 7 GB of commit is free. Windows grows its system-managed pagefile when commit runs out (tested
11:47: limit 21.5 -> 23.8 GB with 3 GB committed and 1.3 GB free), so the scheduler has Windows grow it before a
start and treats RAM as the limit (about 40 % of a run's commit is touched); still at most three runs at once. The
queue is now a function of the results on disk and can be restarted at any point without stopping running
simulations; each job starts only if its estimated memory fits.
- Phase 1: v14's reference and the screen, scenario by scenario (the 2 % rule applied as results come in, as written
  at 11:19). Beside it: the rest of the tank measurement, then the training and stress runs of the candidate that leads
  the screen so far. Those are used only if the screen's rule later chooses that candidate; the screen's reading does
  not depend on them.
- Phase 2: the held-out set (v14 and the chosen candidate) and the candidate's training and stress runs side by side.
  This replaces the order written at 11:19 (held-out set first; training and stress only if item 3 passes): all three
  items are now run before any is read. Each item's rule is unchanged; `sb/v15_full_eval.py` reads items 1-3, and the
  notebook is built and checked only if all three pass.

## Screen results (27 Oct, as they come; read with `python -m sb.v15_screen_eval`)

- **A (slab-limited glide) fails on its first scenario**, 7001 chicago_jan15: 0.01714 -> 0.02023 (+18.0 %; the rule
  fails a candidate at +2 %). Comfort regret falls by 94 % (0.00086 -> 0.00005), but energy plus carbon rises by 24 %
  (0.01628 -> 0.02018). Per day (`results/bigdev/*/building_7001__chicago_jan15.npy`): the extra loss is on the second
  Sunday, +0.0039 of the run's mean, when the slower predicted rate makes the large rooms start their recovery about a
  day before Monday 06:00; Monday gives back 0.0011 (comfort and the warm-up v14 does on Monday morning). Reading
  (opinion): in these rooms, being warm on time after a cold weekend costs about three times what the late recovery
  costs in comfort under this reward; v14's late recovery is the cheaper choice. Its remaining 11 scenarios are skipped
  (rule of 11:19).
- **C (A + lower gain bound) and D (A + 48-hour horizon) fail on the same scenario**: 0.02039 (+19.0 %) and 0.02046
  (+19.4 %). Both remove the Monday comfort regret (0.00086 -> 0.00000 and 0.00002) and raise energy plus carbon by
  25-26 %, the same mechanism as A. Every candidate with the slab-limited glide is out after one scenario.
- **B (lower gain bound only)**, first scenario: 0.01713 against 0.01714 (-0.06 %); it changes only the last day
  (comfort -0.00007, energy +0.00004). It goes on through the 12 scenarios; to pass it needs a mean 1 % below v14's.
- Queue, 12:16: the last step (reading items 1-3, then the notebook and its check) runs as a job of the queue, so the
  notebook check counts as one of the three simulations; behind all of v15 the queue runs the replication of the size
  test (docs/BIG_BUILDINGS.md, its rule committed at 12:13 before any of its runs).
- Correction to the unit check of 25 Oct ("leaves a training-size room at the 0.25 clip"): that held for one room. On
  train_1 fairbanks_1 (first 2880 steps) candidate A departs from v14 at step 772 and loses 10.4 % (0.05725 vs
  0.05185), so the slab-limited rate also binds in shipped-size rooms in deep cold (docs/BIG_BUILDINGS.md, public-board
  test, 12:33). A would not have passed the training item either.

## Screen decided (27 Oct, 14:16): no candidate passes; v14 stays

| candidate | scenarios run | mean vs v14 (0.01461 over the 12) | reading |
|---|---|---|---|
| A slab-limited glide | 1 (7001 chicago_jan15) | +18.0 % | fails (a scenario more than 2 % worse) |
| B lower gain bound | 12 | 0.01462, +0.06 %; better in 2, worst +0.25 % | fails (mean not 1 % below) |
| C = A + B | 1 | +18.9 % | fails |
| D = A + 48 h horizon | 1 | +19.3 % | fails |

By the rule of 25 Oct no candidate goes to the full check, so there is no v15 and nothing is submitted. Reading
(opinion): the only change that moved the full-size cold scenarios (being warm on time after a weekend) costs more
energy than the comfort it buys, and the lower gain bound alone changes nothing that matters. What is left at full
size is mostly the cooling bill in hot weather (docs/BIG_BUILDINGS.md, where the extra loss falls), which v14 already
runs at its model's cheapest point. The queue goes on with the replication of the size test, candidate A's Monday
trace (figure) and the rest of the tank measurement.
