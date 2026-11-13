# v16 behind faulty sensors (written 4 Nov 2026, 16:25 by `date`; before any run)

## Why

The competition's page says the goal is "a policy that can adapt to a new building with minimal configuration" and
that "winning solutions may have the opportunity to test their models on three real buildings". Our paper's limitation
says that nothing here has run in a real building and that the one-step lag belongs to this simulator. The simulator's
sensors are perfect; real ones are not. So we test the claim that matters for a real building: does a controller that
learns online survive bad readings, or does learning make it fragile?

## What (`sb/run_faults.py`, `policies/zonal_v16_faults.py`; frozen v16 file and parameters unchanged)

The controller reads zone temperatures through a fault; the simulator's true temperature still decides the comfort
term. Twelve full-size buildings of rounds 6 and 7 (seen before, so post hoc), ten days each:

| arm | fault |
|---|---|
| noise02 | Gaussian noise, 0.2 K, new at every step (a decent thermistor) |
| noise05 | the same, 0.5 K (a poor one) |
| bias05 | a fixed calibration error per zone, drawn with 0.5 K standard deviation |
| lag1 | one more step of reading delay (two in all, against the one we designed for) |
| stuck10 | 10 % of the zones' sensors stuck at their first reading (dead sensors) |

Known-answer check first: with no fault the wrapper must reproduce v16 exactly (288 steps).

## Reading rule (fixed now)

Reported for each arm: loss relative to clean v16, worst building, comfort term, and in how many of the twelve it stays
below clean pid_water (the baseline gets perfect sensors).
- R1: noise02 at most 1.10 x clean v16: "tolerates ordinary sensor noise".
- R2: lag1 at most 1.25 x: "a longer lag than designed for does not break it" (the learned model does not know the lag).
- R3: stuck10 below clean pid_water in at least 10 of 12: "survives dead sensors".
Failed marks are reported as failures. Any weakness may lead to a fix only through a new screen and a blind round; the
submitted v16 does not change because of this test.

Expectation (opinion): noise02 passes; noise05 costs more because full-effort rules and the learning both see the
noise; lag1 is the most likely to restart the limit cycle; stuck zones lose comfort and dominate the loss.
