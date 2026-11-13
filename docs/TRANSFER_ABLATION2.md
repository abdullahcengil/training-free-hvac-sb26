# What carries the transfer, part 2 (plan written 08 Nov 2026, 19:05 by `date`, before any run)

## Why

An AI review of the paper (Argon 4, 8 Nov) raised three points that the first ablation (docs/TRANSFER_ABLATION.md,
Table 2) cannot answer:

1. The `no delay compensation` arm turns off only the planner's look-ahead; the delay-aware safety net
   (`safety_pred`) and the rule against cooling right after heating (`cool_hold`), both responses to the same lag,
   stay on. So Table 2 may understate what the delay finding is worth, and the paper's explanation (that `cool_hold`
   already blocks the relay) is untested.
2. The slow slab node stays on in every arm of Table 2, so its contribution to transfer is not isolated.
3. The slab follows the room with a fixed lag of 48 steps (four hours, `mass_n`), set from the scenario files and not
   identified online; the review asks how much a wrong lag would cost in buildings of other construction.

## Design

v16 (frozen/zonal_v16f.py, SHA-256 `af9c0d2bff35568b...`, submission/V16_PARAMS.json) with one change at a time, on
the same twelve full-size buildings, windows and steps as Table 2 (rounds 6 and 7, first 2880 steps), against v16's
existing runs there (`results/round6h/v16`, `results/round7/chm`). These buildings are no longer blind: post hoc and
descriptive, and every arm is reported, whatever it shows.

| arm | change |
|---|---|
| nolag | the planner, the safety net and the cooling rule all ignore the delay: `delay_comp 0`, `safety_pred 0`, `cool_hold 0` |
| nohold | `cool_hold 0` only |
| noslab | `mass_model 0`: the three-number zone model without the slab node (as in v10), learning on |
| lag24 | `mass_n 24`: the slab follows the room two hours behind instead of four |
| lag96 | `mass_n 96`: eight hours behind |

Script: `sb/run_transfer_abl2.py` (60 runs, three at a time); log `D:/SmartBuildings_data/transfer_abl2.log`; read
with `python -m sb.run_transfer_abl2 --read`. Measures as in Table 2: ratio of mean losses (arm / v16) over the 12
scenarios with a 95 % bootstrap interval over scenarios (10,000 resamples), the number of scenarios in which the arm
is worse, and the comfort term.

## What each outcome means for the paper (fixed now)

1. The delay finding carries a large part of the transfer if `nolag` is at least 10 % worse than v16, its interval
   lies above 1, and it is worse in at least 10 of 12 scenarios. If it is less than 5 % worse, the paper must say that
   the delay matters little for transfer in these buildings. Between 5 and 10 %: a modest contribution.
2. The paper's explanation for Table 2's small `no delay compensation` effect (the lag's other responses overlap) holds
   if `nolag` is worse than v16 by at least twice the 2 % of `no delay compensation` (ratio of means at least 1.04);
   otherwise the paper drops that explanation. `nohold` is reported beside it.
3. The slab node matters for transfer if `noslab` is at least 5 % worse with its interval above 1.
4. The fixed four-hour lag need not be exact if `lag24` and `lag96` are each within 5 % of v16 on the mean and no
   scenario is worse by more than 15 %; otherwise the paper says that the lag must match the building's construction
   and is a limitation.

No arm becomes a candidate; nothing is tuned on these runs (v16 is final).

## Expectations, written before the runs (opinion)

- nolag: 10 to 40 % worse; without any delay handling the relay of rounds 1 and 7 should return in small, fast rooms.
- nohold: 2 to 8 % worse, mostly in the two round-7 buildings with small rooms (New York, Chicago).
- noslab: 5 to 30 % worse, mostly in cold windows (the slab node was the largest gain of round 5).
- lag24, lag96: each within 5 %; the learned coupling should absorb part of a wrong lag.

## Result (runs 08 Nov 19:05-23:32; read 08 Nov 2026, 23:37 by `date`)

`python -m sb.run_transfer_abl2 --read` and `--days` (output `D:/SmartBuildings_data/transfer_abl2_read.txt`). All 60 runs
finished without a crash. Mean loss per step of v16 on the twelve buildings: 0.014265; comfort term 0.00048. "Same": the
run is identical to v16's step for step (the switched-off rule never fired).

| arm | mean loss | ratio of means (95 % CI) | worse / same / better | per-scenario change | comfort term |
|---|---|---|---|---|---|
| nolag | 0.016223 | 1.137 (1.026-1.302) | 12 / 0 / 0 | +0.06 to +119 %, median +1.0 % | 0.00173 |
| nohold | 0.014957 | 1.048 (1.000-1.124) | 3 / 9 / 0 | +7.3, +10.5, +27.0 %, the rest identical | 0.00099 |
| noslab | 0.016603 | 1.164 (1.085-1.269) | 12 / 0 / 0 | +4.1 to +42.4 %, median +13.6 % | 0.00189 |
| lag24 | 0.014147 | 0.992 (0.977-1.002) | 5 / 0 / 7 | -4.7 to +1.2 % | 0.00040 |
| lag96 | 0.014520 | 1.018 (1.008-1.032) | 12 / 0 / 0 | +0.5 to +6.1 % | 0.00062 |

The rules written before the runs give:

1. The delay finding carries a large part of the transfer: `nolag` is 13.7 % worse (at least 10 %), its interval lies
   above 1, and it is worse in 12 of 12. The rise is concentrated, however: four buildings carry it (New York, October,
   +119 %; Duluth, December, +58 %; Chicago, December, +48 %; New York, January, +19 %); in the other eight the change is
   at most +2 %. The paper reports both.
2. The overlap explanation for Table 2's small `no delay compensation` effect holds: 1.137 against the mark of 1.04.
   `nohold` is 1.048 and acts in only three buildings (the rule never fires in the other nine).
3. The slab node matters for transfer: `noslab` is 16.4 % worse and its interval lies above 1 (worse in 12 of 12).
4. The fixed four-hour lag need not be exact: `lag24` 0.992 and `lag96` 1.018, each within 5 % of v16, and no scenario
   worse by more than 15 % (worst +6.1 %).

All four arms that had an expectation came out within it. `lag24` is 0.8 % below v16 on the mean, an interval that
includes 1; as the plan says, no arm becomes a candidate and v16 stays final.
