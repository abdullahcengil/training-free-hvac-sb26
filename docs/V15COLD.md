# v15 for deep cold at full size (screen rules written 30 Oct 2026, 00:46, before any screen run)

Why: in the deep-cold size test (docs/BIG_BUILDINGS.md, 30 Oct) v14 at full size loses 1.21 times what it loses at
the shipped size, and these scenarios are large (0.045 per step, six times v14's training mean). Where the extra goes
(7 buildings, 7003 left out; `results/coldsize`, per-step records): comfort in comfort time, worst 06:00-09:00 and
still there through the afternoon, worst on Mondays (after the weekend float); energy in the morning recovery (03:00-09:00).
Two parts of v14 limit how fast a cold zone is brought back:
- in comfort time a zone gets at most f_heat_max (0.245) of its box's airflow, or f_heat_safety (0.45) once it is more
  than boost_k (0.25 K) below its target; v14 prices unmet cooling in its plant plan but not unmet heat;
- while recovering at night a zone behind its glide path gets at most max(f_heat_safety, f_heat_rec) = 0.45.
At full size every box keeps the same 2 m3/s while rooms are about twice as large, so these caps bind more often.
The heat a late zone needs is about the same at any airflow (the coil warms the outside-air share in proportion to the
heat delivered); a higher cap adds mostly fan work and shortens the time spent below the band.

Candidates (`frozen/zonal_v15dev_h.py`, all options off reproduce v14 exactly: 864 steps of building_train_1
fairbanks_1, identical per-step records; parameters in `docs/v15cold_candidates.json`, each on top of V14_PARAMS):
- **cu** (heat_cu 1): in comfort time a zone below the comfort band may take its whole box (cap 1.0).
- **rc** (rec_cu 1): while recovering at night a zone behind its glide path by more than boost_k may take its whole box.
- **curc**: both.
- **hp12** (heat_price 1, heat_caps 0.6 and 1.0, heat_h 12): in comfort time each air handler is also planned with
  caps 0.6 and 1.0, and the plan with the lowest energy cost plus the comfort value of the heat its zones still lack
  (predicted shortfall two steps ahead, counted for 12 steps) is kept.
- **hpz** (hp12 with heat_price_zone 1; added 30 Oct, 00:52, still before any screen run, after the first two diagnosis
  traces): the higher caps apply only to zones already below the comfort band. Reason: in building 7407 at full size
  the three largest rooms (665-887 m2) sit 1.2-1.5 K below the band through comfort time, 63 % of their cold steps at
  the 0.45 cap; and the static pressure is set by the box with the largest airflow share, so a higher cap for one zone
  raises every box's floor airflow (outside air the coils must heat: about 212 of 375 kW of occupied gas in 7408).
- **hpzrc**: hpz with rec_cu 1.

Screen (`sb/run_v15cold_screen.py`; reference: v14's runs of the deep-cold size test, `results/coldsize/full`):
1. Stage 1: all six candidates on the eight fairbanks_nov21 full-size scenarios, first 2880 steps. A candidate
   advances if its mean loss is at least 2 % below v14's and no scenario is more than 2 % worse.
2. Stage 2: of those that advance, the one with the lowest mean runs on the eight duluth_jan25 scenarios; it passes if
   the same two conditions hold there.
3. Regression checks for the stage-2 winner, before any blind round: the twelve full-size development scenarios of
   docs/BIGDEV.md (mild winter and hot summer; v14 in `results/bigdev/v14`): mean loss at most 0.5 % above v14's and
   no scenario more than 2 % worse; the 30 training scenarios at full length: mean at most 0.3 % above v14's 0.007328.
4. A candidate that passes all of this is frozen and goes to a blind round on new buildings (its own rules, written
   and timestamped before that round is generated). If none passes, v14 stays and this is reported.

## Before stage 1 (30 Oct, 01:02)

- Identity check of the final candidate file (SHA-256 207c9d5cd58c8f1436e3ec54f2d22bd2982c0bccf7aecd0b1845007dc1c6561a),
  all new options off: 864 steps of building_train_1 fairbanks_1, per-step records identical to frozen v14's
  (`D:/SmartBuildings_data/v15h_identity.log`: IDENTITY OK, largest difference 0.0). Stage 1 started at 01:00.
- Third diagnosis trace (7001 at full size, Duluth, -17.0 C): comfort 0.01356 of a 0.07288 loss (scaled 0.00134 of
  0.05589); the four largest rooms (745-1164 m2) sit 1.6-2.3 K below the band through comfort time, and 88 % of the
  cold zone-steps are at the 0.45 cap.

## Stage 1 decided (30 Oct, 01:28): no candidate passes; v14 stays

First scenario (7402 fairbanks_nov21; v14 0.02570, comfort 0.00080), loss and comfort per step:

| candidate | loss | vs v14 | comfort |
|---|---|---|---|
| cu | 0.02756 | +7.2 % | 0.00123 |
| rc | 0.02721 | +5.9 % | 0.00118 |
| curc | 0.03689 | +43.6 % | 0.00272 |
| hp12 | 0.02652 | +3.2 % | 0.00093 |
| hpz | 0.02675 | +4.1 % | 0.00104 |
| hpzrc | 0.03549 | +38.1 % | 0.00250 |

- Every candidate is more than 2 % worse on its first scenario, so by the rule none can pass; the remaining runs
  were skipped (`D:/SmartBuildings_data/v15cold_skip.txt`), the curc run on 7407 was stopped.
- Descriptive (not part of the rule), the building with the largest rooms (7407; v14 0.07584, comfort 0.00896):
  cu 0.11763 (+55.1 %, comfort 0.02162), rc 0.09317 (+22.9 %, comfort 0.01169). Development run (not part of the
  rule): hp12z with the idle zones' extra floor air priced (heat_idle 1) on 7402: 0.02662 (+3.6 %, comfort 0.00101).
- Every variant makes comfort worse, not better. Mechanism (simulator code, `vav.py`): a box's airflow is its damper
  times its maximum times sqrt(P/2000 Pa), and the damper never closes below 0.1 while its air handler runs (the
  outside-air requirement). The static pressure is shared, so a higher cap for one room raises the floor airflow of
  every other box on that air handler; in deep cold that air is the mixed air at about 8 C. The other rooms cool,
  fall below the band, ask for heat in turn, and the pressure stays high.
- With the screen of 27 Oct (an earlier, slab-limited recovery: +10.4 % on training fairbanks_1, +18 % at full size
  in Chicago), both ways to bring the large rooms back on time cost more than the comfort they buy. Reading
  (opinion): in deep cold at full size v14's comfort losses are the cheaper side of this plant's trade-off.

## After stage 1: the other side, a lower boost cap (exploration, 30 Oct 01:30-01:40; no rule, development only)

If more air fails because of the shared pressure, does less air pay? `f_heat_safety` 0.35 instead of 0.45 (zones
below the band by `boost_k` take at most 0.35 of their box), first 2880 steps, frozen/zonal_v15dev_h.py with V14_PARAMS:

| scenario | v14 loss | 0.35 loss | change | comfort v14 -> 0.35 | energy and carbon v14 -> 0.35 |
|---|---|---|---|---|---|
| 7402 fairbanks_nov21, full size | 0.02570 | 0.02584 | +0.55 % | 0.00080 -> 0.00113 | 0.02490 -> 0.02470 |
| 7407 fairbanks_nov21, full size | 0.07584 | 0.08037 | +5.97 % | 0.00896 -> 0.02159 | 0.06689 -> 0.05878 |
| train_1 fairbanks_1, shipped size | 0.05185 | 0.05174 | -0.21 % | 0.00065 -> 0.00103 | 0.05120 -> 0.05071 |

- Less air saves energy (-12 % in 7407) but costs more comfort than it saves; at shipped size the two nearly cancel.
  With the six "more air" candidates above, v14's 0.45 sits at the bottom of both sides. Not pursued (a priced
  choice between caps, `boost_choose`, is coded but not run: both sides lose on 7402 and 7407).
