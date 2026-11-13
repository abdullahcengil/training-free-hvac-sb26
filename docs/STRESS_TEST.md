# Climate stress test (written 23 Oct 2026, before any run)

**Why.** v12's public score is 1.43 x its training score; on our own held-out rounds (new buildings, mostly the
training stations) v11 was 1.11 x training and pid_water 1.02 x. The hidden test set uses five weather stations that
appear nowhere in training (organisers' paper, arXiv 2610.18511). Either the hidden climates are harder for
everyone, or our controller does worse in climates it has not seen. A calibration submission of the official
pid_water baseline (docs/RESULTS_EXTERNAL.md, 23 Oct) answers the first part; this test looks for the second.

**Data.** Hourly 2023 weather for ten cities, none used so far: Miami, Houston, Las Vegas, San Francisco, New York,
Seattle, Chicago, Helena, Duluth, Dubai (Open-Meteo archive, ERA5, downloaded 23 Oct 16:20 with the user's
approval; raw JSON in `D:/SmartBuildings_data/stress/download`). Converted to the shipped format by `sb/make_stress.py`:
local standard time (the shipped files are local time: their warmest hour is 13-15 h), one convection coefficient
per station from a fit to the six shipped stations' annual mean wind. Two 30-day windows per city (from 15 January
and from 15 July, 06:00); each window with two of the six training buildings (round robin): 40 scenarios. The
buildings are the training buildings unchanged (floor plans and zone maps identical), so only the climate is new.
ERA5 is reanalysis, not airport observations: smoother than station data, so this tests climate, not sensor noise.

**Runs.** v13 (frozen v11 file + `submission/V13_PARAMS.json`) and the official pid_water baseline, full length,
`sb/jobs_stress.json`, results in `results/stress/{v13,pid_water}`.

**Reference (training, fixed now).** v13 against pid_water's shipped returns, ratio of means over the 30 training
scenarios: 0.136 (atlanta 0.159, denver 0.107, fairbanks 0.194, phoenix 0.088, singapore 0.126; single scenarios
0.049-0.296).

**Reading, fixed now.**
1. Overall: the ratio of means v13 / pid_water over the 40 scenarios. At most 0.163 (1.2 x training): our
   controller keeps its advantage in new climates, and the public 1.43 is (mostly) a harder test set. At least
   0.204 (1.5 x training): it loses ground in new climates; find where.
2. Weak spot: a city whose ratio of means over its four scenarios is at least 0.204, or any scenario where v13 is
   worse than pid_water. Each weak spot is diagnosed (loss by component and by hour) before any change.
3. From the first result on, these 40 scenarios are a development set, not a blind test: any change found here is
   checked on the 30 training scenarios and, if it is kept, in a new pre-registered round.

## Result (23 Oct, 20:43; read with `sb/stress_eval.py`, nothing changed before reading)

- 40 of 40 scenarios. v13 0.00740, pid_water 0.05189 (means per step). **Ratio of means 0.143** (training 0.136):
  by rule 1, **v13 keeps its advantage in new climates** (mark 0.163).
- v13 is better than pid_water in all 40 scenarios (ratios 0.047-0.324).
- **Weak spots by rule 2: Chicago 0.236, Duluth 0.233, Helena 0.231** (ratio of means over each city's four
  scenarios; mark 0.204). All three are cold continental climates. The other cities: Seattle 0.167, New York 0.164,
  Miami 0.154, Las Vegas 0.103, San Francisco 0.091, Houston 0.087, Dubai 0.072.

## Diagnosis (rule 2: loss by component and by hour, before any change)

`sb/stress_diag.py` (weather of each window; table in `analysis/stress_weather.csv`) and the per-step records.

- The training set has only three windows with a mean outside temperature below 5 C (fairbanks_1, _2, _8); the
  stress set has ten. The weak cities' January windows (mean -9 to -2 C) fill that gap.
- In the January scenarios v13's loss is 64-71 % carbon and 26-28 % energy cost (gas), comfort 1-11 %; pid_water's
  is 44-72 % comfort. The July scenarios of the weak cities have ratios 0.15-0.17 (mild weather).
- Chicago and Helena (buildings 1 and 5): v13's energy-plus-carbon loss per 1000 heating degree-hours (below 18 C)
  is 1.0-1.1, against 1.5 for building 1 in fairbanks_1 and 1.1 for building 8 in fairbanks_8; comfort is 0.25 x
  1e-3 per step or less in building 1. By hour, v13's loss falls in the recovery (04:00-08:00, about 45 %), as in
  training (39 % in fairbanks_1). pid_water burns less at night and loses comfort all day (its comfort is about half
  its loss), so the ratio rises where the cold is moderate. Reading (opinion): no sign that v13 handles these
  climates worse than the training ones; the high ratio comes mostly from pid_water doing relatively well there.
- Duluth, building 7 (ratio 0.324, the highest of all 40): comfort is 10.6 % of v13's loss and is lost all day, not
  only in the recovery; energy-plus-carbon per 1000 degree-hours is 1.9, against 0.76 for building 2 in the same
  weather. Day by day, building 7's comfort loss jumps on day 8 (mean -4.8 C, milder than the days before) and stays
  high in mild days 22-26, while building 2 stays near zero. So it is not only the extreme cold (days 13-19). Building
  7 has no cold window in training. Next: per-zone dumps of days 7-12 for buildings 7 and 2 (`sb/stress_dump.py`,
  `sb/stressdiag.sh`): are the missing zones at their box's maximum airflow (plant limit), at the policy's heating cap,
  or under-planned by a drifting zone model?
