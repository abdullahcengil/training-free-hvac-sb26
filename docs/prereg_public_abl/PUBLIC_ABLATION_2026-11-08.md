# Does the transfer ablation hold on the hidden buildings? (plan written 08 Nov 2026, 15:44 by `date`, before any notebook is built or submitted)

## Why

Section 4.1 of the paper (Table 2, docs/TRANSFER_ABLATION.md) shows what carries the transfer, but on the twelve
full-size buildings of rounds 6 and 7, which we had already used; the Limitations say so. The public leaderboard scores
a policy on about a third of the hidden test set: buildings and five weather stations that nobody on our side has
seen. Submitting the same five variants there tests the section's claims on unseen buildings. Precedent: two ablations
of v11 were scored in public on 23 Oct for the appendix table of v11 ablations, "submitted only for this table, never
used for tuning". Knob probing on the public board ended on 8 Nov (docs/LEADERBOARD_PROBE.md: steps are now at the
board's display resolution), so these slots cost the ranking nothing.

## Design

Five Kaggle notebooks, each the frozen v16 file (`frozen/zonal_v16f.py`, SHA-256 `af9c0d2bff35568b...`) with
`submission/V16_PARAMS.json` and one change, the same arms as docs/TRANSFER_ABLATION.md:

| arm | change |
|---|---|
| nolearn | `rls 0`: the five numbers of each zone stay at their priors, and no disturbance is estimated |
| offset | the five numbers stay at their priors, the disturbance estimate is learned: the frozen v16 file with the `OffsetOnlyPolicy` subclass of `policies/zonal_v16_offsetonly.py` appended in the notebook's code cell |
| half | all five priors (`m2_prior`) halved, learning on |
| double | all five priors doubled, learning on |
| nodelay | `delay_comp 0`: plans and safety nets ignore the heat already in the pipe |

Built by `submission/lb/make_ablation.py`. Before submission each notebook must pass `sb/nbcheck.py` (its own code,
gateway wrapper included, gives the same actions as the repository's policy with the same settings for 576 steps on
building_train_1/atlanta_2; for `offset` the reference is `policies/zonal_v16_offsetonly.py`, which loads the frozen
file unchanged). A notebook that fails the check is not submitted. Submitted after the daily reset (9 Nov, 01:00
local), using all five of 9 Nov's slots; Kaggle description "Ablation of v16 (one change): ... For the paper's
test-set ablation table; not used for tuning." Reference: v16's public score 0.01031 (submitted 31 Oct).

## Measure

Each arm's public score divided by v16's 0.01031. One number per arm, so no interval; the board shows five decimals,
a resolution of about 0.1 % at this level.

## What each outcome means for the paper (fixed now)

1. Online learning carries the transfer on the hidden buildings too if `nolearn` scores at least 1.10 times v16
   (0.01134 or more). Below 1.05 times (under 0.01083), the paper must say that on the public windows learning is not
   what transfers. In between, the paper calls it a modest contribution there.
2. The five numbers matter beyond an offset there if `offset` scores at least 1.05 times v16 (0.01083 or more).
3. The priors need not be right there either if `half` and `double` each score within 5 % of v16 (0.00979 to
   0.01083).
4. The delay compensation matters for transfer there if `nodelay` scores at least 1.05 times v16; otherwise it stays
   "small", as in Table 2.

Every arm is reported in the paper whatever it shows (a public column in Table 2, or a sentence under it), and the
Limitations sentence on the ablation changes to match. No arm becomes a candidate or a final selection, and nothing is
tuned on these scores. A notebook that fails on Kaggle is reported as missing, fixed, and resubmitted on 10 Nov if
possible; 11 Nov is the last day for new paper content.

## Expectations, written before any score (opinion)

- nolearn: 1.5 to 3.5 times v16 (Table 2: 2.68). The public windows are heating-heavy, and without learning the comfort
  term rises in every zone whose prior fits badly.
- offset: 1.05 to 1.30 (Table 2: 1.16).
- half: 1.00 to 1.05; double: 0.97 to 1.06 (Table 2: 1.02 and 1.01).
- nodelay: 1.00 to 1.04 (Table 2: 1.02).

## Result

(empty until the scores come)
