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

## Result

(empty until the runs end)
