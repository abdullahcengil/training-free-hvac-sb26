# What carries the transfer? (plan written 31 Oct 2026, 07:04, before any run)

## Why

The paper's title says the controller "learns each new building online", and its conclusion says that five physical
numbers per zone, identified in hours, carry everything building-specific. Neither claim has been tested on the final
controller in unseen buildings: the only ablation of online identification is on v7, the first controller, on the
ten-day development set (Appendix "Ablations": fixed g and lambda doubled the loss), and v16 has a different model
(five numbers with a slab node), priors from offline fits on four training traces, and a disturbance estimate. If the
priors alone do as well, the transfer comes from the structure and the priors, not from learning, and the paper must
say so.

## Design

v16 (frozen/zonal_v16f.py, sha256 af9c0d2b..., submission/V16_PARAMS.json) with one part removed or disturbed at a
time, on the twelve full-size buildings of rounds 6 and 7 (first 2880 steps, the rounds' own windows), against v16's
existing runs there (`results/round6h/v16`, `results/round7/chm`). These buildings are no longer blind: the ablation is
post hoc and descriptive, and every arm is reported, whatever it shows.

| Arm | Change |
|---|---|
| nolearn | `rls 0`: the five numbers of each zone stay at their priors, and no disturbance is estimated |
| offset | the five numbers stay at their priors; the disturbance estimate is learned (`policies/zonal_v16_offsetonly.py`, a subclass that loads the frozen file unchanged) |
| half | all five priors halved, learning on |
| double | all five priors doubled, learning on |
| nodelay | `delay_comp 0`: plans and safety nets ignore the heat already in the pipe |

Known-answer check, run first: `offset` with `dist_beta 0` must give exactly the rewards of `nolearn` over 288 steps
(building 7802, Helena). If it fails, the `offset` arm is not reported as an ablation.

Script: `sb/run_transfer_abl.py` (61 runs, three at a time, about five hours); log
`D:/SmartBuildings_data/transfer_abl.log`; read with `python -m sb.run_transfer_abl --read`.

## Measures

Per arm: the ratio of mean losses (arm / v16) over the 12 scenarios, with a 95 % bootstrap interval over scenarios
(10,000 resamples), the number of scenarios in which the arm is worse than v16, and the comfort term.

## What each outcome means for the paper (fixed now)

1. Online learning carries the transfer if `nolearn` is at least 10 % worse than v16, its interval lies above 1, and
   it is worse in at least 10 of 12 scenarios. If `nolearn` is less than 5 % worse, learning is not what transfers:
   the title and the conclusion change to say that the structure (the delay and the slab) and the priors carry it.
   Between 5 and 10 %: reported as a modest contribution, and the title loses "learns".
2. The five numbers matter beyond an offset if `offset` is at least 5 % worse than v16 with its interval above 1;
   otherwise the paper says that the learned offset (integral action) does most of the adapting.
3. The priors need not be right (training-free in the strong sense) if `half` and `double` are each within 5 % of v16
   on the mean and no scenario is worse by more than 15 %; otherwise the paper says how much the priors matter and
   that they came from four training traces.
4. The delay finding matters for transfer if `nodelay` is at least 5 % worse with its interval above 1.

## My expectations, written before the runs (opinion)

- nolearn: 30-60 % worse. Room sizes in full-size buildings range from 20 to 890 m2 on the same 2 m3/s box, so one
  gain cannot fit all zones (the smallest rise 7-10 K per step at full heat, the largest recover at 0.7 K/h).
- offset: 10-30 % worse; an offset cannot fix a wrong gain.
- half and double: within 3 %; ten days are long against the hours learning needs.
- nodelay: 5-30 % worse; ignoring the heat in the pipe should bring back the relay of rounds 1 and 7 in small rooms.

## Result

(to be filled in after the runs, with the time of reading)
