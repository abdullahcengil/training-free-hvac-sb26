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

## Notebook check (08 Nov 2026, 15:47 by `date`)

`submission/lb/make_ablation.py` built `submission/lb/v16abl_<arm>.ipynb` and `abl_<arm>_PARAMS.json`. All five pass
`sb/nbcheck.py` (log `D:/SmartBuildings_data/nbcheck_v16abl.log`): identical actions for 576 steps on
building_train_1/atlanta_2. Total rewards over those steps: v16 -0.390830 (its own submission notebook, same check),
nolearn -0.408158, offset -0.389437, half -0.406849, double -0.409135, nodelay -0.407186. Each differs from v16, so
each change acts in the notebook.

Kaggle notebook versions saved 08 Nov 2026, after 15:48 and before 15:58 by `date` (Save & Run All; not yet submitted): 46 nolearn, 47 offset,
48 half, 49 double, 50 nodelay (version names "abl <arm>: ..."). Version 49 was imported twice: a mistyped version name
went into the editor the first time, and the second import replaced the whole draft before saving. Each version's
code is checked on its Kaggle page before submission.

Kaggle check (08 Nov 2026, 16:12 by `date`): versions 46-49 ran without error (12 min 59 s, 12 min 37 s, 13 min 10 s,
14 min 22 s); 50 was still running. The saved code of 48, 49 and 50 shows each arm's own setting
(`'m2_prior': [-0.165, 0.135, 0.045, 0.008, 0.125]`, `[-0.66, 0.54, 0.18, 0.032, 0.5]`, `'delay_comp': 0`) and three
cells. Versions 46 and 47 render in a frame the browser extension cannot read, but Kaggle's line counts between versions
match the files: 46 against 45 (c6fhm40) +1 -1 (the settings line), 47 +26 -1 (the appended subclass and the settings
line), 48 +1 -26 (subclass removed), 49 and 50 +1 -1.

Kaggle submissions (09 Nov 2026, between 01:03:15 and 01:05:56 by `date`; all five of the day's slots, 5 of 5 before, in this
order): version 50 nodelay, 49 double, 48 half, 47 offset, 46 nolearn. Each description starts "Ablation of v16 (one
change):" and ends "For the paper's test-set ablation table; not used for tuning." All five were "Notebook Running"
at 01:05:56. The final selections were not touched (2/2: v16 and c6fhm40).

## Result (scores read and written 09 Nov 2026, 08:34 by `date`; about 7 h after submission)

All five notebooks scored. Public score, and its ratio to v16's 0.01031:

| arm | score | / v16 | expected (written before) | rule |
|---|---|---|---|---|
| nolearn (no online learning) | 0.01544 | 1.50 | 1.5 to 3.5 | at least 1.10: online learning carries the transfer on the hidden buildings. **Met.** |
| offset (five numbers at priors, disturbance estimate learned) | 0.01034 | 1.00 (1.003) | 1.05 to 1.30 | at least 1.05 would say the five numbers matter beyond an offset there. **Not met**, and below my expectation. |
| half (priors halved) | 0.01042 | 1.01 | 1.00 to 1.05 | within 5 %: the starting values need not be right. **Met.** |
| double (priors doubled) | 0.01033 | 1.00 (1.002) | 0.97 to 1.06 | as above. **Met.** |
| nodelay (no delay compensation in planning) | 0.01180 | 1.14 | 1.00 to 1.04 | at least 1.05: delay compensation matters there. **Met**, and far above my expectation. |

The two results that differ from Table 2 (twelve full-size buildings):

- Learning only the disturbance estimate costs 1.16 times v16 there and 1.00 times here. On the public windows the five
  numbers add nothing measurable beyond the offset (0.3 %, about three steps of the board's resolution).
- Planning past the delay is worth 2 % there and 14 % here.

The paper says both: public column in Table 2, a paragraph in Section 4.2, the Limitations sentence, the abstract and the
conclusion (the 1.5 times). No arm becomes a candidate or a final selection; nothing is tuned on these scores.
