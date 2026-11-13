# Cold start on a work day (plan written 08 Nov 2026, 23:36 by `date`, before any run)

## Why

The paper says the controller pays no extra loss on its first work day in a new building (Figure 2b, abstract, Section
4.1). An AI review of the paper (Argon 4, 8 Nov) points out that this is a weak test: nearly every window starts on a
weekend, so the controller has 24 to 48 hours of unoccupied running to learn before comfort first counts, and the
figure has no full-size building. The claim needs a true cold start, or it must be narrowed.

## Design

v16 (frozen/zonal_v16f.py, SHA-256 `af9c0d2bff35568b...`, submission/V16_PARAMS.json), loaded unchanged by
`policies/zonal_v16_coldstart.py`, which re-creates the whole policy object at one step: at 06:00 on the first work day
of the window (the first weekday that is not a US federal holiday; every window starts on a Sunday at 06:00). All
learned numbers return to their starting values, the disturbance estimate to zero, the slab node to the next reading, and
everything else the controller remembers to its start-up value. Before that step the run is v16 itself, so the building
arrives at the restart in the state that v16's own weekend control left it in; this is a limit of the test (a real
hand-over would inherit another controller's building).

Same twelve full-size buildings of rounds 6 and 7, first 1152 steps (four days, enough for the first work day and the
next one when Monday is a holiday). Compared on the same steps with v16's existing runs (`results/round6h/v16`,
`results/round7/chm`) and pid_water's (`results/round6h/pid_water`, `results/round7/pid_water`). These buildings are no
longer blind: post hoc and descriptive, reported whatever it shows. Script: `sb/run_coldstart.py`, three simulations
at a time; log `D:/SmartBuildings_data/coldstart.log`.

Known-answer check, required before any run: with no restart (`cold_step -1`) the wrapper reproduces v16's rewards
exactly for 288 steps on building_7802 helena_feb19. In the runs, every step before the restart must match v16's.

Known-answer check done before freezing this plan (08 Nov 2026, 23:36 by `date`): identical to v16 for 288 steps.

## Measures

- M1: summed loss over the 288 steps from the restart (06:00 on the first work day to 06:00 the next day), cold arm
  divided by v16, as a ratio of sums over the twelve buildings, with a 95 % bootstrap interval over buildings (10,000
  resamples).
- M2: in how many of the twelve the cold arm is below pid_water over those 288 steps.
- M3: M1 on the next 288 steps.
- The comfort term on the first work day, for both arms.

## What each outcome means for the paper (fixed now)

1. M1 at most 1.05: "no extra loss on the first work day" stands, now also from a cold start.
2. M1 above 1.05 and at most 1.30: a modest cost. The abstract and introduction drop "no extra loss on its first work
   day" and the text states M1.
3. M1 above 1.30: a large cost. The claim is restricted to runs that start on a weekend, and the text says so.
4. Transfer holds on the cold first day if M2 is at least 11 of 12; otherwise the paper names the buildings where it
   does not.
5. The controller has caught up by the next work day if M3 is at most 1.05.

Nothing is tuned on these runs, and v16 stays final. Every outcome is reported.

## Expectations, written before the runs (opinion)

M1 between 1.05 and 1.40, with most of it comfort on the first morning (priors, no slab history). M2 12 of 12. M3 about
1.02.

## Result (runs 08 Nov 23:37 to 09 Nov 00:03; read 09 Nov 2026, 00:04 by `date`)

`python -m sb.run_coldstart --read` (output `D:/SmartBuildings_data/coldstart_read.txt`). All twelve runs finished without
a crash, and each is identical to v16 step for step before its restart.

| measure | result |
|---|---|
| M1, first work day, cold / v16 | 1.196 (95 % CI 1.092-1.340), worse in 12 of 12; per building 1.050-1.825, median 1.129 |
| M2, below pid_water on that day | 12 of 12 (ratio of sums 0.281; median 0.237, against 0.216 for v16) |
| M3, next work day, cold / v16 | 1.014 (95 % CI 0.993-1.040) |
| Loss summed over the twelve, first work day | v16 75.9, cold 90.8 |
| Comfort term summed over the twelve, first work day | v16 5.09, cold 21.33 |

Largest per-building ratios: New York, October 1.825; Dubai 1.490; Houston 1.360. In Dubai the comfort term alone goes from
0.01 to 7.99. The comfort rise (16.2) is larger than the whole rise of the loss (14.9), so energy and carbon fall a little.

The rules written before the runs give:

- M1 lies above 1.05 and at most 1.30, a modest cost (rule 2): the abstract and introduction drop "no extra loss on its
  first work day" and the text states M1.
- M2 is 12 of 12, at least 11 (rule 4): transfer holds on the cold first day.
- M3 is at most 1.05 (rule 5): the controller has caught up by the next work day.

M1 and M3 came out inside the expectation written before the runs (1.05 to 1.40, about 1.02), and M2 equals it.
