# Pre-registration, round 7: no cooling right after heating, with a smaller heating margin (written 30 Oct 2026, 23:43 by `date`; before any result of the screen of docs/CHATTER.md and before the scenarios are generated)

## What is tested

- v15: frozen `D:/SmartBuildings_data/frozen/zonal_v14f.py` (sha256 0a31d331ee3dd867b73577f1f8c0d4624725db847aa9ed80b3a416c186232b13)
  with `submission/V15_PARAMS.json` (sha256 de24f579c58f331950d29bafae0a17d36b025ea39b10e18d3b23a2f2667cf034).
- chm: `D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py` (sha256
  af9c0d2bff35568b8b9f937ed5d49c63b821770e430086d2165bdb34acdb7b77; built by sb/make_v16ch.py, sha256
  ef64d3d37479654649b2492cb0db62dd11162ffcc931a9a8587c55f613fff7d4, from zonal_v14f.py; with cool_hold 0 it computes
  exactly what v15 computes, checked on 576 steps) with V15_PARAMS plus `cool_hold` 2 and `margin_heat` 0.30: a zone
  asked for heat in one of the last two steps is not cooled, and the controller aims 0.30 K instead of 0.40 K above
  the lower comfort bound when it heats.

Why (docs/HEATLESS.md, docs/CHATTER.md): the smaller margin lowered the loss by 1.63 % in six cold full-size windows,
but in one training window it tipped a fast zone into a cycle of full heating and full cooling; cool_hold removes the
cycle (development scenarios only).

## Scenarios (generated after this file is stamped; nothing has been run on them)

`python -m sb.make_round7 --out D:/SmartBuildings_data/round7` (sb/make_round7.py, sha256
923f4f3379e602a9f4d23fddaa1ef7e0d5d2cfac0eb701bf120707d4528cf1e3; seeds and windows unchanged since commit 8671143,
30 Oct 17:53, before any result of the margin or cool-hold lines): generator seeds 7801-7806 (spares 7807-7815, used
in order when the generator's own check rejects a building), raw full-size buildings, one window each, ten days (2880
steps) from a Sunday 06:00, 2023 ERA5 weather:

| slot | window | ten-day mean outside temperature |
|---|---|---|
| 1 | duluth_feb19 | -10.6 C (minimum -22.9 C) |
| 2 | helena_feb19 | -6.5 C (minimum -26.8 C) |
| 3 | newyork_jan29 | 0.8 C (minimum -16.5 C) |
| 4 | chicago_dec03 | 2.8 C |
| 5 | seattle_nov26 | 5.1 C |
| 6 | sanfrancisco_mar05 | 9.9 C |

Slots 1 and 2 hold Presidents' Day (Monday 20 February); the holiday rule acts there in both arms. No run of ours has
used these seeds or windows. Runner: `python -m sb.run_round7` (sb/run_round7.py, sha256
d3e5f6e33e6f131d60baa95894f212e3f2723362ee0f47d6baa3de022ea1a297), both arms, first 2880 steps.

## Hypotheses and marks (read with `python -m sb.run_round7 --read`)

- H1: chm's mean loss per step over the six is at least 0.5 % below v15's.
- H2: chm's loss is below v15's in at least 4 of the 6.
- H3: no building's loss is more than 2 % above v15's.
- H4: chm's comfort regret, summed over the six, is at most 1.5 times v15's.

Expectation (opinion): the smaller margin gave -1.2 to -3.2 % in mild January windows at full size; slots 1 and 2
are colder than any full-size window run so far, where heating less may cost comfort, and slot 6 needs little heat;
so a mean of -0.5 to -1.5 %, and H1 may fail.

## Decision

This plan is stamped and run only if the screen of docs/CHATTER.md passes. chm becomes v16 if H1, H2 and H3 pass; a
failed H4 is reported with it. Then `bash sb/make_v16_submission.sh` (notebook and `sb/nbcheck.py`) and a Kaggle
submission, its reading rule written before it is sent. If H1, H2 or H3 fails, v15 stays and the result is reported
as it is. Either way the result goes into the paper.
