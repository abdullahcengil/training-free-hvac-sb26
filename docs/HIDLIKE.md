# Where does the public gap come from? (24 Oct 2026, 03:10; written before any run)

The calibration submission (docs/RESULTS_EXTERNAL.md) puts the official pid_water at 1.18 x its training score in
public, against 1.43 x for our controller: by the rule written before, the hidden test is harder for us than for
pid_water (v13/pid_water 0.164 in public, 0.136 in training). Two explanations, tested separately:

1. **pid_water's tank subsidy.** pid_water moves the hot-water setpoint and gains from the tank accounting issue in
   the cold (its loss is 34 % higher in fairbanks_1 under the proposed fix, docs/TANKFIX.md). A cold-heavy hidden set
   would lower its public ratio without any weakness of ours. Test: pid_water on the patched simulator on ten January
   stress scenarios (Chicago, Duluth, Helena, New York, Seattle; `sb/jobs_subsidy.json`), against its shipped runs.
   Reading: a mean increase of at least 15 % means the subsidy alone can explain a large part of the gap.
2. **New buildings and new climates together.** Our blind rounds tested new buildings in known climates (v11/pid_water
   ratio x1.09 against training) and the stress test new climates on known buildings (x1.05); the hidden test does both
   at once. Test: the six round-5 buildings, each in four stress windows (chicago_jan15, helena_jan15, dubai_jul15,
   lasvegas_jul15; `sb/make_hidlike.py`, `sb/jobs_hidlike.json`), v14 and pid_water. Reading: a ratio of means
   v14/pid_water of at least 0.160 reproduces the public gap (then diagnose by component, hour and building); at most
   0.150 does not.

## Result 1: pid_water's tank subsidy (24 Oct, 03:20)

pid_water on the patched simulator against its shipped runs (both ours, same path), ten January stress scenarios:
Chicago +18.4 / +19.2 %, Helena +13.4 / +14.3 %, Duluth +17.3 / +28.7 %, Seattle -2.1 / -2.3 %, New York -1.3 / -3.9 %.
**Mean +10.2 % (ratio of means +13.3 %): below the 15 % mark, so by the rule the subsidy alone does not explain a large
part of the public gap.** It is large in deep cold (13-29 %) and absent in mild winters. Rough reading (opinion): with
warm climates in the hidden set too, pid_water's public score would rise by perhaps 5-7 % under the fix, which would
take our public ratio to pid_water from 0.164 to about 0.155: about a third of the gap to training's 0.136.

## Result 2: new buildings x new climates (24 Oct, 07:13)

v14 and pid_water on the six round-5 buildings, each in four stress windows (24 scenarios, full length):
**ratio of means v14 / pid_water 0.133 (v14 0.01149, pid_water 0.08608): at most 0.150, so by the rule this set does
not reproduce the public gap** (0.164). By window: Chicago January 0.167, Helena January 0.160, Las Vegas July 0.122,
Dubai July 0.098. So the January windows sit at the public level, the July windows far below it.

By building (`sb/hidlike_eval.py`): one building carries it. **Building 7407 has ratios 0.22-0.33 in all four windows**
(the others 0.04-0.22, mostly 0.08-0.15) and is 31 % of v14's loss over the set. It has the largest rooms of the six
(room size 40-48 against 20-40) and the fewest air handlers (3 against 4-7), so the most load per air handler, and the
energy score is normalised per air handler. Where its loss goes (per-step records): in Chicago January v14 burns
0.0185 (energy plus carbon, reward units per step) in empty nights against pid_water's 0.0089 (buildings 7406 and 7408:
0.0094-0.0105 against 0.0092-0.0143); empty nights are a third of v14's cold-weather loss in every building (32-34 %).
In Dubai July v14's occupied-hours energy in 7407 is twice that of the other buildings (0.0427 against 0.019-0.021
per step) while pid_water's is not (0.0615 against 0.088-0.108). The stress test's only weak spot was the same kind
of case (building 7 in Duluth, docs/STRESS_TEST.md).

Reading (opinion): the public gap is consistent with a hidden set that leans to cold continental winters and
high-load buildings; our controller is weakest exactly there (heating through empty nights and recovering before
06:00), and pid_water's tank subsidy is largest there (result 1). Next lever, honest: the night and recovery strategy
in high-load buildings in cold weather (night energy twice pid_water's in building 7407).

## Screen: the recovery airflow cap in high-load buildings (24 Oct, 07:35; rule written before any run)

In cold weather v14 heats through the night along a glide path whose slope comes from the heating rate at
`f_heat_rec` (0.35 of the box maximum); in building 7407 the recovery starts around midnight and its empty-night
energy is four times pid_water's. Size of the lever, not a tuning step (the hidden-like set becomes a development set
for this question): `f_heat_rec` 0.45 and 0.6 on buildings 7407 and 7408, Chicago and Helena January
(`sb/jobs_hidlike_rec.json`). Rule: worth developing as a per-building (capacity-aware) recovery cap only if 0.6 or
0.45 lowers the four-scenario total by at least 5 % against v14 with comfort regret per step at most twice v14's.
(A global 0.45 is already ruled out by training: fairbanks_8 +23 %.)

Result (07:42): `f_heat_rec` 0.45: four-scenario total 0.07718 against v14's 0.07736 (-0.24 %), comfort regret per step
x1.03; 0.6: +0.97 % (building 7408 Chicago +5.1 %), comfort x1.16. **Neither reaches the 5 % mark: the recovery
airflow cap is not what makes the nights expensive in high-load buildings.** The ramp's slope comes from the mass
model's heating rate (the slab has to be warmed as well), so the night energy is mostly heat the building really
needs by 06:00. Not pursued.

## Screen: the glide path's safety factor (24 Oct, 08:39; rule written before any run)

With the airflow cap ruled out, the other knob on the night ramp is `glide_safety` (v14: 0.6606), the fraction of the
modelled heating rate the ramp assumes: a higher value makes the ramp steeper, so recovery starts later. Same four
scenarios and the same rule as the cap screen: worth developing only if 0.8 or 0.9 lowers the four-scenario total by
at least 5 % against v14 (0.07736) with comfort regret per step at most twice v14's (`sb/jobs_hidlike_gs.json`,
results `results/hidlike/gs80`, `gs90`, log `D:/SmartBuildings_data/hidlike_gs.log`, about 25 min).

Result for 0.8 (08:56): four-scenario total 0.07719 against 0.07736 (-0.23 %), comfort regret x1.20: below the 5 % mark. 0.9 was still
running when the session stopped at 09:00; it finished at about 09:05: 0.07708 (-0.37 %), comfort regret x1.33, also below
the mark. The night ramp is not the lever either.
