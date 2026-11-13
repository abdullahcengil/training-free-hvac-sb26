# v16 on the corrected simulator (written 4 Nov 2026, 16:00 by `date`; before any run)

## Why

Hosts (forum 749531 and 751998, about 29 Oct): "Our aim is to run the final verification on the corrected simulator";
no confirmed plan or commit yet. Two energy fixes are proposed: the tank (pull request 2; v13 unaffected,
docs/TANKFIX.md) and return air mixed by airflow instead of floor area (pull request 3, forum 753804, new to us). The
second one is the first thing we have read that could move *our* score: its authors report that the official PID
baseline receives a mean of 43 kW of unbilled heat in one Fairbanks scenario, and needs 15 % more boiler heat once
corrected. v16 sends heat at high airflow to the zones that need it, so it may receive some too, and part of the
leaderboard's lead may come from this issue. We do not know how v16 behaves on it.

## What

`sb/make_fixsim.py` writes the fix (our code, from the description) on top of the tank-fix copy:
`D:/SmartBuildings_data/kit_fixed`. `sb/run_fixsim.py` runs v16 and pid_water, unchanged, on six cold and six hot
full-size development windows, first 2880 steps, against their shipped-simulator runs.

## Reading rule (fixed now)

- If v16's loss rises by less than 3 % in both the cold and the hot set: v16 does not depend on the issue; say so in
  the paper next to the public score.
- If it rises by 3 % or more in either: v16 gets part of its score from it; the paper must say how much, and the next
  candidate is tuned on the corrected copy (setpoints that are optimal there), not on the public leaderboard alone.
- The ratio v16/pid_water on the corrected copy goes into the paper either way, since the final ranking may be
  computed there.

Expectation (opinion): a rise of a few percent in cold weather, more for pid_water; little in hot weather.

## Result, v16 (read 4 Nov 16:48 by `date`)

Cold set +2.1 % (0.00924 to 0.00943; worst window Seattle +4.3 %), hot set +0.1 % (0.01939 to 0.01942). Both means are
below the 3 % mark, so by the rule v16 does not depend on the issue. pid_water's runs follow.

## Result, pid_water (read 4 Nov 17:32 by `date`)

Cold +2.1 % on the five windows with a shipped run (0.06893 to 0.07041; only Duluth moves much, +20.8 %, the others
-1.0 to +0.8 %), hot +0.1 %. My expectation that the baseline would lose much more than v16 was wrong on these windows.
On the corrected copy v16 stays below pid_water in 12 of 12: ratio of means 0.233 (cold 0.132, hot 0.370). Forum figures
for the baseline (+15 % boiler heat) came from one Fairbanks scenario on a different building and are not contradicted;
this set simply does not reproduce that size.
