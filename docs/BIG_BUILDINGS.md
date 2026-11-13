# Are the hidden buildings bigger than ours? (25 Oct 2026, 20:55; written before any run)

The kit's generator samples footprints of 400-700 x 300-500 and rooms of 30-60 (+11-16) cells, 1-2 occupants per
zone (`run_floor_generator.py`, DEFAULT_RANGES), and its README says these "default footprint ranges are larger than
the shipped six". The hidden buildings are "drawn from the same generator and the same parameter ranges". Every
blind round we ran scaled the generated buildings down to the shipped size (`sb/make_heldout.py`, MAX_W 430,
MAX_H 301, rooms scaled too, s = 0.65-0.78 in round 5). So no test of ours has seen full-size buildings, and the one
weak building of the hidden-like set (7407, docs/HIDLIKE.md) is the one with the largest rooms. Raw round-5
buildings have 1.7-2.4 x the floor area and rooms up to 69 cells.

Test: the same seeds unscaled (raw YAMLs in `heldout5/buildings`): buildings 7402, 7407, 7408 in chicago_jan15 and
dubai_jul15 (`sb/make_bigbld.py`), v14 and pid_water, first 2880 steps (10 days); the scaled versions' first 2880
steps come from their full-length records (deterministic simulator, causal policy, so identical to a 2880-step run).
Reading:
- **Size is the missing piece** if the raw ratio of means v14/pid_water is at least 0.160 and at least 1.15 x the
  scaled ratio on the same six pairs: then diagnose and develop on full-size buildings.
- **Not it** if the raw ratio is at most 1.05 x the scaled one.
- In between: unclear; run full length.

## Result, first 4 of 6 pairs (25 Oct, 21:02; building 7408 still running)

| pair (first 2880 steps) | full v14 | full pid_water | ratio | scaled v14 | scaled pid_water | ratio |
|---|---|---|---|---|---|---|
| 7402 chicago_jan15 | 0.00502 | 0.05866 | 0.086 | 0.00539 | 0.04486 | 0.120 |
| 7402 dubai_jul15 | 0.01577 | 0.04720 | 0.334 | 0.00851 | 0.07203 | 0.118 |
| 7407 chicago_jan15 | 0.01793 | 0.10021 | 0.179 | 0.01721 | 0.09680 | 0.178 |
| 7407 dubai_jul15 | 0.03338 | 0.07415 | 0.450 | 0.01748 | 0.05258 | 0.332 |

**Ratio of means full 0.257 against scaled 0.182 (x1.41): by the rule, size is the missing piece.** Level: v14 x1.48
on full-size buildings, pid_water x1.05, close to the public pattern (v14 1.43 x training, pid_water 1.18 x). The loss
is in hot weather: in Dubai v14's loss almost doubles on the full-size buildings (0.0085 -> 0.0158, 0.0175 -> 0.0334)
while pid_water's does not; in Chicago v14 is unchanged. Next: diagnose v14 on full-size buildings in hot weather and
build a full-size development set (raw YAMLs in heldout*/buildings; run sb.fix_heldout_paths after generating).

## Result, all 6 pairs (25 Oct, 21:16)

| pair (first 2880 steps) | full v14 | full pid_water | ratio | scaled v14 | scaled pid_water | ratio |
|---|---|---|---|---|---|---|
| 7402 chicago_jan15 | 0.00502 | 0.05866 | 0.086 | 0.00539 | 0.04486 | 0.120 |
| 7402 dubai_jul15 | 0.01577 | 0.04720 | 0.334 | 0.00851 | 0.07203 | 0.118 |
| 7407 chicago_jan15 | 0.01793 | 0.10021 | 0.179 | 0.01721 | 0.09680 | 0.178 |
| 7407 dubai_jul15 | 0.03338 | 0.07415 | 0.450 | 0.01748 | 0.05258 | 0.332 |
| 7408 chicago_jan15 | 0.01544 | 0.09522 | 0.162 | 0.01151 | 0.05575 | 0.207 |
| 7408 dubai_jul15 | 0.01527 | 0.06845 | 0.223 | 0.00841 | 0.10096 | 0.083 |

**Ratio of means full 0.232 against scaled 0.162 (x1.43): by the rule, size is the missing piece.** Level: v14 x1.50
on the full-size buildings, pid_water x1.05 (public: v14 1.43 x training, pid_water 1.18 x). Building 7408 confirms the
pattern: in Dubai v14's loss rises from 0.0084 to 0.0153 while pid_water's falls; in Chicago v14 rises by a third
(0.0115 -> 0.0154), less than in Dubai. Records: `results/bigbld/{v14,pid_water}`, read with `python -m sb.bigbld_eval`.

## Diagnosis 1: hot weather (25 Oct, 21:25; `sb/bigbld_dump.py`, read with `sb/bigbld_dump_read.py`)

v14 on building 7402 in Dubai, first 2016 steps (Saturday to Friday), full size against scaled (same seed, same AHU
count). Plant-side records from the simulator itself (fan and cooling power as billed, airflow, pressure, supply air):

| | scaled | full size | full / scaled |
|---|---|---|---|
| floor area (m2) | 4793 | 10293 | 2.15 |
| zones / AHUs | 30 / 4 | 34 / 4 | |
| loss (2016 steps) | 0.00881 | 0.01629 | 1.85 |
| cooling power, occupied hours (kW) | 33.3 | 62.7 | 1.88 |
| fan power, occupied hours (kW) | 1.8 | 3.8 | 2.1 |
| cooling power per floor area, occupied (W/m2) | 6.95 | 6.09 | 0.88 |
| AHU airflow / maximum when on (mean, p90) | 0.07, 0.10 | 0.13, 0.17 | |
| supply-air temperature when on | 12.5 C (the coldest allowed) | 12.5 C | |
| occupied zone-steps above the cooling setpoint | 0.4 % | 0.3 % | |
| occupied zone-steps with the box at >= 95 % damper | 0.1 % | 4.4 % | |

Reading:
- **The doubling is the load, not a control failure.** The full-size building has 2.15 x the floor area on the same
  four air handlers, and the energy terms are normalised per air handler (`max_electricity_rate` = 80 kW x AHUs). The
  internal gains alone are 10 W/m2 in comfort time (103 kW here). v14's cooling power per square metre is 12 % lower
  on the full-size building than on the scaled one; comfort is held (0.3 % of occupied zone-steps above the band).
- v14 already runs at the cheapest point of this plant model: the coldest supply air (285 K) at the least airflow
  (13 % of the AHU maximum, pressure near the 200 Pa floor). With mixed air warmer than the zones (30 % outside air at
  35-40 C), every extra unit of airflow costs chiller power for the outside air it brings in, so the coldest supply
  air with the least air is the cheapest way to remove a given heat (cost per unit of heat removed
  (T_mixed - T_sat) / (T_zone - T_sat), lowest at the lowest T_sat).
- Over all three Dubai pairs, v14's loss grows less than the floor area (x1.85, x1.91, x1.82 for area x2.15, x2.08,
  x2.45); in Chicago it hardly grows (x0.93, x1.04, x1.34): heating load follows the envelope, and the larger
  interior carries more internal gains.
- pid_water's loss does not grow with the building because most of it is comfort regret and fan work that do not
  follow the load (its Dubai energy is 0.098 full against 0.104 scaled), so the ratio v14/pid_water rises on large
  buildings without v14 getting worse per square metre.
- Consequence for the public board (opinion): if the hidden buildings are full size, hot-weather scenarios weigh more
  in our public loss than in training (cooling energy per AHU about doubles), for every team alike; the public level
  (1.43 x training) is explained without a weakness of the controller. What is left to look for on full-size
  buildings: boxes at their maximum in large rooms (4.4 % of occupied zone-steps in Dubai) and comfort in cold weather
  (7407 Chicago: comfort regret 0.00196 full against 0.00012 scaled), checked next.

## Replication on five more buildings (rule fixed 27 Oct, 12:13, before any of these runs)

The v15 development set (`D:/SmartBuildings_data/bigdev`, `sb/make_bigdev.py`) holds five more buildings that round 1
also ran scaled: 7001, 7002, 7003, 7007, 7008 (round-1 raw YAMLs; 7005 has no scaled version and is left out), each in
its cold and hot stress window (7001 chicago_jan15 / dubai_jul15, 7002 helena_jan15 / lasvegas_jul15, 7003
duluth_jan15 / houston_jul15, 7007 newyork_jan15 / miami_jul15, 7008 seattle_jan15 / chicago_jul15), first 2880 steps.
v14 at full size is the screen's reference (`results/bigdev/v14`); added now: pid_water at full size
(`results/bigdev/pid_water`), and v14 and pid_water on the same buildings scaled as in round 1
(`heldout/buildings_scaled`, same windows; `D:/SmartBuildings_data/bigdev_scaled`, `sb/make_bigdev_scaled.py`).
Reading, as for the first test (`sb/bigdev_size_eval.py`; the heading first said 12:25, written ahead of the clock; the
rule was committed at 12:13:41, 9cab9e8):
- **Replicated** if the ratio of means v14/pid_water at full size is at least 0.160 and at least 1.15 x the scaled
  ratio on the same ten pairs.
- **Not replicated** if it is at most 1.05 x the scaled ratio; in between, unclear.
- Also reported, not used for the reading: each controller's full/scaled level ratio, cold and hot separately.

## A test on the hidden set itself (rule fixed 27 Oct, 12:23, before its runs and before any submission)

Candidate A of the v15 screen (`frozen/zonal_v15dev_a.py` with V14_PARAMS and glide_sus 1; docs/BIGDEV.md) differs
from v14 only in zones whose slab-limited sustained rate is below their one-step rate. At full size it changes the
large rooms' recoveries (7001 Chicago: loss +18 %). If it leaves every shipped-size building untouched, one public
submission tells whether the hidden buildings have such rooms.
- Premise, checked first: on six shipped training buildings, one scenario each (train_1 fairbanks_1, train_2
  phoenix_6, train_4 fairbanks_4, train_5 singapore_4, train_7 denver_5, train_8 phoenix_4), first 2880 steps, A's
  per-step rewards equal v14's (`results/dev14_8640/of3/*.npy`) at every step. If not, nothing is submitted.
- If the premise holds, A is submitted once (notebook checked with `sb/nbcheck.py`), as an outside check, never as a
  candidate. Reading: a public score equal to v14's 0.01048 (the board shows five decimals) means no hidden room is
  large enough for the slab-limited rate to bind, against the size finding; a score at least 1 % away from it, in
  either direction, means the hidden set has such rooms, as our full-size buildings do; anything between is unclear.
- **Result (12:33): the premise fails on the first building, so nothing is submitted.** On train_1 fairbanks_1 A
  departs from v14 at step 772 and its loss over the 2880 steps is 0.05725 against 0.05185 (+10.4 %): in deep cold the
  slab-limited rate binds in shipped-size rooms too, so A is no clean probe of room size. The other five premise runs
  were dropped once the outcome was fixed; one, train_2 phoenix_6, had already started: there A equals v14 at every
  step (0.00854), so in hot weather the cooling side did not bind in a shipped building.

## Where the extra full-size loss falls (27 Oct; description, `python -m sb.size_parts`)

First test (7402, 7407, 7408; mean loss per step over the first 2880 steps, full size minus scaled):
- v14, cold (x1.13): energy and carbon in occupied steps +0.00079, comfort +0.00042, energy in empty steps +0.00022.
- v14, hot (x1.87): energy and carbon in occupied steps +0.00891, in empty steps +0.00115; comfort -0.00005. In hot
  weather nine tenths of v14's extra loss is the cooling bill of the occupied hours: twice the floor area on the
  same four air handlers, and the bill is normalised per air handler.
- pid_water, cold (x1.29): comfort +0.02283, energy -0.00393; hot (x0.84): comfort -0.01440 (the larger rooms drift
  more slowly out of the band), energy +0.00248. So the ratio rises in hot weather because the baseline's comfort
  loss falls while our controller's cooling bill grows.
- Absolute parts in Dubai (first test, three buildings, first 2880 steps; mean per step): v14 full size comfort
  0.00013, energy cost 0.01731, carbon 0.00403 (scaled: 0.00018, 0.00913, 0.00215); pid_water full size comfort
  0.02895, energy cost 0.02757, carbon 0.00674 (scaled: 0.04335, 0.02414, 0.00770). At full size v14 still uses 38 %
  less energy and carbon than the baseline and holds comfort; its bill doubles with the load per air handler while
  the baseline's grows by 8 % (opinion: its fans and fixed setpoints do not follow the load).

## Replication result (runs finished 27 Oct, 15:48; read 29 Oct, 19:23)

Rule of 27 Oct, 12:13 (section above): replicated if the full-size ratio v14/pid_water is at least 0.160 and at least
1.15 times the scaled ratio. Output of `python -m sb.bigdev_size_eval`, `sb.size_stats` and `sb.size_parts`
(round-1 buildings 7001, 7002, 7003, 7007, 7008; first 2880 steps; mean loss per step):

| pair | full v14 | full pid_water | ratio | scaled v14 | scaled pid_water | ratio |
|---|---|---|---|---|---|---|
| 7001 chicago_jan15 | 0.01714 | 0.09319 | 0.184 | 0.01766 | 0.07459 | 0.237 |
| 7001 dubai_jul15 | 0.03794 | 0.07986 | 0.475 | 0.01657 | 0.05557 | 0.298 |
| 7002 helena_jan15 | 0.00944 | 0.08757 | 0.108 | 0.00857 | 0.06520 | 0.131 |
| 7002 lasvegas_jul15 | 0.02557 | 0.06274 | 0.408 | 0.01144 | 0.06875 | 0.166 |
| 7003 duluth_jan15 | 0.00539 | 0.04303 | 0.125 | 0.01336 | 0.05197 | 0.257 |
| 7003 houston_jul15 | 0.00671 | 0.02635 | 0.255 | 0.00337 | 0.12729 | 0.026 |
| 7007 newyork_jan15 | 0.01097 | 0.07663 | 0.143 | 0.01087 | 0.05138 | 0.211 |
| 7007 miami_jul15 | 0.01271 | 0.04109 | 0.309 | 0.00633 | 0.02619 | 0.242 |
| 7008 seattle_jan15 | 0.00342 | 0.04422 | 0.077 | 0.00432 | 0.03996 | 0.108 |
| 7008 chicago_jul15 | 0.01230 | 0.04180 | 0.294 | 0.00445 | 0.02176 | 0.204 |

- **REPLICATED**: ratio of means 0.237 at full size against 0.166 scaled (x1.43). v14 full/scaled x1.46, pid_water
  x1.02 (first test: x1.50 and x1.05).
- Bootstrap over pairs (`sb.size_stats`): replication alone k = 1.43, 95 % interval 0.87-2.46 (ten pairs do not
  exclude 1 on their own); first test 1.43 (0.97-2.16); all sixteen pairs 1.43 (1.02-2.02).
- By weather: hot windows full 0.378 vs scaled 0.141 (v14 x2.26, pid_water x0.84); cold windows full 0.135 vs scaled
  0.193 (v14 x0.85, pid_water x1.22). The size effect is a hot-weather effect.
- Parts (`sb.size_parts`, replication): v14 hot extra = energy and carbon in occupied steps +0.00956, empty steps
  +0.00102, comfort +0.00004; pid_water hot: comfort -0.01068, energy -0.00147 occupied, +0.00261 empty. Same picture
  as the first test.

## Is there room left in hot weather? (29 Oct, 19:23; description)

Read from `results/bigbld_diag/v14_7402_dubai_full.npz` (building 7402 at full size, Dubai, first 2016 steps; 780
occupied steps) and the simulator code in `starter-kit/smart_buildings/smart_control`:
- Occupied hours: chiller 62.7 kW, fans 3.8 kW, gas 0.25 kW, pumps 0: the chiller is 94 % of the electricity. Of its
  219 kW of heat (implied COP 3.50), 54 kW (25 %) is the outside air and 165 kW the rooms.
- Every plant lever that would lower it sits at a limit the simulator sets: recirculation at its cap 0.7
  (`air_handler.py`, `max_recirculation`), supply air at the action floor 285 K (`config.gin`), static pressure at
  the floor 200 Pa on three of four air handlers (`min_static_pressure`), the handler cannot heat
  (`get_supply_air_temp`), and the box discharge is capped at 308.15 K (`vav.py`). Rooms sit 0.10 K below the band's
  upper edge on average; air handlers run only while a zone asks for heat or cooling (`zonal_v14f.py`).
- Comfort against energy: the comfort term is the occupancy-weighted shortfall, deviation / 5 K, weight 0.6
  (`setpoint_energy_carbon_regret.py`); every zone holds about one person on average whatever its area (0.67-1.35;
  `occ` in the trace), so 0.1 K too warm everywhere costs about 0.012 per step, against about 0.039 per step for the
  whole occupied energy and carbon bill of this building. Letting rooms drift cannot pay.
- Time shifting: the loss per kW of electricity is 0.000414 at 02:00 and 0.000450 at 14:00 in January (0.000445 and
  0.000477 in July; price and carbon together, after the reward's normalisation); a shift to the night gains at most
  7-8 % before storage losses. Precooling was already tried and dropped (+9.5 %, `docs/TUNING_LOG.md`).
- Over v14's 70 full-length runs (30 training, 40 stress), comfort is 1.2 % of the loss; energy and carbon are the
  rest (`results/dev14_8640/of3`).
- Opinion: in hot weather v14 is close to what this simulator allows; the remaining gains we can see are a few tenths
  of a percent (for example a seasonal boiler standby, which saves the tank's standing loss of about 0.3 kW in
  cooling-only months).

## Is there room left in cold weather? (29 Oct, 20:20; description)

Read from `results/bigbld_diag/v14_7407_chicago_full.npz` (building 7407 at full size, Chicago, first 2016 steps):
- Occupied hours: gas 63.6 kW. The coil heat estimated at the 35 °C discharge cap is 63.0 kW (the estimate closes the
  bill); 45.3 kW of it reaches the rooms and 18 kW (28 %) warms the shared supply air (15.9 °C) up to room
  temperature in the heated zones. Airflow: 2.7 m3/s to heated zones, 0.7 at the damper floor, 7.0 to zones the cold
  supply air is cooling (interior rooms with internal gains). So the building heats its perimeter and cools its core
  at the same time from one supply-air temperature.
- That supply air is already close to the warmest the minimum outside air allows (0.7 x room + 0.3 x outside, about
  16.6 °C here, against 15.9 °C chosen): a warmer supply would save at most about 4 % of the occupied reheat, and the
  core would then need more airflow (fan power is 11 % of the occupied cost). The planner prices this trade every step.
- Empty hours carry 47 % of the gas (25 kW over 1392 steps), mostly the morning recovery after the night setback;
  heated rooms then sit 0.6 K above the eco band's lower edge (median), and 43 % of that coil heat goes to rooms already
  more than 1 K above it, which is the recovery towards the comfort band.
- Opinion: as in hot weather, the remaining legitimate gains we can see are a few percent of one part of the bill at
  most, each traded against comfort or fan power the controller already prices; we open no new candidate.

## Does size raise heating in deep cold? (rule fixed 29 Oct, 22:56, before any of these runs)

Why: the size test's January windows were mild: mean outside temperature over their first ten days 0.9 C (Chicago,
four pairs), -2.0 (Helena), -4.5 (Duluth), 3.1 (New York) and 4.1 C (Seattle). In them v14's loss did not grow at full
size (x0.95 over the eight cold pairs). The tank probe now says heating is as large a share of v14's public loss as of
its training loss: the issue removes 0.00348 per step in public against 0.00227 in training, about 0.0013 per step (two
fifths of v14's public gap) more heating than the size test predicts (29 Oct). A full-size
building has about twice the floor area on the same four air handlers, and energy is normalised per air handler; in
mild weather the larger core's internal gains can offset the perimeter's losses, in deep cold they cannot.

Test (`sb/make_coldsize.py`, `sb/run_coldsize.py`): frozen v14 (`frozen/zonal_v14f.py` + V14_PARAMS) on the same
eight buildings as both size tests (7402, 7407, 7408, 7001, 7002, 7003, 7007, 7008), at full size and scaled as in the
blind rounds, in two deep-cold windows no earlier run used: Fairbanks from 21 Nov 2023 06:00 (mean -21.8 C over the
first ten days; starts when training window fairbanks_8 ends) and Duluth from 25 Jan 2023 06:00 (mean -17.7 C; starts
when duluth_jan15 ends); first 2880 steps; 16 pairs. pid_water is not run: the question is v14's own level.
Reading (`python -m sb.run_coldsize --read`; ratio of mean losses full/scaled over the 16 pairs):
- **Size explains the heating part** if the ratio is at least 1.30 and energy plus carbon carries at least half of the
  extra loss.
- **Size does not explain it** if the ratio is at most 1.10.
- In between: partial, reported as such.
- Also reported, not used for the reading: the bootstrap 95 % interval over pairs, each window alone, the split of the
  extra loss into comfort and energy plus carbon, occupied and empty steps.
- Why 1.30: in public the issue removes x1.53 the training amount of heating while the rest of the loss is x1.38; a
  size effect on heating should be of that order where heating dominates.

## Deep-cold result (runs 29 Oct 22:56 - 30 Oct 00:42; read 30 Oct, 00:43)

Output of `python -m sb.run_coldsize --read` (v14, first 2880 steps, mean loss per step):

| building | fairbanks_nov21 full | scaled | x | duluth_jan25 full | scaled | x |
|---|---|---|---|---|---|---|
| 7402 | 0.02570 | 0.02207 | 1.16 | 0.02357 | 0.02021 | 1.17 |
| 7407 | 0.07584 | 0.05852 | 1.30 | 0.07833 | 0.05984 | 1.31 |
| 7408 | 0.05241 | 0.03646 | 1.44 | 0.05352 | 0.03703 | 1.45 |
| 7001 | 0.07863 | 0.05877 | 1.34 | 0.07948 | 0.05980 | 1.33 |
| 7002 | 0.03502 | 0.02600 | 1.35 | 0.03292 | 0.02443 | 1.35 |
| 7003 | 0.01374 | 0.03394 | 0.40 | 0.01256 | 0.02459 | 0.51 |
| 7007 | 0.05135 | 0.04272 | 1.20 | 0.05179 | 0.04365 | 1.19 |
| 7008 | 0.03285 | 0.02803 | 1.17 | 0.02917 | 0.02547 | 1.15 |

- **PARTIAL** by the rule: ratio of means 1.21 (95 % interval over pairs 1.06-1.31; Fairbanks 1.19, Duluth 1.22),
  between 1.10 and 1.30. Energy plus carbon carries 72 % of the extra loss (+0.00783 per step: comfort in occupied
  steps +0.00222, energy and carbon +0.00290 occupied and +0.00272 empty).
- Fourteen of sixteen pairs rise (x1.15-1.45); building 7003 falls in both windows (x0.40, x0.51): its scaled version
  loses more than its full-size one (not yet diagnosed).
- Reading (opinion): at full size v14's deep-cold loss grows by about a fifth, unlike in the mild January windows
  (x0.95), so size explains part of the heating that the public probe shows, not all of it (the probe implies about
  x1.5). These scenarios are large: 0.045 per step at full size, six times v14's training mean, so if the hidden set
  holds any, they weigh heavily in its score.
- The sixteen scenarios are now spent as a test and free for development (deep cold at full size).

## Deep-cold diagnosis (30 Oct, 00:55; description, `sb/cold_diag_read.py` on `results/coldsize_diag`, first 2016 steps)

- 7408 at full size, Fairbanks (mean -21.0 C): loss 0.04611 = energy 0.01253 + carbon 0.03207 + comfort 0.00150.
  Gas 375 kW occupied, 172 kW empty. Outside air the coils must heat (30 % of the air handlers' flow, warmed from
  outside to room temperature): about 212 of the 375 kW occupied; the boxes run at 14 % of their maximum on average
  and 58 % of them sit at the damper floor. Occupied zone-steps below the band: 6.0 %, at the heating caps (0.20-0.30
  of the box: 35 %; 0.40-0.50: 37 %), never at the box maximum.
- 7407 at full size (the largest rooms), same window: loss 0.06711, comfort 0.00741 (scaled: 0.05221, comfort
  0.00072). The three largest rooms (887, 665 and 847 m2, each on a 2 m3/s box) carry 52 % of the comfort loss and
  sit 1.2-1.5 K below the band on average through comfort time; 63 % of the cold zone-steps are at the 0.45 cap
  (f_heat_safety), none above 0.5.
- Monday after the weekend, the same three rooms: 14-16 K below the band through Sunday (the glide floor); recovery
  starts at 20:00, reaches the 0.45 cap at 23:00 and stays there all night and all Monday (air handler at 405 Pa,
  0.45^2 x 2000); the rooms gain about 0.7 K/h and are 4-8 K below the band at 06:00, still 2.4-3.0 K below at 13:00.
  At the box maximum the heat delivered would be about 2.2 times larger.
- Opinion: v14's caps were tuned on shipped-size buildings, where boxes are large for their rooms; at full size in
  deep cold they bind for hours. The heat a late room needs is about the same at any airflow; a higher cap mostly adds
  fan work, and through the static pressure it raises every box's floor airflow on that air handler. The v15 screen
  (docs/V15COLD.md) weighs this.
