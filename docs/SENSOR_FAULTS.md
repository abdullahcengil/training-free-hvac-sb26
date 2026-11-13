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

## Result (read 6 Nov 2026, 01:00 by `date`; `python -m sb.run_faults --read`)

Known-answer check: with no fault the wrapper reproduced v16 exactly (288 steps). Twelve buildings per arm; clean v16
mean loss 0.01427 (comfort term 0.00048), clean pid_water 0.07982.

| arm | loss / clean v16 | worst building | comfort term | below clean pid_water |
|---|---|---|---|---|
| noise02 | 1.014 | 1.05 | 0.00072 | 12 of 12 (ratio 0.18) |
| noise05 | 1.076 | 1.26 | 0.00140 | 12 of 12 (0.19) |
| bias05 | 1.355 | 2.14 (Seattle) | 0.00533 | 12 of 12 (0.24) |
| lag1 | 1.500 | 2.34 (Miami) | 0.00436 | 12 of 12 (0.27) |
| stuck10 | 2.296 | 8.15 (New York, Oct) | 0.01449 | 10 of 12 (0.41) |

- R1 (noise02 at most 1.10x): 1.014. **PASS.**
- R2 (lag1 at most 1.25x): 1.500, only Duluth (Feb) and Seattle below 1.25. **FAIL.**
- R3 (stuck10 below clean pid_water in at least 10 of 12): 10 of 12. **PASS** (at the mark); the two above are Houston
  and Miami, hot windows where pid_water itself is cheap (0.027, 0.038).

Reading: ordinary noise costs about 1 %, so learning online does not make the controller fragile to it. Two faults cost
a lot. A second step of reading delay costs half again (worst in hot, humid windows: x2.2-2.3): the delay-aware safety
net expects one step, so with two it acts late, and the comfort term grows ninefold. A dead sensor leaves its zone
uncontrolled; most of the stuck arm's loss is comfort (0.0145 of 0.0328), and the relative cost is largest where clean
v16 is cheapest (New York in October, San Francisco: x8). A fixed 0.5 K calibration error costs a third. In 58 of 60
faulty runs v16 still stays below pid_water running with perfect sensors.

Consequence (fixed in the plan): the submitted v16 does not change. For a real building this says what has to come
first: measure the reading delay on site (the probe of Appendix A does this) and detect dead sensors (a zone whose
reading does not move while its damper and reheat do). Both are reported as limitations in the paper.
