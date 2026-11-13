# Our controller under the proposed hot-water tank fix

Written 23 Oct 2026, 18:12 (UTC+2), before any run on the patched simulator.

## Why

Forum threads 749531 and 751998 report that, in the shipped simulator, billed boiler gas and the reheat the coils
receive can differ when the supply-water setpoint moves. The hosts have not ruled yet. On 23 Oct a participant opened
starter-kit pull request 2 ("Energy-balanced hot-water tank"): the tank temperature follows
C dT/dt = Q_burner - Q_coils - Q_loss and gas is billed as Q_burner. The organisers' paper says the top submissions are
re-run "at a fixed simulator commit", so the final standings may be computed with or without such a fix. Our
controller should score the same either way; this checks it.

## How

- `sb/make_tankfix.py` writes the pull request's equations into a separate copy of the installed package
  (`D:/SmartBuildings_data/kit_tankfix`). The code is ours, written from the pull request's description; its files
  were not downloaded or run. The installed simulator is not touched. Runs use the copy through `PYTHONPATH`.
- `sb/tankfix_check.py` (passed 23 Oct, 18:10): energy is conserved over charge/discharge cycles (relative error
  4e-15); a setpoint dropped below the tank gives no unbilled heat; with the setpoint held at 350 K the bill equals the
  shipped formula at every step (difference 0).
- Runs (`sb/jobs_tankfix.json`, full length, 8640 steps): v13 (`submission/V13_PARAMS.json`) and the official
  pid_water baseline on the five training scenarios of building_train_1, on the patched copy; pid_water also on the
  shipped simulator for fairbanks_1, to confirm that the shipped `baseline_returns.json` value reproduces here.

## Expectation (written before the runs)

- v13 holds the supply water at 350 K from the first step, so only the first four steps (the tank heating from 340 K)
  can differ. Expected: v13's score changes by less than 0.1 % in every scenario.
- pid_water moves the setpoint; no prediction.

## Use

A sentence in the paper, and numbers the user may post on the forum to help the hosts decide. Not used for tuning.

## Result (23 Oct, 21:28)

| scenario (building_train_1) | v13 shipped | v13 fixed | change | pid_water shipped | pid_water fixed | change |
|---|---|---|---|---|---|---|
| fairbanks_1 | 0.045417 | 0.045417 | -2.3e-7 | 0.21392 (run here) | 0.28569 | +33.6 % |
| denver_7 | 0.002083 | 0.002083 | -2.4e-6 | 0.03100 (run here) | 0.03084 | -0.5 % |
| atlanta_2 | 0.003128 | 0.003128 | -1.4e-6 | 0.02491 (run here) | 0.02436 | -2.2 % |
| phoenix_5 | 0.014430 | 0.014430 | -4.1e-7 | 0.13649 (run here) | 0.12654 | -7.3 % |
| singapore_8 | 0.006641 | 0.006641 | -7.5e-7 | 0.02835 (run here) | 0.02952 | +4.1 % |

- **v13: the expectation holds.** The largest change is 2.4e-6 of the score (0.0002 %; mark 0.1 %). Per step the rewards
  differ only in the last digits (the bill is computed by a different formula with the same value) and in the first
  steps, while the tank heats from 340 K.
- **pid_water** moves the setpoint, so it is affected: +33.6 % in fairbanks_1, both runs made here the same way. The
  other four are compared with the shipped `baseline_returns.json`, which the starter kit's tracker produced; our
  direct runs differ from it by about 1 % (fairbanks_1: 0.21392 here, 0.21168 shipped), so those four changes carry
  that error. Runs of pid_water on the shipped simulator for the four, made the same way, are queued
  (`sb/jobs_tankfix_shipped2.json`, after screen e).
- Reading (opinion): a controller that holds the setpoint is unaffected by the proposed fix; a standard reset policy
  moves by a few percent in mild climates and by a third in the coldest one.

- 23 Oct, 22:53: the four shipped pid_water runs made here the same way (`sb/jobs_tankfix_shipped2.json`) replace
  the shipped-file values in the table: pid_water changes by +33.6 % (Fairbanks), +4.1 % (Singapore), -0.5 % (Denver),
  -2.2 % (Atlanta) and -7.3 % (Phoenix) under the fix.

## Would a hot-water reset save real gas under the fix? (1 Nov 2026, 16:24 by `date`; no runs)

Under the energy-balanced tank the only real saving from a lower water temperature is the tank's standing loss
(boiler.py, `compute_thermal_dissipation_rate`: insulated cylinder, radius 0.5 m, length 2 m, 6 cm insulation at
0.067 W/m/K; the scenarios set only the outside convection coefficient, 8.8-26.7 W/m2/K). At -20 C outside it is
0.64-0.69 kW at 350 K, 0.51-0.55 kW at 330 K and 0.44-0.48 kW at 320 K: a reset saves at most about 0.2 kW, against
heating loads of tens of kW per building in cold weather, so well under 1 % of the loss. Not a candidate (standing rule:
more than 1 % evidence first). On the shipped simulator a reset would gain mainly from the accounting issue, which we
do not use.
