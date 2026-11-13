# Paired statistics (descriptive)

Loss = mean |reward| per step (lower is better). Reduction = 1 - mean(ours)/mean(reference). Sign test and Wilcoxon signed-rank test are two-sided, over scenarios; ties (identical runs) are dropped from both tests. Bootstrap: 10,000 resamples of scenarios, seed 0. Written by `sb/stats.py`.

| comparison | n | better / same / worse | reduction | bootstrap 95 % CI | sign test p | Wilcoxon p |
|---|---|---|---|---|---|---|
| Round 1 (pre-registered): v7 vs pid_water | 12 | 8 / 0 / 4 | 7.7% | -24.3% to 36.9% | 0.39 | 0.27 |
| Round 1, post hoc: v8 vs pid_water | 12 | 12 / 0 / 0 | 71.7% | 67.4% to 75.5% | 0.00049 | 0.00049 |
| Round 2 (pre-registered): v8 vs v7 | 12 | 12 / 0 / 0 | 66.7% | 54.3% to 77.5% | 0.00049 | 0.00049 |
| Round 2 (pre-registered): v8 vs pid_water | 12 | 12 / 0 / 0 | 76.8% | 73.8% to 80.5% | 0.00049 | 0.00049 |
| Round 3 (pre-registered): v9 vs v8, cold | 6 | 6 / 0 / 0 | 9.1% | 6.5% to 12.4% | 0.031 | 0.031 |
| Round 3 (pre-registered): v9 vs v8, warm | 6 | 1 / 4 / 1 | 0.4% | -0.1% to 1.7% | 1 | 1 |
| Round 3 (pre-registered): v9 vs pid_water | 12 | 12 / 0 / 0 | 72.2% | 65.8% to 77.3% | 0.00049 | 0.00049 |
| Training, 30 scenarios: v9 vs v8 | 30 | 15 / 13 / 2 | 4.2% | 2.3% to 6.3% | 0.0023 | 0.00084 |
| Round 4 (pre-registered): v10 vs v9, warm | 6 | 5 / 0 / 1 | 19.7% | 8.1% to 30.2% | 0.22 | 0.062 |
| Round 4 (pre-registered): v10 vs v9, cold | 6 | 4 / 0 / 2 | -0.2% | -2.0% to 1.5% | 0.69 | 1 |
| Round 4 (pre-registered): v10 vs v9 | 12 | 9 / 0 / 3 | 6.1% | 0.9% to 14.6% | 0.15 | 0.052 |
| Round 4 (pre-registered): v10 vs pid_water | 12 | 12 / 0 / 0 | 70.5% | 60.3% to 78.3% | 0.00049 | 0.00049 |
| Training, 30 scenarios: v10 vs v9 | 30 | 30 / 0 / 0 | 8.9% | 5.8% to 12.7% | 1.9e-09 | 1.9e-09 |
| Round 5 (pre-registered): v11 vs v10 | 12 | 12 / 0 / 0 | 27.8% | 21.8% to 35.4% | 0.00049 | 0.00049 |
| Round 5 (pre-registered): v11 vs v10, cold | 6 | 6 / 0 / 0 | 27.6% | 21.4% to 36.9% | 0.031 | 0.031 |
| Round 5 (pre-registered): v11 vs v10, warm | 6 | 6 / 0 / 0 | 28.2% | 16.8% to 40.4% | 0.031 | 0.031 |
| Round 5 (pre-registered): v11 vs pid_water | 12 | 12 / 0 / 0 | 85.0% | 81.5% to 88.7% | 0.00049 | 0.00049 |
| Training, 30 scenarios: v11 vs v10 | 30 | 30 / 0 / 0 | 31.9% | 28.2% to 37.0% | 1.9e-09 | 1.9e-09 |
| Round 6 (pre-registered, ten days): v15 vs v14 | 6 | 6 / 0 / 0 | 2.7% | 1.6% to 4.2% | 0.031 | 0.031 |
| Round 6, pid_water run after the round: v15 vs pid_water | 6 | 6 / 0 / 0 | 79.4% | 67.5% to 87.8% | 0.031 | 0.031 |
| Training, 30 scenarios: v15 vs v14 | 30 | 23 / 7 / 0 | 1.8% | 1.4% to 2.3% | 2.4e-07 | 2.4e-07 |
| Stress, 40 windows: v15 vs v14 | 40 | 20 / 20 / 0 | 0.9% | 0.6% to 1.1% | 1.9e-06 | 1.9e-06 |
| Round 7 (pre-registered, ten days): v16 vs v15 | 6 | 6 / 0 / 0 | 7.6% | 0.4% to 16.7% | 0.031 | 0.031 |
| Round 7, pid_water run after the round: v16 vs pid_water | 6 | 6 / 0 / 0 | 83.7% | 77.5% to 89.7% | 0.031 | 0.031 |
| Training, 30 scenarios: v16 vs v15 | 30 | 18 / 11 / 1 | 0.4% | 0.2% to 0.7% | 7.6e-05 | 9.5e-05 |
| Round 8 (pre-registered, ten days): candidate vs v16 | 6 | 4 / 1 / 1 | 0.1% | 0.0% to 0.8% | 0.38 | 0.12 |
| Round 8, pid_water run after the round: v16 vs pid_water | 6 | 6 / 0 / 0 | 86.5% | 79.5% to 95.1% | 0.031 | 0.031 |

With 6 to 12 scenarios per round these tests are coarse; they are reported to show how much of each difference could be chance, not as new hypotheses.
