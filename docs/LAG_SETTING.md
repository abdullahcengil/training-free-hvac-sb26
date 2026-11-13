# Setting the measured delay: does it remove the extra-lag weakness? (written 6 Nov 2026, 13:33 by `date`; before any run)

## Why

The sensor-fault test (docs/SENSOR_FAULTS.md) failed its lag mark: with one step of reading delay more than the one
v16 was built for, v16's loss rose 1.50x (mark 1.25x). The paper says that a real deployment must measure the delay on
site with a probe. That advice is only worth something if telling the controller the delay actually helps. This test
checks it. v16 itself and the paper's claims about v16 do not change.

## What (`sb/make_v16lag.py`, `policies/zonal_v16lag_faults.py`, `sb/run_lagset.py`)

One option is added to the frozen v16 file, `extra_lag` (steps of reading delay beyond the one found in this simulator).
With extra_lag d the controller learns each zone from the heat commanded d steps further back, and before planning it
rolls its zone model forward d steps from the stale reading through the heat it has already sent. With extra_lag 0
every new line is skipped (known-answer check: identical to v16 for 288 steps, required before reading anything else).

Same twelve full-size buildings of rounds 6 and 7 as the fault test, ten days each:
- lagcomp: one extra step of reading delay (the fault test's lag1), extra_lag 1;
- overset: no extra delay, but extra_lag 1 (what a wrong setting costs; descriptive).

## Reading rule (fixed now)

- S1: lagcomp at most 1.25 x clean v16's loss (the mark v16 failed at 1.50 x): "with the delay measured and set, one
  more step of lag no longer breaks it".
- S2: lagcomp below lag1 (v16 unaware of the extra lag) in at least 10 of 12 buildings.
- overset is reported as it comes (loss and comfort relative to clean v16), no mark.
Failures are reported as failures. Whatever the result, the submitted v16 and its final selection do not change; the
result goes into the paper's fault appendix as an extension tested post hoc on seen buildings.

## Result (read 6 Nov 2026, 15:08 by `date`; run 13:33-15:05)

Known-answer check (extra_lag 0, 288 steps): IDENTICAL to v16.

| Arm | Loss / clean v16 | Worst | Comfort | Below clean pid_water |
|---|---|---|---|---|
| lag1 (v16 unaware, fault test) | 1.500 | 2.34 | 0.00436 | 12 |
| lagcomp (extra lag, set d=1) | 1.000 | 1.01 | 0.00046 | 12 |
| overset (no extra lag, d=1) | 1.269 | 1.47 | 0.00257 | 12 |

- S1 PASS (1.000 <= 1.25).
- S2 PASS (lagcomp below lag1 in 12 of 12).
- overset: a wrong setting costs 1.27x, so the probe matters both ways.

Paper: paragraph added to Appendix "Faulty sensors"; Limitations sentence says the extra delay costs nothing once set.
Main text still ends on page 8. v16 unchanged.
