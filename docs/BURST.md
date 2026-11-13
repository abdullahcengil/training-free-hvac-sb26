# Skipping air-handler steps when the zones can wait (rules written 8 Nov 2026, 00:55 by `date`; before any run)

For the second, public-tuned Kaggle selection only (docs/LEADERBOARD_PROBE.md); not part of the paper.

## Why

While an air handler runs, every zone under it gets at least the damper floor of air, and that air is at least 30 %
outside air (recirculation is capped at 0.7). In cold weather the zones that asked for nothing are cooled by it and
must be reheated later; in occupied hours in Fairbanks, zones at the damper floor carried 5-24 % of the outside-air
load (docs/TUNING_LOG.md, 23 Oct). v16 runs a handler at every step in which any of its zones asks for heat. If the
zones that ask can wait one step and still stay inside the comfort band, the handler can skip that step: no outside
air reaches the idle zones, the fan draws nothing, and the heat follows one step later. Never two skips in a row, so
this changes timing, not the temperatures aimed at.

## What

`sb/make_v16burst.py` builds `policies/zonal_v16burst.py` = the frozen v16 file plus `skip_ahu` and `skip_k`
(0.05 K). skip_ahu 1: heating-only handlers, in comfort time, when every zone that asked for heat stays at least skip_k
above the comfort band's lower edge at k+2 without heat and none is far below; 2: also cooling-only handlers (zones
stay skip_k below the upper edge) and mixed ones when both hold. 0: off.

## Runs (`sb/run_burst.py`, at most 3 at a time)

The 12 full-size development windows of the tuned check (6 cold, 6 hot; `results/bigdev` scenarios), 2880 steps:
- B = c8fhm40 (best public, 0.01004): V16_PARAMS + glide_safety 1.20, glide_floor -26, margin_heat 0.20,
  f_heat_rec 0.45, f_heat_max 0.40.
- S1 = B + skip_ahu 1; S2 = B + skip_ahu 2.

## Checks and reading rule (fixed now)

- K1: skip_ahu 0 gives v16's rewards exactly (288 steps of the first round-7 building).
- An arm goes to the leaderboard if (1) its mean loss over the 12 windows is at least 1 % below B's, (2) its comfort
  term is at most 1.5 times B's, and (3) it is worse than B in at most 2 of the 12 windows. If both pass, both go.
- Reported whatever the result.

## Result (read 08 Nov 04:09, `python -m sb.run_burst read`; runs 00:57-04:08)

| | mean loss (12 windows) | vs B | comfort vs B | worse than B in |
|---|---|---|---|---|
| B (c8fhm40) | 0.01413 | | | |
| S1 (skip_ahu 1) | 0.01413 | +0.00 % | 1.00x | 1 of 12 |
| S2 (skip_ahu 2) | 0.01413 | +0.00 % | 1.00x | 1 of 12 |

K1 passed (identical rewards, 00:57). Every window's ratio to B rounds to 1.0000; the one "worse" window (Duluth) moves
the comfort term from 8.2 to 8.3 x1e-5. **Both arms fail rule (1)** (need at least 1 % below B), so neither goes to
the leaderboard. Why (likely, not measured step by step): the controller asks for heat only when a zone is predicted
below its aim, which sits 0.20 K above the band's lower edge, so a handler with a heat request nearly always has at
least one requesting zone that would end below the edge + 0.05 K at k+2 without heat; the skip condition, which needs
every requesting zone of the handler to stay above that line, almost never holds. Loosening it (skipping zones that
would leave the band) trades comfort for energy, which the rule against comfort losses was written to exclude; not
pursued.
