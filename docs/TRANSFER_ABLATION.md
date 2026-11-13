# What carries the transfer? (plan written 31 Oct 2026, 07:04, before any run)

## Why

The paper's title says the controller "learns each new building online", and its conclusion says that five physical
numbers per zone, identified in hours, carry everything building-specific. Neither claim has been tested on the final
controller in unseen buildings: the only ablation of online identification is on v7, the first controller, on the
ten-day development set (Appendix "Ablations": fixed g and lambda doubled the loss), and v16 has a different model
(five numbers with a slab node), priors from offline fits on four training traces, and a disturbance estimate. If the
priors alone do as well, the transfer comes from the structure and the priors, not from learning, and the paper must
say so.

## Design

v16 (frozen/zonal_v16f.py, sha256 af9c0d2b..., submission/V16_PARAMS.json) with one part removed or disturbed at a
time, on the twelve full-size buildings of rounds 6 and 7 (first 2880 steps, the rounds' own windows), against v16's
existing runs there (`results/round6h/v16`, `results/round7/chm`). These buildings are no longer blind: the ablation is
post hoc and descriptive, and every arm is reported, whatever it shows.

| Arm | Change |
|---|---|
| nolearn | `rls 0`: the five numbers of each zone stay at their priors, and no disturbance is estimated |
| offset | the five numbers stay at their priors; the disturbance estimate is learned (`policies/zonal_v16_offsetonly.py`, a subclass that loads the frozen file unchanged) |
| half | all five priors halved, learning on |
| double | all five priors doubled, learning on |
| nodelay | `delay_comp 0`: plans and safety nets ignore the heat already in the pipe |

Known-answer check, run first: `offset` with `dist_beta 0` must give exactly the rewards of `nolearn` over 288 steps
(building 7802, Helena). If it fails, the `offset` arm is not reported as an ablation.

Script: `sb/run_transfer_abl.py` (61 runs, three at a time, about five hours); log
`D:/SmartBuildings_data/transfer_abl.log`; read with `python -m sb.run_transfer_abl --read`.

## Measures

Per arm: the ratio of mean losses (arm / v16) over the 12 scenarios, with a 95 % bootstrap interval over scenarios
(10,000 resamples), the number of scenarios in which the arm is worse than v16, and the comfort term.

## What each outcome means for the paper (fixed now)

1. Online learning carries the transfer if `nolearn` is at least 10 % worse than v16, its interval lies above 1, and
   it is worse in at least 10 of 12 scenarios. If `nolearn` is less than 5 % worse, learning is not what transfers:
   the title and the conclusion change to say that the structure (the delay and the slab) and the priors carry it.
   Between 5 and 10 %: reported as a modest contribution, and the title loses "learns".
2. The five numbers matter beyond an offset if `offset` is at least 5 % worse than v16 with its interval above 1;
   otherwise the paper says that the learned offset (integral action) does most of the adapting.
3. The priors need not be right (training-free in the strong sense) if `half` and `double` are each within 5 % of v16
   on the mean and no scenario is worse by more than 15 %; otherwise the paper says how much the priors matter and
   that they came from four training traces.
4. The delay finding matters for transfer if `nodelay` is at least 5 % worse with its interval above 1.

## My expectations, written before the runs (opinion)

- nolearn: 30-60 % worse. Room sizes in full-size buildings range from 20 to 890 m2 on the same 2 m3/s box, so one
  gain cannot fit all zones (the smallest rise 7-10 K per step at full heat, the largest recover at 0.7 K/h).
- offset: 10-30 % worse; an offset cannot fix a wrong gain.
- half and double: within 3 %; ten days are long against the hours learning needs.
- nodelay: 5-30 % worse; ignoring the heat in the pipe should bring back the relay of rounds 1 and 7 in small rooms.

## Result

Known-answer check (read 31 Oct 08:16): `offset` with `dist_beta 0` gave exactly the rewards of `nolearn` over 288
steps (max |difference| 0): PASS, so the `offset` arm is reported as an ablation.

### nolearn (all 12 read 31 Oct 09:06 by `date`)

| scenario | v16 | nolearn | change | comfort term v16 -> nolearn |
|---|---|---|---|---|
| r6 7701 Houston May | 0.00650 | 0.01280 | +96.9 % | 0.00005 -> 0.00666 |
| r6 7702 Miami Jul | 0.01170 | 0.03159 | +170.1 % | 0.00008 -> 0.02087 |
| r6 7703 Dubai Sep | 0.02832 | 0.09442 | +233.4 % | 0.00003 -> 0.06914 |
| r6 7704 New York Oct | 0.00305 | 0.02450 | +704.6 % | 0.00004 -> 0.02270 |
| r6 7705 Chicago Nov | 0.01338 | 0.03132 | +134.0 % | 0.00016 -> 0.01955 |
| r6 7706 Duluth Dec | 0.01043 | 0.03044 | +191.8 % | 0.00041 -> 0.02150 |
| r7 7802 Helena Feb | 0.01720 | 0.03569 | +107.5 % | 0.00034 -> 0.01912 |
| r7 7803 New York Jan | 0.01381 | 0.04302 | +211.6 % | 0.00036 -> 0.03096 |
| r7 7804 Chicago Dec | 0.02253 | 0.05315 | +135.9 % | 0.00281 -> 0.03500 |
| r7 7806 San Francisco Mar | 0.00353 | 0.00965 | +173.2 % | 0.00001 -> 0.00649 |
| r7 7807 Duluth Feb | 0.03601 | 0.06896 | +91.5 % | 0.00148 -> 0.03906 |
| r7 7808 Seattle Nov | 0.00472 | 0.02277 | +382.2 % | 0.00001 -> 0.01882 |

Ratio of means 2.677 (95 % CI 2.269-3.227), worse in 12 of 12, per-scenario ratio median 2.716 (1.915-8.046); comfort
term 0.00048 -> 0.02582 per step, so the whole rise is discomfort (the energy term falls a little).
By rule 1 (at least 10 % worse, interval above 1, worse in at least 10 of 12): online learning carries the transfer.
Above my expectation (30-60 % worse).

### offset (all 12 read 31 Oct 09:24 by `date`)

| scenario | v16 | offset | change | comfort term v16 -> offset |
|---|---|---|---|---|
| r6 7701 Houston May | 0.00650 | 0.00663 | +2.0 % | 0.00005 -> 0.00026 |
| r6 7702 Miami Jul | 0.01170 | 0.01248 | +6.7 % | 0.00008 -> 0.00099 |
| r6 7703 Dubai Sep | 0.02832 | 0.04261 | +50.5 % | 0.00003 -> 0.01523 |
| r6 7704 New York Oct | 0.00305 | 0.00436 | +43.1 % | 0.00004 -> 0.00148 |
| r6 7705 Chicago Nov | 0.01338 | 0.01335 | -0.2 % | 0.00016 -> 0.00048 |
| r6 7706 Duluth Dec | 0.01043 | 0.01132 | +8.5 % | 0.00041 -> 0.00154 |
| r7 7802 Helena Feb | 0.01720 | 0.01725 | +0.3 % | 0.00034 -> 0.00084 |
| r7 7803 New York Jan | 0.01381 | 0.01560 | +13.0 % | 0.00036 -> 0.00241 |
| r7 7804 Chicago Dec | 0.02253 | 0.02552 | +13.2 % | 0.00281 -> 0.00601 |
| r7 7806 San Francisco Mar | 0.00353 | 0.00357 | +1.0 % | 0.00001 -> 0.00005 |
| r7 7807 Duluth Feb | 0.03601 | 0.04053 | +12.6 % | 0.00148 -> 0.00790 |
| r7 7808 Seattle Nov | 0.00472 | 0.00503 | +6.5 % | 0.00001 -> 0.00039 |

Ratio of means 1.158 (95 % CI 1.058-1.284), worse in 11 of 12, median 1.076 (0.998-1.505); comfort term 0.00048 ->
0.00313. By rule 2 (at least 5 % worse, interval above 1): the five numbers matter beyond an offset. The learned
offset closes most of the no-learning gap (2.68 -> 1.16). Within my expectation (10-30 % worse).

Day by day (`--days`, loss ratio to v16 summed over the 12 scenarios; day 1 and days 7-8 are mostly weekend days,
when comfort does not count): nolearn 0.99 1.95 2.82 3.05 3.09 3.69 1.03 0.92 2.46 3.29; offset 0.98 0.98 1.23 1.17
1.20 1.29 1.00 0.91 1.21 1.19. Without learning the gap opens on the first work day and widens through the week.

### half (all 12 read 31 Oct 10:16 by `date`)

| scenario | v16 | half | change | comfort term v16 -> half |
|---|---|---|---|---|
| r6 7701 Houston May | 0.00650 | 0.00651 | +0.2 % | 0.00005 -> 0.00002 |
| r6 7702 Miami Jul | 0.01170 | 0.01174 | +0.4 % | 0.00008 -> 0.00006 |
| r6 7703 Dubai Sep | 0.02832 | 0.02839 | +0.3 % | 0.00003 -> 0.00007 |
| r6 7704 New York Oct | 0.00305 | 0.00325 | +6.7 % | 0.00004 -> 0.00012 |
| r6 7705 Chicago Nov | 0.01338 | 0.01383 | +3.3 % | 0.00016 -> 0.00053 |
| r6 7706 Duluth Dec | 0.01043 | 0.01088 | +4.3 % | 0.00041 -> 0.00063 |
| r7 7802 Helena Feb | 0.01720 | 0.01737 | +1.0 % | 0.00034 -> 0.00035 |
| r7 7803 New York Jan | 0.01381 | 0.01455 | +5.4 % | 0.00036 -> 0.00085 |
| r7 7804 Chicago Dec | 0.02253 | 0.02409 | +6.9 % | 0.00281 -> 0.00380 |
| r7 7806 San Francisco Mar | 0.00353 | 0.00366 | +3.6 % | 0.00001 -> 0.00006 |
| r7 7807 Duluth Feb | 0.03601 | 0.03624 | +0.7 % | 0.00148 -> 0.00133 |
| r7 7808 Seattle Nov | 0.00472 | 0.00479 | +1.4 % | 0.00001 -> 0.00000 |

Ratio of means 1.024 (95 % CI 1.010-1.043), worse in 12 of 12, median 1.024 (1.002-1.069); comfort term 0.00048 ->
0.00065. Day by day: 1.108 on the first day (a Sunday), then 1.00-1.04. Within my expectation for the mean (within
3 %), but worse in every building: learning makes up for most of a twofold error in a day, not all of it in ten.
Rule 3 is read when `double` is in.

### double (all 12 read 31 Oct 11:09 by `date`)

| scenario | v16 | double | change | comfort term v16 -> double |
|---|---|---|---|---|
| r6 7701 Houston May | 0.00650 | 0.00672 | +3.5 % | 0.00005 -> 0.00031 |
| r6 7702 Miami Jul | 0.01170 | 0.01185 | +1.3 % | 0.00008 -> 0.00028 |
| r6 7703 Dubai Sep | 0.02832 | 0.03171 | +12.0 % | 0.00003 -> 0.00383 |
| r6 7704 New York Oct | 0.00305 | 0.00333 | +9.3 % | 0.00004 -> 0.00032 |
| r6 7705 Chicago Nov | 0.01338 | 0.01334 | -0.4 % | 0.00016 -> 0.00023 |
| r6 7706 Duluth Dec | 0.01043 | 0.01048 | +0.5 % | 0.00041 -> 0.00062 |
| r7 7802 Helena Feb | 0.01720 | 0.01708 | -0.7 % | 0.00034 -> 0.00060 |
| r7 7803 New York Jan | 0.01381 | 0.01361 | -1.5 % | 0.00036 -> 0.00036 |
| r7 7804 Chicago Dec | 0.02253 | 0.02067 | -8.3 % | 0.00281 -> 0.00161 |
| r7 7806 San Francisco Mar | 0.00353 | 0.00353 | -0.1 % | 0.00001 -> 0.00003 |
| r7 7807 Duluth Feb | 0.03601 | 0.03638 | +1.0 % | 0.00148 -> 0.00271 |
| r7 7808 Seattle Nov | 0.00472 | 0.00474 | +0.5 % | 0.00001 -> 0.00007 |

Ratio of means 1.013 (95 % CI 0.973-1.056), worse in 7 of 12, median 1.005 (0.917-1.120); comfort term 0.00048 ->
0.00091. Day by day: 0.96 0.95 1.11 1.02 1.01 1.04 1.00 0.94 1.01 0.99.

Rule 3 (half and double each within 5 % of v16 on the mean, no scenario worse by more than 15 %): half +2.4 % (worst
+6.9 %), double +1.3 % (worst +12.0 %): met. The priors need not be right; learning makes up for a twofold error
either way, at a small cost (worst in hot Dubai and New York in October when the gain is overestimated: too little
cooling at first). Post hoc and not a candidate: doubled priors helped the round-7 Chicago building (-8.3 %), whose
smallest rooms are the fastest.

### nodelay (all 12 read 31 Oct 12:00 by `date`; "transfer ablation END" logged 12:00:28)

| scenario | v16 | nodelay | change | comfort term v16 -> nodelay |
|---|---|---|---|---|
| r6 7701 Houston May | 0.00650 | 0.00651 | +0.2 % | 0.00005 -> 0.00007 |
| r6 7702 Miami Jul | 0.01170 | 0.01171 | +0.1 % | 0.00008 -> 0.00009 |
| r6 7703 Dubai Sep | 0.02832 | 0.02833 | +0.1 % | 0.00003 -> 0.00007 |
| r6 7704 New York Oct | 0.00305 | 0.00317 | +4.0 % | 0.00004 -> 0.00011 |
| r6 7705 Chicago Nov | 0.01338 | 0.01352 | +1.0 % | 0.00016 -> 0.00023 |
| r6 7706 Duluth Dec | 0.01043 | 0.01104 | +5.8 % | 0.00041 -> 0.00083 |
| r7 7802 Helena Feb | 0.01720 | 0.01737 | +1.0 % | 0.00034 -> 0.00043 |
| r7 7803 New York Jan | 0.01381 | 0.01441 | +4.3 % | 0.00036 -> 0.00080 |
| r7 7804 Chicago Dec | 0.02253 | 0.02406 | +6.8 % | 0.00281 -> 0.00391 |
| r7 7806 San Francisco Mar | 0.00353 | 0.00360 | +2.0 % | 0.00001 -> 0.00005 |
| r7 7807 Duluth Feb | 0.03601 | 0.03604 | +0.1 % | 0.00148 -> 0.00137 |
| r7 7808 Seattle Nov | 0.00472 | 0.00475 | +0.5 % | 0.00001 -> 0.00001 |

Ratio of means 1.019 (95 % CI 1.005-1.039), worse in 12 of 12, median 1.010 (1.001-1.068); comfort term 0.00048 ->
0.00067. Day by day: 1.01-1.03 every day. By rule 4 (at least 5 % worse with the interval above 1): NOT met. The
delay compensation is worth about 2 % in v16, consistently but little; most in the two buildings with small, fast rooms
(round-7 New York and Chicago, +4.3 and +6.8 %) and in two cold round-6 windows; nothing in hot weather. Below my
expectation (5-30 %). Reading (opinion): the relay that the delay-aware cooling net was built against (round 1) is now
also blocked by the cool-hold rule, itself a response to the lag, which `nodelay` keeps; and v8's ablation on the
ten-day development set had found 6 % for delay compensation.

## Summary (31 Oct 12:00)

| variant of v16 | loss / v16 (95 % CI) | worse in | comfort term | rule |
|---|---|---|---|---|
| no online learning | 2.68 (2.27-3.23) | 12 of 12 | 0.02582 | 1 met: learning carries the transfer |
| offset learned, five numbers at priors | 1.16 (1.06-1.28) | 11 of 12 | 0.00313 | 2 met: the five numbers matter beyond an offset |
| priors halved | 1.02 (1.01-1.04) | 12 of 12 | 0.00065 | 3 met (with double): the priors need not be right |
| priors doubled | 1.01 (0.97-1.06) | 7 of 12 | 0.00091 | |
| no delay compensation | 1.02 (1.005-1.04) | 12 of 12 | 0.00067 | 4 not met: about 2 % |
| v16 | 1 | | 0.00048 | |

By the rules fixed before the runs: the title's "learns each new building online" stands, and the conclusion's "five
numbers per zone carry what is building-specific" is supported; the delay compensation is a small part of the
transfer, so the paper must not present it as a main carrier (the lag still matters through the safety nets and the
cool-hold rule: rounds 1 and 7). Figure: `python -m sb.fig_transfer_abl docs/fig/fig_transfer_abl.png`.

Context (no new runs; sb/params_read.py on the size-gate traces of v15, day 3): the learned gain's median is 0.275 in
the six shipped buildings, 0.290 in the scaled twins and 0.213 in the full-size ones (interquartile range 0.162-0.275),
against the prior 0.27, so the priors fit the shipped buildings. Per full-size building (computed 31 Oct, written 12:05 by `date`):
medians 0.142 (7001 Chicago), 0.159 (7002 Helena), 0.295 (7003 Duluth), 0.210 (7005 Chicago), 0.181 (7007 New York),
0.178 (7008 Seattle); the highest zone's gain over the lowest within a building 2.0-3.6. The gains differ both by
building and by zone.

## What next (written 31 Oct 12:09 by `date`)

Exploration, no decision: `sb/run_explore_learn.py` (arm `pv10`: v16 with the RLS prior variances ten times larger,
so the five numbers move faster in the first hours) on the six cold and six hot full-size development windows and four
training scenarios at full length, against v16's existing runs. It runs after the delay-aware heating-net exploration
(`chain_explore_learn.cmd` waits for "explore sp1 END"). A candidate follows only if it shows a gain above 1 % without
large losses, with its screen and pass marks written before any run.
