# A delay-aware heating net (written 31 Oct 2026, 13:00 by `date`; before any run of the screen below)

## Why

Round 7 (docs/RESULTS_ROUND7.md) showed that v16 still cycles on heat alone in the smallest rooms during the morning
recovery: the heating safety net gives full effort on the lagged reading, the zone overshoots by several kelvin, falls
back by itself, and the net fires again. v16 makes only the cooling net delay-aware (`safety_pred 2`). The existing
option `safety_pred 1` makes the heating net delay-aware too: it fires only if the zone is still far below its band
after the heat already in the pipe (frozen/zonal_v16f.py, lines 814-819). No code changes.

## Exploration (no decision; sb/run_explore_sp1.py, runs 31 Oct 12:00-13:00, read 13:00 by `date`)

v16 + safety_pred 1 against v16's runs:

| set | scenario | v16 | sp1 | change |
|---|---|---|---|---|
| round-7 buildings (no longer blind) | 7804 Chicago Dec | 0.02253 | 0.02151 | -4.56 % |
| | 7803 New York Jan | 0.01381 | 0.01366 | -1.09 % |
| scaled twin (163 small rooms) | 7003 Duluth Jan | 0.00543 | 0.00523 | -3.60 % |
| cold full-size development | 7001 Chicago | 0.01627 | 0.01624 | -0.15 % |
| | 7002 Helena | 0.00895 | 0.00894 | -0.09 % |
| | 7003 Duluth | 0.00506 | 0.00506 | 0.00 % |
| | 7005 Chicago | 0.01194 | 0.01193 | -0.05 % |
| | 7007 New York | 0.01000 | 0.01000 | -0.05 % |
| | 7008 Seattle | 0.00319 | 0.00319 | -0.11 % |
| training, full length | train_8 atlanta_1 | 0.00478 | 0.00475 | -0.74 % |
| | train_1 fairbanks_1 | 0.04438 | 0.04428 | -0.24 % |

Lower in 10 of 11, equal in one, comfort lower or equal in every one. The gain is above 1 % where the small rooms are
(Chicago and New York of round 7, the scaled Duluth twin), so by the standing rule a candidate may follow.

## Candidate and screen (fixed now, before any screen run)

**sp1** = submission/V16_PARAMS.json + safety_pred 1, with `D:/SmartBuildings_data/frozen/zonal_v16f.py` (sha256
af9c0d2b..., unchanged). No other value or option is tried on these data.

Screen (`python -m sb.run_screen_sp1`, restartable, three simulations at most), four sets against v16's existing runs:
- **S**: the five cold windows of the scaled twins (`bigdev_scaled`, January 15), 2880 steps, against
  `results/chatter/s_chm`.
- **F**: the six cold full-size development windows, 2880 steps, against `results/chatter/f_chm`.
- **H**: the six hot full-size development windows (July 15), 2880 steps, against `results/chatter/h_chm`.
- **T**: the 30 shipped training scenarios at full length (8640 steps), against `results/chatter/t_chm`.
Runs the exploration already made with the same file and settings are reused (deterministic): all of F, the Duluth
window of S, and atlanta_1 and fairbanks_1 of T. So F is not new evidence, and S and T are partly seen.

Reading rule (fixed now): sp1 goes on to a blind round (round 8, its plan stamped before its buildings are generated)
only if all four hold:
- S: no window more than 2 % worse than v16 (mean and comfort reported);
- F: mean at most 0.1 % above v16, no window more than 1 % worse;
- H: mean at most 0.1 % above v16, no window more than 1 % worse;
- T: total at most 0.1 % above v16, no scenario more than 2 % worse.
Otherwise v16 stays and the result is reported (docs, paper appendix). The screen asks for no gain: the gain is the
blind round's question, on new buildings.

## Screen result (read 31 Oct 15:32 by `date`; `python -m sb.run_screen_sp1 --read`)

| set | windows | v16 | sp1 | change | better | worst window | rule |
|---|---|---|---|---|---|---|---|
| S, scaled cold | 5 | 0.008842 | 0.008803 | -0.44 % | 2 | +0.01 % | none above +2 %: pass |
| F, full-size cold | 6 | 0.009235 | 0.009228 | -0.08 % | 5 | +0.00 % | mean at most +0.1 %, none above +1 %: pass |
| H, full-size hot | 6 | 0.019387 | 0.019387 | +0.00 % | 0 | +0.00 % | mean at most +0.1 %, none above +1 %: pass |
| T, training, full length | 30 | 0.007164 | 0.007157 | -0.10 % | 13 | +0.02 % | total at most +0.1 %, none above +2 %: pass |

All four hold, so sp1 goes to round 8 (docs/PREREGISTRATION_8.md, stamped before its buildings are generated).
Comfort was unchanged in every hot and training window (five decimals). As expected, sp1 differs from v16 only where
the heating net would fire, so the gain sits in the small rooms (the scaled Duluth twin, -3.6 %); elsewhere the two
are nearly identical.
