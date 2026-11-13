# Can the controller tell a full-size building from a shipped one? (30 Oct 2026, 17:41 by `date`)

## Why

At full size, every change that heats a little less lowered v14's loss in the two cold development windows
(docs/FULLSWEEP.md: margin_heat 0.30 -1.49 % and -1.66 %, glide_safety 0.80 -1.45 % in New York, damping 0.60
-1.90 % and -2.07 %), while in hot windows the heating parameters change nothing. On the shipped (scaled) training
buildings the same direction costs: glide_safety 0.80 +5.4 % on three of the cold four, fairbanks_8 +20.7 %
(docs/TUNING_LOG.md, screen b, 23 Oct), and the CMA-ES search on six training scenarios settled at margin_heat 0.395.
Physical reading (opinion): energy is normalised per air handler and comfort per occupant; a full-size building has
about twice the floor area on the same air handlers with about the same number of people (diagnosis traces: 68 vs 70
people in building 7407, 64 vs 58 in 7402, full vs scaled), so a kelvin of heating costs about twice as much reward
there while a kelvin of discomfort costs the same. The cost-optimal heating trade-off moves towards energy.

A legitimate rule can only use what the controller sees. The metadata has no floor areas, the boxes are 2 m3/s in
every generated building, and the occupant count does not grow with size. What remains is the controller's own model
of each zone (Eq. 1 of the paper): its gain g (K per kW per step) and its envelope term b; b/g is the zone's
envelope conductance in kW per K, which grows with the room.

## Diagnostic (no candidate, no decision about v15)

`python -m sb.run_sizegate_diag` runs v15 unchanged (frozen/zonal_v14f.py + V15_PARAMS) for the first 864 steps
(three days) of the cold window of every shipped training building (Fairbanks), every full-size development building
(docs/BIGDEV.md) and the scaled twins in `bigdev_scaled`, with the trace dump of sb.bigbld_dump (internal state
included: each zone's identified mass-model parameters per step) and the true room areas from the simulator (for
reading only; the controller never sees them). 17 traces in `results/sizegate/`.

What is read (sb/sizegate_read.py): per building, after one, two and three days, the median over zones of g, b and
b/g, and their correlation with the true room area. A gate is usable if one of these separates every full-size
building from every shipped and scaled one with room to spare, and is stable from day two on. If none does, the
size-aware rule is dropped and v15 stays.

A candidate rule, its screen and its pass marks will be written in this file after the diagnostic and before any
candidate run. The development scenarios that the diagnostic reads are not the scenarios of a later blind round.

## Upside check (written 30 Oct 17:45 by `date`, before any run; not a candidate)

Is a size-aware rule worth building at all? The sweep moved one parameter at a time. `python -m sb.run_sizegate_upside`
runs one building-wide variant, **hl2** = V14_PARAMS + margin_heat 0.30 + glide_safety 0.80 (the two heating-only
changes that lowered the loss in cold full-size windows), with the frozen v14 file, on the six cold full-size
development windows (bigdev: 7001 Chicago, 7002 Helena, 7003 Duluth, 7005 Chicago, 7007 New York, 7008 Seattle; all
January 15), first 2880 steps. Reference: v14 on the same runs (`results/bigdev/v14`). It starts when the diagnostic
ends (three simulations at most).

Reading rule: the size-aware line goes on only if hl2's mean loss over the six is at least 1.5 % below v14's (the gate
can only keep part of a building-wide gain, and the hidden set also holds hot windows, where these parameters change
nothing). Otherwise it stops here and v15 stays. No scenario-level threshold is applied; the per-scenario changes are
reported. hl2 itself can never be submitted: on the shipped buildings the same direction costs (Why, above).

Addendum (30 Oct 17:51 by `date`, before any of these runs): the same runner also traces v15 unchanged on the six
shipped training buildings in their Fairbanks windows for the full 8640 steps (`train30__*.npz`, description only),
as fillers next to the upside runs. Reason: in the first three days the training buildings' median 1/g stays at
3.38-4.21, but one building rose by 0.46 on day 3; a gate threshold needs their month-long path, not three days.

## First reading of the diagnostic (30 Oct 17:51; two of six full-size traces)

Median 1/g over zones: shipped training buildings 3.38-4.21 after three days (prior 3.70); full-size 7001 Chicago
4.28, 5.55, 7.62 after one, two and three days, 7002 Helena 3.84, 4.41, 6.76. Rank correlation of 1/g with the true
room area over the zones: 0.81 and 0.66 at full size (median rooms 461 and 391 m2, against 78-138 m2 in the shipped
buildings). The signal exists; it needs about three days to form.

Four of six full-size traces (17:54): "full size" is not "large rooms". 7003 (Duluth) has 163 zones of median 136 m2
and 17 air handlers; its median 1/g stays at 3.41 after three days, like the shipped buildings; 7005 (86 zones, median
240 m2) reaches 5.04. Room counts scale with air handlers (9-10 zones per handler everywhere), people do not scale
with room area (rank correlation of a room's peak occupancy with its area -0.03 to 0.19 in all ten traces; 8-19
people per air handler everywhere). Reading (opinion): a kelvin in zone z costs energy in proportion to its envelope
(room size) divided by the number of air handlers, and comfort in proportion to its share of the people, which does not
grow with the room; with zones and people per handler about constant, the trade-off moves towards energy with the
room's size, not with the building's. So the relevant signal is the size of the rooms, which the median 1/g measures.
Prediction for the upside check (written before it runs): hl2 helps in 7001, 7002 and 7005 (median 1/g after three
days 7.62, 6.76, 5.04) and not in 7003 (3.41).

All six full-size traces and two scaled twins (17:58): median 1/g after three days against the median room.

| building | median room (m2) | zones | air handlers | median 1/g, day 1 / 2 / 3 |
|---|---|---|---|---|
| full 7001 (Chicago) | 461 | 46 | 5 | 4.28 / 5.55 / 7.62 |
| full 7008 (Seattle) | 410 | 47 | 5 | 3.76 / 4.67 / 5.88 |
| full 7002 (Helena) | 391 | 40 | 5 | 3.84 / 4.41 / 6.76 |
| full 7007 (New York) | 292 | 94 | 10 | 4.14 / 5.13 / 5.66 |
| full 7005 (Chicago) | 240 | 86 | 9 | 3.79 / 4.03 / 5.04 |
| scaled 7001 | 170 | 50 | 5 | 4.06 / 4.31 / 4.75 |
| scaled 7008 | 162 | 49 | 5 | 3.71 / 3.73 / 3.81 |
| scaled 7002 | 155 | 43 | 5 | 3.72 / 3.74 / 4.12 |
| scaled 7007 | 133 | 83 | 10 | 3.62 / 3.65 / 3.86 |
| scaled 7003 | 53 | 163 | 17 | 3.32 / 3.16 / 2.88 |
| full 7003 (Duluth) | 136 | 163 | 17 | 3.67 / 3.49 / 3.41 |
| shipped training (Fairbanks) | 78-138 | 30-85 | 3-9 | 3.28-3.75 / 3.43-3.75 / 3.38-4.21 |

The order of the median 1/g follows the order of the median room in all but one adjacent pair (7008 and 7002), and
the values keep rising on day 3 in the large-room buildings. By prediction (above), the upside check now also says
whether heating less pays in 7005 and 7007 (median rooms 240 and 292 m2), which sets where a threshold could sit.

## Upside check, first three of six (read 30 Oct 18:16 by `date`): the prediction FAILED for 7003

hl2 against v14, first 2880 steps: 7001 -1.48 %, 7002 -2.76 %, **7003 -3.30 %**. The prediction written before the
check said hl2 would not help in 7003 (163 rooms of median 136 m2, median 1/g 3.41, like the shipped buildings); it
helps there most. So in these windows heating less does not pay because the rooms are large. What separates these
results from the earlier harm on the shipped buildings (glide_safety 0.80: +5.4 % on three of the cold four,
fairbanks_8 +20.7 %, comfort 0.00050 -> 0.00375 per step; TUNING_LOG screen b, 23 Oct) may be the weather: those
were Fairbanks windows in deep cold, these are mild January windows (-4.5 to +4.1 C on average). Opinion, not tested.
Consequence: a gate on room size has no support as a mechanism, whatever the mean of the six turns out to be; the
next step is a screen on the shipped training scenarios, with its rule written before it runs.

## Upside check, all six (read 30 Oct 18:26 by `date`)

hl2 against v14, first 2880 steps: 7001 -1.48 %, 7002 -2.76 %, 7003 -3.30 %, 7005 -1.84 %, 7007 -3.04 %, 7008
-4.86 %; mean 0.00959 against 0.00983, **-2.41 %**, better in 6 of 6. By the rule, heating less is worth pursuing
(mark -1.5 %). Its gain does not follow room size (largest in the mild Seattle window and the small-room Duluth
building), so the size gate is dropped and the line goes on as the margin screen of docs/HEATLESS.md (rule written
18:17, before these last three results and before any of its own runs). The month-long training traces were
dropped (18:20) for the same reason. The 1/g diagnostic stays as a description: the controller's zone model does see
room size (table above), it is just not what decides here.
