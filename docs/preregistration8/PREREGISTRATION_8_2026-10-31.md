# Pre-registration, round 8: a delay-aware heating net (written 31 Oct 2026, 13:03 by `date`; before any result of the screen of docs/HEATNET.md and before the scenarios are generated)

## What is tested

- v16: frozen `D:/SmartBuildings_data/frozen/zonal_v16f.py` (sha256
  af9c0d2bff35568b8b9f937ed5d49c63b821770e430086d2165bdb34acdb7b77, identical to the repository's frozen/zonal_v16f.py)
  with `submission/V16_PARAMS.json` (sha256 99c40761ef8e6f5c961f297e381284b9dd857a64e1c6b0d67aa2140516c6c572).
- sp1: the same file and parameters plus `safety_pred` 1: the heating safety net, like the cooling one, gives full
  effort only if the zone is still far below its band after the heat already in the pipe.

Why (docs/RESULTS_ROUND7.md, docs/HEATNET.md): v16 still cycles on heat alone in the smallest rooms during the morning
recovery; in the exploration (development data and the round-7 buildings, no longer blind) sp1 was lower or equal in
11 of 11 windows, by 1.1-4.6 % where the small rooms are.

## Scenarios (generated after this file is stamped; nothing has been run on them)

`python -m sb.make_round8 --out D:/SmartBuildings_data/round8` (sb/make_round8.py, sha256
588b209441d8a8f86e7c17ba44834668924f42ab5f27203be375d62010d37aeb; the procedure of sb/make_round7.py with new seeds
and windows): generator seeds 7901-7906 (spares 7907-7915, used in order when the generator's own check rejects a
building), raw full-size buildings, one window each, ten days (2880 steps) from a Sunday 06:00, 2023 ERA5 weather:

| slot | window | ten-day mean outside temperature |
|---|---|---|
| 1 | duluth_jan29 | -14.8 C (minimum -29.4 C) |
| 2 | helena_dec10 | -0.4 C (minimum -6.7 C) |
| 3 | chicago_jan08 | 1.6 C (minimum -6.9 C) |
| 4 | newyork_feb12 | 6.8 C (minimum -2.8 C) |
| 5 | seattle_dec10 | 6.0 C (minimum 0.6 C) |
| 6 | sanfrancisco_feb05 | 9.3 C (minimum 3.9 C) |

Slot 3 holds Martin Luther King Day (Monday 16 January) and slot 4 Presidents' Day (Monday 20 February); the holiday
rule acts there in both arms. No run of ours has used these seeds or windows. Runner: `python -m sb.run_round8`
(sb/run_round8.py, sha256 93f9d06638d2fca63f73f0b6075a9c83394ae86d4483a8ae79bd1607145d1988), both arms, first 2880
steps; after them, pid_water from the starter kit, unchanged, on the same six (descriptive, no hypothesis: it only
updates the count of unseen scenarios in which our final version is below the strongest official baseline, as
docs/BASELINE_R67.md did for rounds 6 and 7; added 31 Oct 14:39 by `date`, before stamping and before the screen
ended).

## Hypotheses and marks (read with `python -m sb.run_round8 --read`)

- H1: sp1's mean loss per step over the six is at least 0.3 % below v16's.
- H2: sp1's loss is at or below v16's in at least 5 of the 6.
- H3: no building's loss is more than 1 % above v16's.
- H4: sp1's comfort regret, summed over the six, is at most v16's.

Expectation (opinion): the gain comes from small, fast rooms, which two of the six round-7 buildings had; with one or
two such buildings the mean is -0.3 to -1.5 %, with none about -0.1 %, and H1 fails. Slot 1 is colder than any
full-size window run so far, where a heating net that waits for the pipe may recover later.

## Decision

This plan is stamped and run only if the screen of docs/HEATNET.md passes. sp1 becomes v17 if H1, H2 and H3 pass; a
failed H4 is reported with it. Then its Kaggle notebook (the v16 notebook with `safety_pred` 1, checked with
`sb/nbcheck.py`) and a submission, its reading rule written before it is sent. If H1, H2 or H3 fails, v16 stays and
the result is reported as it is. Either way the result goes into the paper.
