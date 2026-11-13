# A heating-cooling limit cycle in fast zones (30 Oct 2026, 20:55 by `date`; written before any run of the option)

## What the margin screen's failure showed (docs/HEATLESS.md)

Traces of the first two days of building_train_8 atlanta_1 (`sb.bigbld_dump`, 600 steps, v15 and mh30;
`results/heatless/trace_*_t8_atlanta1.npz`): the whole loss of mh30 on that Monday sits in one zone (index 20, VAV_28,
air handler 2). At 06:00 it was 1.7 K below its band, the heating net fired (full heat), the zone jumped about 8 K in
one step, the warm net then fired on the lagged reading (full airflow at an 11.9 C supply), the zone fell to 13-14 C,
the heating net fired again, and so on: full heating and full cooling in turn, every three to four steps, from 06:00
to about 16:00. Its occupied shortfall: 37 K person-steps under v15, 270 under mh30. Under v15 the same zone already
swings between 20.6 and 23.2 C, without full effort.

The zone model cannot see this: it identified a gain of 0.31-0.37 K per kW and step and a relaxation of 0.27-0.30 per
step, while the zone moved 8-14 K in a step at full effort and fell back 7-8 K in the next. The warm net's guard
(safety_pred 2: fire only if the heat already in the pipe will not bring the zone back) trusts that model.

How common (scan of all 19 traces with zone states, scratch script chatter_scan.py; full-effort heating and full-effort
cooling in the same zone within two steps): none in the six full-size development buildings, none in five of the six
shipped training buildings (Fairbanks, three days), none in four of five scaled twins; 12 zones of the scaled Duluth
building (7003, 163 small rooms; 179 heat-to-cool flips in three days), where those zones hold 83 % of the occupied
shortfall and comfort is 12.3 % of the loss; and zone 20 of building_train_8 under mh30 (39 flips in 600 steps).

## The option (sb/make_v16ch.py -> D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py)

`cool_hold` n: a zone asked for heat (by the plan or the heating net) in one of the last n steps is not cooled this
step; its box goes to the minimum airflow without reheat and the zone falls back by itself. Idle reheat (just enough
to stop the minimum airflow over-cooling a zone that needs nothing) does not count as heat, so summer cooling is
untouched. With cool_hold 0 the file computes exactly what v15 computes. n = 2 covers the one-step lag of the reading
and the step in which the heat acts.

## Exploration (development scenarios only; no decision is taken from it)

- E1: cool_hold 0 against v15 on the first 576 steps of building_train_8 atlanta_1: every reward term identical.
- E2: building_train_8 atlanta_1 at full length, v15 + cool_hold 2 and mh30 + cool_hold 2, against the recorded v15
  and mh30 runs.
- E3: the scaled Duluth window (bigdev_scaled 7003 duluth_jan15, 2880 steps), v14 + cool_hold 2 against the recorded
  v14 run.

A candidate, its screen and its pass marks are written here before any screen run, and only if the exploration shows
the cycle gone at no visible cost elsewhere. The scenarios above are not those of a later blind round.

## Exploration result (read 30 Oct about 21:10; development scenarios, no decision)

- E1: cool_hold 0 against v15, 576 steps of building_train_8 atlanta_1: identical (largest difference 0.0).
- E2, building_train_8 atlanta_1, full length, mean loss per step against v15's 0.00485: v15 + cool_hold 2 0.00485
  (-0.14 %); mh30 + cool_hold 2 0.00478 (-1.45 %; comfort 0.00007 per step), where mh30 alone had 0.00507 (+4.39 %,
  comfort 0.00026).
- E3, scaled Duluth (bigdev_scaled 7003 duluth_jan15, 2880 steps), against v14's 0.01336: v14 + cool_hold 2 0.00562
  (**-57.9 %**), comfort term 0.00547 -> 0.00023 per step.

Next (not started): write the candidate (v15 + cool_hold 2, with and without margin_heat 0.30), its screen (30
training scenarios at full length, the six cold full-size windows, the scaled set) and pass marks here before any
screen run; then a blind round with its plan stamped before its buildings are generated.

## Candidate and screen (written 30 Oct 23:40 by `date`, before any run of this screen)

**chm** = submission/V15_PARAMS.json + cool_hold 2 + margin_heat 0.30, with
`D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py` (sb/make_v16ch.py applied to frozen/zonal_v14f.py). cool_hold alone
is not a candidate: it changes nothing measurable at full size (no full-effort heat-to-cool flip in any full-size
trace), so its only value would be robustness; with the smaller margin it may also keep the gain of docs/HEATLESS.md
(F: -1.63 %) without the cycle that failed that screen.

Screen (`python -m sb.run_screen_ch`, restartable, three simulations at most), four sets:
- **S**: the five cold windows of the scaled twins (`bigdev_scaled`: 7001 chicago, 7002 helena, 7003 duluth, 7007
  newyork, 7008 seattle; January 15), 2880 steps, v15 (new reference runs: v15 differs from the recorded v14 runs on
  the 16 January holiday) and chm.
- **F**: the six cold full-size development windows of docs/HEATLESS.md, 2880 steps, against v15's runs there
  (`results/heatless/v15_bigdev`).
- **H**: the six hot full-size development windows (`bigdev`: 7001 dubai, 7002 lasvegas, 7003 houston, 7005 lasvegas,
  7007 miami, 7008 chicago; July 15), 2880 steps, against v14's runs (`results/bigdev/v14`; no weekday federal holiday
  falls in these windows, so v15 computes exactly what v14 computes there).
- **T**: the 30 shipped training scenarios at full length (8640 steps), against v15's runs (`results/holiday/ed1_full`).

Reading rule (fixed now): chm goes on to a blind round (round 7, with its own plan stamped before its buildings are
generated) only if all four hold:
- S: no window more than 2 % worse than v15 (mean and comfort reported);
- F: mean at least 1.0 % below v15, no window more than 2 % worse;
- H: mean at most 0.1 % above v15, no window more than 1 % worse;
- T: total at most 0.1 % above v15, no scenario more than 2 % worse.
Otherwise v15 stays and the result is reported (docs, paper appendix). Not independent of what we have seen: atlanta_1
(T) and scaled 7003 Duluth (S) were in the exploration, the F windows in the margin screen. No other value of
cool_hold or margin_heat is tried on these data.

Operational note (30 Oct 23:42): the screen's scheduler was first started with PowerShell's `*>>`, which wrote the
log in UTF-16; it was stopped by PID (its two running simulations kept running) and restarted at 23:42:39 with a plain
text log (`cmd /c ... >> screen_ch.log`); the new scheduler adopted both simulations. No run was lost or repeated, and
no rule or setting changed. The first lines are kept in `screen_ch_utf16.log`.

## Screen result (ended 31 Oct 03:21:12, read 03:21 by `date`): PASS on all four sets

`python -m sb.run_screen_ch --read` (per-scenario rows there; results/chatter/s_v15, s_chm, f_chm, h_chm, t_chm):

| set | runs | v15 | chm | change | better | worst | marks | |
|---|---|---|---|---|---|---|---|---|
| S, five cold scaled windows | 5 | 0.009628 | 0.008842 | -8.16 % | 5 | -1.06 % | worst <= +2 % | pass |
| F, six cold full-size windows | 6 | 0.009388 | 0.009235 | -1.63 % | 6 | -1.23 % | mean <= -1.0 %, worst <= +2 % | pass |
| H, six hot full-size windows | 6 | 0.019387 | 0.019387 | +0.00 % | 0 | +0.00 % | mean <= +0.1 %, worst <= +1 % | pass |
| T, 30 training scenarios, full length | 30 | 0.007193 | 0.007164 | -0.40 % | 18 | +0.09 % (fairbanks_1) | total <= +0.1 %, worst <= +2 % | pass |

Comfort and energy terms summed over each set (reported, no mark): S comfort x0.20, energy -4.11 %; F comfort x1.11,
energy -1.95 %; H identical; T comfort x1.23 (0.00211 -> 0.00260, a rise worth about 0.1 % of the loss), energy
-0.62 %. In T, twelve scenarios changed by less than 0.01 % (all six Singapore ones, four of the six Phoenix ones and
two Atlanta ones), 17 improved, and fairbanks_1 is the only one that got worse (+0.09 %). The training window that
failed the margin screen (building_train_8 atlanta_1, +4.39 % there) is now -1.45 %.

Decision, by the rule above: chm goes on to round 7. Its plan (docs/PREREGISTRATION_7.md, unchanged since commit
c944d79 of 30 Oct 23:43) was copied to `docs/preregistration7/PREREGISTRATION_7_2026-10-31.md` (sha256 9b423afc...)
and stamped at 03:21:35 (two OpenTimestamps calendars) before the round's buildings were generated; the six hashes
the plan names were checked at 03:21:32 and all match.
