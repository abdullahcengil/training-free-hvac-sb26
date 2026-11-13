# Do the delay handling and the slab node matter on the hidden buildings? (plan written 09 Nov 2026, 01:08 by `date`, before any notebook is built or submitted)

## Why

docs/TRANSFER_ABLATION2.md measured what the delay handling and the slab node are worth, but on twelve full-size
buildings we had already used (rounds 6 and 7). The public leaderboard scores about a third of the hidden test set:
buildings and five weather stations that we have never seen. As in docs/PUBLIC_ABLATION.md, the same variants submitted
there test the claims on unseen buildings. Knob probing on the public board ended on 8 Nov, so the slots cost the
ranking nothing.

## Design

Five Kaggle notebooks, each the frozen v16 file (`frozen/zonal_v16f.py`, SHA-256 `af9c0d2bff35568b...`) with
`submission/V16_PARAMS.json` and one change, the arms of docs/TRANSFER_ABLATION2.md:

| arm | change |
|---|---|
| nolag | `delay_comp 0`, `safety_pred 0`, `cool_hold 0`: the planner, the safety net and the cooling rule all ignore the delay |
| nohold | `cool_hold 0` |
| noslab | `mass_model 0`: the three-number zone model without the slab node |
| lag24 | `mass_n 24`: the slab follows the room two hours behind instead of four |
| lag96 | `mass_n 96`: eight hours behind |

Built by `submission/lb/make_ablation2.py`. Before submission each notebook must pass `sb/nbcheck.py` (its own code,
gateway wrapper included, gives the same actions as the frozen file with the same settings for 576 steps on
building_train_1/atlanta_2). A notebook that fails the check is not submitted. Submitted after the daily reset (10 Nov,
01:00 local), using the day's slots; Kaggle description "Ablation of v16 (one change): ... For the paper's test-set
ablation table; not used for tuning." If a notebook of the first batch (docs/PUBLIC_ABLATION.md, submitted 9 Nov) failed
on Kaggle, it takes the slot of `nohold`. Reference: v16's public score 0.01031.

## Measure

Each arm's public score divided by v16's 0.01031. One number per arm, so no interval; the board shows five decimals, a
resolution of about 0.1 % at this level.

## What each outcome means for the paper (fixed now)

1. All the delay handling together carries a large part of the transfer on the hidden buildings if `nolag` scores at
   least 1.10 times v16 (0.01134 or more). Below 1.05 times (under 0.01083), the paper must say that on the public
   windows the delay handling matters little. In between: a modest contribution there.
2. The slab node matters there if `noslab` scores at least 1.05 times v16 (0.01083 or more).
3. The slab's lag need not be exact there either if `lag24` and `lag96` each score within 5 % of v16 (0.00979 to 0.01083).
4. `nohold` is reported as it comes.

Every arm is reported in the paper whatever it shows (a public column in the table of these variants). No arm becomes a
candidate or a final selection, and nothing is tuned on these scores. A notebook that fails on Kaggle is reported as
missing; 11 Nov is the last day for new paper content.

## Expectations, written before any score (opinion)

- nolag: 1.02 to 1.15. In docs/TRANSFER_ABLATION2.md it was 1.137, but four of twelve buildings carried that.
- nohold: 1.00 to 1.02. The public gain of v16 over v15 was only 0.4 %.
- noslab: 1.05 to 1.30 (1.164 there; 2.05 for v11 in training).
- lag24: 0.98 to 1.02; lag96: 1.00 to 1.04 (0.992 and 1.018 there).

## Result

(empty until the scores come)
