# A trained neural controller as a comparison (plan written 09 Nov 2026, 03:27 by `date`; before the training run and before any run on the test scenarios)

## Why

The paper compares v16 with the official baselines only, and says so in Limitations ("we compared with no trained policy").
The starter kit ships no trained policy and no training code. An outside review named this as the main remaining gap. The
hosts' own study trains SAC and DDPG agents on one building of the same simulator (Goldfeder et al., ICCV Workshops 2025),
which shows the approach works there, but on other buildings and not across buildings, so its numbers cannot be compared.

## The controller

`policies/trained_residual.py`. One small network (27 inputs, two hidden layers of 64, tanh) is shared by every zone and
outputs corrections to that zone's damper and reheat valve commands; another with the same shape is shared by every air
handler and outputs corrections to its supply-air temperature, fan pressure and recirculation commands. Because the weights
are shared, the same two networks run on any building, of any size. The corrections are added to the action of the strongest
official baseline, pid_water (`policies/pid_water_official.py`, verbatim copy; with no weights the policy reproduces
pid_water exactly, checked action by action for 360 steps), and clipped to the action range. A decision is taken every
15 minutes and held. The on/off commands and the hot-water loop stay with pid_water.

Inputs are the zone's temperature relative to the comfort band and to the band in force, its last two changes, the clock,
the comfort flags, hours to comfort, outside temperature now and its 24-hour mean, building occupancy, last commands, box
size, air-handler state and the baseline's own command. Nothing from v16 (no zone model, no delay handling) goes in.

Why this shape: it is the strongest starting point available without a building model. It begins exactly at the strongest
baseline, it transfers to new buildings by construction, and it can reach any continuous action.

## Training

`sb/train_rl.py`, `sb/rl_core.py` (numpy; every gradient checked against finite differences, and a toy problem solved).
PPO with one reward per agent: a zone's reward is its own comfort loss (from the simulator's per-zone temperature and
occupancy, available during training only) plus its share of the energy and carbon cost (electricity by airflow, gas by
airflow times reheat valve), scaled so that the mean over zones is the building's reward; an air handler's reward is the mean
over its zones. Samples from steps when the air handler is off do not enter the policy update (the action changes nothing).
Settings: discount 0.98 per decision, GAE 0.95, clip 0.2, 4 epochs, Adam with learning rate 3e-4 falling to 1e-4, three
parallel simulations. Each simulation runs one training scenario from start to end, then a random next one.

- **Simulator:** the corrected copy (`D:/SmartBuildings_data/kit_fixed`, docs/FIXSIM.md), so the policy cannot learn to use
  the simulator's hot-water accounting issue. It also never touches the hot-water loop.
- **Data:** the 25 scenarios of five training buildings. `building_train_4` (five scenarios) is kept out of training and
  used only to choose the checkpoint.
- **Budget:** wall clock, about 38 hours on three CPU processes (the number of simulator steps is reported). One run, one
  seed; there is no time for more.
- **Choosing the checkpoint:** every 150 iterations the policy, with no exploration noise, runs the first 2880 steps of the
  five validation scenarios. The checkpoint with the lowest mean loss there is the result. If the run has to be changed or
  restarted because of a bug or because it plainly does not learn in its first hours, that happens on training and
  validation data only and is written under Deviations.

## The test (once, after training ends)

The twelve full-size scenarios of rounds 6 and 7 (the same as Table 2 of the paper), first 2880 steps, on the shipped
simulator, no exploration noise, same harness (`sb/run.py`) as every other result in the paper. None of these buildings is
used in training or validation. Reference runs that already exist: v16 (`results/round6h/v16`, `results/round7/chm`) and
pid_water (`results/round6h/pid_water`, `results/round7/pid_water`). If the notebook check passes, the same weights also get
one submission to the public leaderboard, reported as it comes (reference: v16 0.01031).

## What each outcome means for the paper (fixed now)

Loss = mean over the first 2880 steps; the twelve scenarios count equally; 95 % interval by bootstrap over scenarios, as in
Table 2.

1. **Is the trained policy a real competitor?** It improves on the strongest official baseline if its mean loss is at most
   0.95 times pid_water's and it is below pid_water in at least 9 of 12 scenarios. Otherwise the paper says that within this
   budget the trained policy did not reliably improve on the baseline, and that this says little about what trained control
   can reach.
2. **Trained policy against v16.** If v16 is below it in at least 10 of 12 and the ratio of mean losses (trained / v16) is at
   least 1.5, the paper says v16 beats a trained policy with this budget and by how much. Between 1.0 and 1.5: v16 is modestly
   better. Below 1.0: the trained policy is better than v16, and the abstract and the conclusion must say so.
3. Every outcome is reported, with the budget (simulator steps, CPU hours) next to v16's zero training. The Limitations
   sentence changes accordingly and still says it is one architecture, one budget and one seed, so not a statement about what
   trained controllers can reach in general.

The weights, the hyperparameters and the policy do not change after the first test run. If this finishes too late for the
PDF freeze on 11 Nov, the paper keeps its present sentence and the result goes into a later revision.

## Expectation, written before any run (opinion)

The trained policy lands at 0.6 to 1.0 times pid_water's loss; v16 is 3 to 5 times below it. v16 starts at 0.18 times pid_water
on these scenarios, and a policy that starts at pid_water and learns one correction per zone has much further to go than 38
CPU hours allow.

## Deviations

1. 09 Nov 2026, 07:21 by `date`. At iteration 195 (3.9 h, 337,000 simulator steps; validation loss at iteration 150: 0.02551 against 0.03293 for pid_water on the corrected simulator) we saw that the zone minibatch of 8192 was larger than the number of active samples per iteration (2,300 to 11,000), so each actor got only 4 gradient steps per iteration. An update costs almost nothing next to the simulator, so the minibatches became 1024 (zones) and 256 (air handlers) and the epochs went from 4 to 8; the run continues from its saved state. Nothing else changes. No test scenario had been run; the decision used training and validation data only.
2. 10 Nov 2026, 01:08 by `date`. The loss during training (with exploration noise, in blocks of 100 iterations) fell from 0.032 to 0.024 by iteration 700 and then rose to 0.035 (iterations 700 to 1050); the validation loss rose from 0.02357 (iteration 450, the best) to 0.02494 (900) and 0.02460 (1050). The likely cause: every update used data from only three scenarios, which stayed in the batch for 15 iterations, and after deviation 1 the actors had enough gradient steps to chase them. The run continues from the actors of the best checkpoint (iteration 450) with: episodes cut at 2880 steps, so that about three times as many scenarios pass per hour; learning rate about 9e-5 falling to 5e-5; 4 epochs; and an exponential average of the actor weights (0.99 per iteration), which is what validation, the checkpoints and the final policy use. The result is the checkpoint with the lowest validation loss over the whole run, 0.02357 unless a later one beats it. No test scenario had been run; the decision used training and validation data only.
3. 10 Nov 2026, 01:39 by `date`. Recorded late, same stage: from the restart of deviation 2 on, validation runs every 100 iterations instead of 150 (command line `--val-every 100`), and the checkpoints with it. It only makes the choice of checkpoint finer; no test scenario had been run.

## Result

11 Nov 2026, 09:36 UTC (10:36 local) by `date` (written after the one test run: 11 Nov 2026, 08:08 to 09:35 UTC, first result 08:25 UTC;
`python -m sb.run_trained` then `--read`; files `results/rl_test/summary.json` and `paper/tab_trained.tex`).
Checkpoint: iteration 1200 (validation 0.02339), budget 3,283,389 simulator steps in
38.0 hours on three CPU processes. Shipped simulator, first 2880 steps, no exploration noise.

| Scenario | v16 | pid_water | trained | trained / pid_water | trained / v16 |
|---|---|---|---|---|---|
| building_7701__houston_may28 | 0.00650 | 0.02712 | 0.01618 | 0.597 | 2.49 |
| building_7702__miami_jul02 | 0.01170 | 0.03794 | 0.02705 | 0.713 | 2.31 |
| building_7703__dubai_sep03 | 0.02832 | 0.06779 | 0.04679 | 0.690 | 1.65 |
| building_7704__newyork_oct08 | 0.00305 | 0.03788 | 0.03202 | 0.845 | 10.52 |
| building_7705__chicago_nov19 | 0.01338 | 0.09094 | 0.08746 | 0.962 | 6.53 |
| building_7706__duluth_dec17 | 0.01043 | 0.09512 | 0.09288 | 0.976 | 8.90 |
| building_7802__helena_feb19 | 0.01720 | 0.11359 | 0.10029 | 0.883 | 5.83 |
| building_7803__newyork_jan29 | 0.01381 | 0.10141 | 0.10008 | 0.987 | 7.25 |
| building_7804__chicago_dec03 | 0.02253 | 0.14350 | 0.13767 | 0.959 | 6.11 |
| building_7806__sanfrancisco_mar05 | 0.00353 | 0.05664 | 0.05117 | 0.903 | 14.48 |
| building_7807__duluth_feb19 | 0.03601 | 0.11949 | 0.09711 | 0.813 | 2.70 |
| building_7808__seattle_nov26 | 0.00472 | 0.06637 | 0.06820 | 1.028 | 14.44 |
| **Mean** | 0.014265 | 0.079815 | 0.071408 | 0.895 (95 % CI 0.831-0.945) | 5.01 (3.52-7.32) |

Comfort term (mean per step): v16 0.00048, pid_water 0.06341, trained 0.06016. Energy
and carbon part (loss minus comfort term): v16 0.01378, pid_water 0.01641, trained 0.01125.

By the rules fixed before training:

1. **Real competitor?** Yes: trained / pid_water = 0.895 (at most 0.95) and below pid_water in 11 of 12 (at least
   9). Within this budget the trained policy improves on the strongest official baseline.
2. **Trained policy against v16:** v16 is lower in 12 of 12 (at least 10) and trained / v16 = 5.01 (at least
   1.5), so the paper says v16 beats a trained policy with this budget, by a factor of 5.0.
3. Reported with the budget next to v16's zero training; the Limitations sentence says it is one architecture, budget and
   seed.

Expectation written before any run (opinion): 0.6 to 1.0 times pid_water's loss (observed 0.89, inside) and v16 3
to 5 times below it (observed 5.0, at the top of the range).

Observation, not a hypothesis: the trained policy's gain is energy. Its energy and carbon part is
0.69 times pid_water's (and 0.82 times v16's), but its comfort term
stays at 0.95 times pid_water's, while v16's is 0.008 times it.
On the validation building, of the shipped size, it had reached 0.71 times pid_water's loss;
on the new full-size buildings 0.89 times.

In the paper: Section 4.1 paragraph, one abstract sentence, the Limitations sentence, the appendix "A trained
controller" (budget, Figure, Table, outcome paragraph and the observation above), a row in the timestamp table (first
result 11 Nov, 08:25 UTC; write-up 11 Nov, 09:36 UTC) and in the sources table.
Kaggle: the notebook (`submission/lb/trained_residual.ipynb`, saved as version 56) gets one public submission once
`python -m sb.make_trained_source --check` passes; its score is reported as it comes.
The check passed on 11 Nov (two-file policy and single file -0.008113 each, largest action difference 0). Submitted
11 Nov 2026 just before 10:45 by `date` (UTC+1; `date` read 10:45:18 right after): version 56 ("trained residual (PPO,
iteration 1200)"), description "Trained residual (PPO corrections to pid_water, iteration 1200; docs/TRAINED_BASELINE.md):
the paper's trained comparison, one submission, weights unchanged, not used for tuning." Kaggle showed "Notebook
Running"; the score is due about seven hours later. When it is in: `python sb/paper_apply_trained_public.py <score>
"<read time UTC>"` (one sentence in appendix O; dry run checked 11 Nov), rebuild, check that the main text still ends
on page 8, then commit. The final selections stay v16 and c8fhm40 (checked on the Submissions page after this
submission).

## Public leaderboard score (written 11 Nov 2026, 21:54 by `date`, 20:54 UTC)

Read on the competition's Submissions page on 11 Nov 2026 at 20:52 UTC (21:52 local): version 56 ("trained residual
(PPO, iteration 1200)"), status Succeeded, public score **0.03911**. That is 0.61 times the official pid_water baseline
submitted unchanged (0.06404) and 3.8 times v16 (0.01031). On the twelve full-size buildings of rounds 6 and 7 the same
weights had 0.89 times pid_water's loss and 5.0 times v16's, so on the hidden public buildings the trained policy is
further below the baseline and closer to v16 than on ours; v16 is still well ahead. Reported as it came, as the plan
says. In the paper: one sentence in appendix "A trained controller" (`sb/paper_apply_trained_public.py`), one in
Section 4.1 and a bracket in the abstract. No new submission was made and the final selections were not touched.
