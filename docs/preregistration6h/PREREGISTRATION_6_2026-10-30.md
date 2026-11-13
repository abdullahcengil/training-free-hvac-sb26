# Pre-registration, round 6: empty holidays (30 Oct 2026, 02:18 by `date`; before the scenarios are generated)

## What is tested

- v14: frozen `D:/SmartBuildings_data/frozen/zonal_v14f.py` (sha256 0a31d331ee3dd867b73577f1f8c0d4624725db847aa9ed80b3a416c186232b13)
  with `submission/V14_PARAMS.json` (sha256 02b1695f5e55c771f12767f4106db2b85e4736aece3b3e6d575a2654695c6ebf).
- ed1: the same file and parameters plus `empty_day` 1, `empty_h` 1.0 (docs/HOLIDAY.md): if nobody has come in one
  hour after the comfort period starts, the rest of the day runs as unoccupied, the setbacks planning towards the next
  work day; if anybody comes in later, the comfort period resumes. No code changes.

Why (simulator code, docs/HOLIDAY.md): on US federal holidays the occupancy model keeps everybody away, while the
setpoint schedule, built without holidays, stays in comfort mode; the comfort term is zero when nobody is in.

## Scenarios (generated after this file is stamped; nothing has been run on them)

`python -m sb.make_round6h --out D:/SmartBuildings_data/round6h` (sb/make_round6h.py, sha256
c2317638ae5fa7ff777c8e2ba05a180326aa0ab66c0369d7a57b9228a41c0d2e): generator seeds 7701-7706 (spares 7707-7715,
used in order when the generator's own check rejects a building), raw full-size buildings, one window each, ten days
(2880 steps), each holding one weekday US federal holiday of 2023 and work days after it:

| slot | window | holiday |
|---|---|---|
| 1 | houston_may28 | Memorial Day, Monday 29 May |
| 2 | miami_jul02 | Independence Day, Tuesday 4 July |
| 3 | dubai_sep03 | Labor Day, Monday 4 September |
| 4 | newyork_oct08 | Columbus Day, Monday 9 October |
| 5 | chicago_nov19 | Thanksgiving, Thursday 23 November |
| 6 | duluth_dec17 | Christmas, Monday 25 December |

No run of ours has used these seeds or windows. Runner: `python -m sb.run_round6h` (sb/run_round6h.py, sha256
bc718ca75199fc4b93bdb0269db55c617b34437d57ff80b09283598f85732a80), both arms, first 2880 steps.

## Hypotheses and marks (read with `python -m sb.run_round6h --read`)

- H1: ed1's mean loss per step over the six is at least 0.5 % below v14's.
- H2: ed1's loss is below v14's in at least 5 of the 6.
- H3: ed1's comfort regret, summed over the six, is at most 1.5 times v14's.
- H4: the two arms' per-step rewards are identical until 07:00 on each holiday.

Expectation (from the screen, opinion): ten-day windows with one holiday, so about three times the screen's 30-day
changes, -1 to -10 % per window.

## Decision

ed1 becomes v15 if H1, H2 and H4 pass and the full-length development check of docs/HOLIDAY.md (all 70 windows, mean
at least 0.3 % below v14, none worse than +1 %) passes; a failed H3 is reported with it. Then `sb/nbcheck.py` on its
notebook (`bash sb/make_v15hol_submission.sh`) and a Kaggle submission, its reading rule written before it is sent.
If H1, H2 or H4 fails, v14 stays and the result is reported as it is.

## Development evidence before this round (docs/HOLIDAY.md)

Screen on ten development windows with a holiday (shipped size, from the start to two work days after the holiday):
better in 10 of 10, mean change of the 30-day loss -1.60 % (from -0.28 % to -3.39 %), comfort regret 1.09 times
v14's over the runs.

## Note

`sb/make_round6.py` (a deep-cold round 6 prepared on 30 Oct for the v15 heating candidates) was never run and has no
rules: no candidate passed its screen (docs/V15COLD.md). This file replaces it as round 6.
