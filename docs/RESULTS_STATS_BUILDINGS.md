# Paired statistics by building (descriptive)

As docs/RESULTS_STATS.md, but scenarios on the same building are averaged first, so that each building counts once. Reduction = 1 - mean(ours)/mean(reference). Bootstrap: 10,000 resamples of buildings, seed 0. Sign test two-sided over buildings, ties dropped. Written by `sb/stats_buildings.py`.

| comparison | scenarios | buildings | better / same / worse | reduction | bootstrap 95 % CI | sign test p |
|---|---|---|---|---|---|---|
| Round 1 (pre-registered): v7 vs pid_water | 12 | 6 | 5 / 0 / 1 | 7.7% | -26.9% to 39.5% | 0.22 |
| Round 1, post hoc: v8 vs pid_water | 12 | 6 | 6 / 0 / 0 | 71.7% | 67.8% to 75.2% | 0.031 |
| Round 2 (pre-registered): v8 vs v7 | 12 | 6 | 6 / 0 / 0 | 66.7% | 50.9% to 78.8% | 0.031 |
| Round 2 (pre-registered): v8 vs pid_water | 12 | 6 | 6 / 0 / 0 | 76.8% | 75.9% to 78.2% | 0.031 |
| Round 3 (pre-registered): v9 vs pid_water | 12 | 6 | 6 / 0 / 0 | 72.2% | 65.5% to 78.1% | 0.031 |
| Training, 30 scenarios: v9 vs v8 | 30 | 6 | 6 / 0 / 0 | 4.2% | 3.1% to 5.9% | 0.031 |
| Round 4 (pre-registered): v10 vs v9 | 12 | 6 | 6 / 0 / 0 | 6.1% | 1.8% to 12.3% | 0.031 |
| Round 4 (pre-registered): v10 vs pid_water | 12 | 6 | 6 / 0 / 0 | 70.5% | 59.2% to 78.8% | 0.031 |
| Training, 30 scenarios: v10 vs v9 | 30 | 6 | 6 / 0 / 0 | 8.9% | 5.0% to 13.6% | 0.031 |
| Round 5 (pre-registered): v11 vs v10 | 12 | 6 | 6 / 0 / 0 | 27.8% | 20.6% to 38.0% | 0.031 |
| Round 5 (pre-registered): v11 vs pid_water | 12 | 6 | 6 / 0 / 0 | 85.0% | 80.5% to 89.4% | 0.031 |
| Training, 30 scenarios: v11 vs v10 | 30 | 6 | 6 / 0 / 0 | 31.9% | 27.1% to 38.3% | 0.031 |
| Training, 30 scenarios: v15 vs v14 | 30 | 6 | 6 / 0 / 0 | 1.8% | 1.6% to 2.1% | 0.031 |
| Stress, 40 windows: v15 vs v14 | 40 | 6 | 6 / 0 / 0 | 0.9% | 0.7% to 1.0% | 0.031 |
| Training, 30 scenarios: v16 vs v15 | 30 | 6 | 6 / 0 / 0 | 0.4% | 0.2% to 0.6% | 0.031 |
