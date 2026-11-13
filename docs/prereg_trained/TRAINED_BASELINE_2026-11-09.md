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

(none yet)

## Result

(empty until the test has run)
