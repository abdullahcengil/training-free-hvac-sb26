# Training set and Kaggle (descriptive, not pre-registered)

Neither number below was used to choose or tune anything. v8 is the round-2 frozen file (`e8dbcd3`, `{"safety_pred": 2, "dist_obs": 1}`).

## The 30 training scenarios, full length (8640 steps)

| controller | score (mean \|reward per step\|) | / pid_water |
|---|---|---|
| pid_water (shipped returns) | 0.0542 | 1 |
| v7 (round-1 frozen) | 0.03185 | 0.588 |
| v8 (round-2 frozen) | 0.01252 | 0.231 |

- v8 per scenario: median 0.00934, range 0.00345 to 0.06625.
- The six Fairbanks scenarios are 20 % of the scenarios but 39 % of v8's total loss (0.148 of 0.376). The worst two are `building_train_1/fairbanks_1` (0.066) and `building_train_8/fairbanks_8` (0.037). Even there v8 beats every baseline.
- Results: `D:/SmartBuildings_data/results/train_8640/{zonal,v8}`.

## Kaggle public leaderboard

- 17 Oct 2026: v8 notebook (`submission/zonal_v8_submission.ipynb`), public score **0.01687**, rank **44**.
- The public board scores about a third of the 30 hidden scenarios.
- The Kaggle sample run (`building_train_1/atlanta_2`) gave −0.005702 per step. Local v8 gives −0.0057005 on the same scenario, so the code runs the same there.
- Reading: 0.01687 lies inside the training-set spread. With a dozen scenarios, one or two cold-climate ones move the mean this much (derived from the table above). The public board is not used for tuning.
- 21 Oct 2026 (reported by the user): v9 notebook (`submission/zonal_v9_submission.ipynb`), public score **0.01623**, about rank 120 of about 240. That is 3.8 % below v8's 0.01687; on the 30 training scenarios v9 is 4.2 % below v8. Not used for tuning.
- 22 Oct 2026: v10 notebook (`submission/zonal_v10_submission.ipynb`), built after round 4 was scored from the round-4 frozen file (`24f07c3`) and `docs/preregistration4/V10_PARAMS.json`. `sb/nbcheck.py` runs the notebook's own code (gateway wrapper included) next to the frozen file on building_train_1/atlanta_2: identical actions for 2016 steps, and the total reward (-2.694860) equals the first 2016 steps of the training run `results/train_8640/v10c`. Expected Kaggle sample run (building_train_1/atlanta_2, full length): about -0.005372 per step (v10, local), against -0.005702 for v8. On the 30 training scenarios v10 is 8.9 % below v9; on round 4 it is 6.1 % below v9.
- 23 Oct 2026, about 02:15 (read in the user's browser, Kaggle submissions page): the user's notebook `smartblabla`
  (private) holds the submissions: versions 1-2 v8 ("testing_rn", 0.01687), version 3 v9 (0.01623), version 4 v10
  (0.01543), version 5 v11 (submitted 22 Oct about 22:15, still running). The user approved on 23 Oct that v12 is
  submitted from their browser once it is better than v11 on all 30 training scenarios and its notebook is verified.
- 23 Oct 2026, about 02:20, the user (leaving): the 5 daily submissions may be used for further trials when they are
  useful, including trials that gather information. Practice kept from here on: parameters and mechanisms are still
  chosen on training scenarios and checked on pre-registered held-out rounds; a public score can set research
  priorities (for example which climate to work on), and every such use is written down here.
- 23 Oct 2026, about 02:50, plan for today's submissions (written before any of them is made; v11's public score not
  yet known): (1) v12 = the frozen v11 file with V11_PARAMS plus the screen-chosen heating boost (`boost_k`), only if
  it is better than v11 on all 30 training scenarios and its notebook passes `sb/nbcheck.py`; (2) two one-change
  ablations of v11, for the paper's test-set ablation table and to learn how much of the public test loss is heating
  and how much cooling: v11 with `dp_reset` 0 (heating side only; -7.8 % on the cold four in training) and v11 with
  `cool_glide` 0 (cooling side only; -11.6 % on the warm four). Their public scores are reported whatever they are;
  they are not used to choose v12's or any later parameters, only to decide which climate to work on next.
- How the two ablations will be read (written 23 Oct 03:05, before either was submitted): the ratio public(ablation) /
  public(v11) is compared with the same ratio on the 30 training scenarios (both ablations will be run there at full
  length for the paper). A public ratio close to the training ratio means the mechanism transfers and the test set's
  heating (or cooling) share is like the training set's; a much larger ratio means the test set leans more that way; a
  ratio near or below 1 means the mechanism does not help on the test buildings (for the pump reset this would point at
  a valve or coil assumption, Kv 0.108, that may not hold there) and is a research question, not a reason to retune.
- 23 Oct, 03:10-03:15: both ablation notebooks pass `sb/nbcheck.py` against `frozen/zonal_v11f.py` with their own
  parameters (building_train_1/atlanta_2, 576 steps, identical actions; total reward -0.504183 with `dp_reset` 0,
  -0.431048 with `cool_glide` 0). Imported into the user's notebook `smartblabla` from the user's browser: version 6
  (`dp_reset` 0) and version 7 (`cool_glide` 0), each differing from version 5 (v11) in one line, the PARAMS line
  (Kaggle's version diff: +1 -1). Both commit runs started; submission after they finish.
- 23 Oct, about 03:34 (UTC+2), submitted from the user's browser under the user's standing permission for trials:
  version 7 (`cool_glide` 0) and then version 6 (`dp_reset` 0), each with the description "Ablation of v11 (one
  change) ... for the paper's test-set ablation table; not used for tuning". v11 (version 5) was still running
  (5 h 20 min after submission). Three submissions left for the day after these two.
- 23 Oct, about 04:55: v12 meets both conditions set before its run (better than v11 on the 30 training scenarios:
  0.00739 vs 0.00744; notebook check passed); submitted from the user's browser under the user's approval of 23 Oct
  ("v12'yi onaylıyorum bittiği zaman gönderebilirsin"), with a one-line notice to the user first.
- 23 Oct, read about 04:54: **v11 public score 0.01071** (version 5; submitted 22 Oct about 22:15), rank 55 on the
  public board (54 teams lower). v10 was 0.01543, so v11 is 30.6 % lower in public, close to its training gain
  (-31.9 %) and a little more than its held-out gain (-27.8 %). The estimate written before the score was known was
  0.0100-0.0111 (opinion); public/training ratio 1.44 (v10 1.41, v9 1.35, v8 1.35). Board at the same time: 1st
  0.00578, 12th 0.00664, 13th 0.00744, 15th 0.00780, 20th 0.00918; between 0.0100 and 0.0107 the board is dense
  (about 20 teams). Not used for tuning.
- 23 Oct, about 05:12: **v12 submitted** (notebook `smartblabla` version 8, "v12: v11 + boost_k 0.25"; its commit run on
  the sample scenario finished with submission.parquet; Kaggle's version diff against the previous version is the
  PARAMS line only). Two submissions left for the day. Final-submission selection left to Kaggle's automatic choice
  (best two public scores) until the user decides.
- 23 Oct, 08:15, training counterparts of the two ablations (30 scenarios, full length, frozen v11 file,
  `results/dev12_8640/abl_{dp0,cg0}_all30`; written before either public score was known): v11 without the pump
  pressure reset 0.00792 vs 0.00744, **ratio 1.064** (cold 1.095, warm 1.030; worse in 19 of 30); v11 without the
  cooling glide 0.00802, **ratio 1.079** (cold 1.013, warm 1.152; worse in 30 of 30).
- 23 Oct, read about 10:07: **v11 without the pump pressure reset (version 6): public 0.01133**, ratio to v11's 0.01071
  **1.058**, against 1.064 on the 30 training scenarios (cold 1.095, warm 1.030). Reading (opinion, as set out before
  the score): the mechanism transfers to the hidden buildings at about its training size, so the valve and coil
  assumption it rests on (Kv 0.108) holds there too; if the training ratios per climate carried over, the public
  ratio would put about 43 % of the public loss in heating-dominated scenarios, against about 53 % in training (a
  rough split, two ratios and one unknown). Not used for tuning. The cooling-glide ablation is still running.
- 23 Oct, read about 10:53: **v11 without the cooling glide (version 7): public 0.01153**, ratio to v11 **1.077**,
  against 1.079 on the 30 training scenarios (cold 1.013, warm 1.152). Reading (opinion): both mechanisms transfer to
  the hidden test set at about their training size (pump reset 1.058 vs 1.064; cooling glide 1.077 vs 1.079). Solving
  each ablation's public ratio for the share of the public loss in heating-dominated scenarios gives 0.43 (pump reset)
  and 0.54 (cooling glide), against about 0.53 in training: the public loss is split between heating and cooling
  about as in training, so the higher public level (1.44 x training for v11) points to harsher conditions or harder
  buildings within both kinds, not to a different mix or a mechanism that fails on new buildings. Not used for tuning.
- 23 Oct, read about 11:33: **v12 public score 0.01058** (version 8), rank 52; v11 0.01071, so -1.2 % in public
  against -0.7 % in training (the stronger boost helps most in the coldest scenarios, fairbanks_1 -3.1 % in
  training). Board at the same time: 13th 0.00688, 15th 0.00780, 16th 0.00789. Kaggle's automatic final selection
  (best two public scores) is now v12 and v11.
- 23 Oct, version saved 15:48, submitted 16:00: **v13** (notebook version 9, Diff +1 -1, "v13: v12 + glide_floor -16 + f_heat_rec 0.35";
  `submission/zonal_v13_submission.ipynb`, `submission/V13_PARAMS.json`). Written before the public score: training
  0.00735 vs v12's 0.00739 (-0.44 %; cold -0.83 %, warm -0.02 %). At v12's training-to-public ratio (1.43) the
  expected public score is about 0.0105; a change of this size may not show on a third of the test set.
- 23 Oct, 16:30: **calibration submitted (notebook version 10): the official pid_water baseline, unchanged**
  (`policies/pid_water_official.py` = starter kit `baselines/pid.py` + `baselines/pid_plus.py` verbatim;
  `submission/pid_water_calibration.ipynb`; identical actions to the package's `PIDWaterResetPolicy` for 576 steps on
  atlanta_2). Why: v12's public score is 1.43 x its training score, but on our own held-out rounds (new buildings,
  mostly training stations) v11 was 1.11 x training and pid_water 1.02 x. The hidden test uses five climate stations
  that appear nowhere in training (organisers' paper, arXiv 2610.18511). Reading, written before the score, with
  pid_water's shipped training mean 0.05414: if its public score is at least 1.30 x that, the test set is harder for
  both and there is no climate gap worth chasing; if at most 1.20 x, our controller loses at least 19 % against the
  baseline on the unseen climates, and a stress test on more climates is worth doing. In between: unclear. Caveat:
  the organisers' paper calls the public subset "rotating"; if it changed between submissions, the ratio is rough.
- 23 Oct, read 22:45: **v13 public score 0.01051** (notebook version 9; submitted 16:00), rank 54 of 303. v12 0.01058,
  so -0.66 % in public against -0.44 % in training; expected about 0.0105 (written before). Public/training ratio 1.43
  (v12 1.43). Board at the same time: 1st 0.00577, 8th 0.00647, 13th 0.00688, 15th 0.00720. The calibration run
  (version 10, submitted 16:30) is still scoring. Kaggle's automatic final selection is now v13 and v12.
- 24 Oct, read 02:20: **calibration (official pid_water, version 10): public 0.06404**, 1.183 x its shipped training
  mean 0.05414. By the rule written before (at most 1.20): **the hidden test is not much harder for pid_water, so our
  controller loses ground there**: v13's public/training ratio is 1.43, i.e. about 1.21 x pid_water's; v13/pid_water is
  0.164 in public against 0.136 in training. Caveat found after the rule was written (docs/TANKFIX.md): pid_water moves
  the hot-water setpoint and gains from the tank accounting issue in cold climates (its loss would be 34 % higher in
  fairbanks_1 under the proposed fix), so a cold-heavy test set would lower its public ratio; part of the 1.21 may be
  that. The gateway (`kaggle_evaluation/gateway.py`, read 24 Oct) loads each scenario with the same
  `evaluate.load_hybrid_environment` and metadata builder as our runs, the same occupancy normalisation (125.0), 48
  scenarios, 8640 steps each; so the gap is not a pipeline difference.
- 24 Oct, ~02:45: **v14 submitted** (notebook version 11, "v14: v13 + offset_free 3", 825 s run, Diff +929 -874 against
  the calibration version: v13's 907 code lines plus the 22 of the option). Expected public: about 0.0104 (training
  -0.37 %, stress -1.30 %).
- 24 Oct, 08:37: v14 (notebook version 11, submitted ~02:45) still scoring. Meanwhile the public-gap tests
  (docs/HIDLIKE.md): pid_water's tank subsidy in new cold climates +10.2 % (explains about a third of the gap,
  opinion); new buildings x new climates give v14/pid_water 0.133 (January windows 0.16-0.17, one high-load building
  carries the set), so the public ratio is consistent with a hidden set that leans to cold continental winters and
  high-load buildings.
- 25 Oct, read 20:40: **v14 public score 0.01048** (notebook version 11), v13 0.01051: -0.29 % in public against -0.37 %
  in training (expected about 0.0104). Board at 20:40: 1st 0.00521, 8th 0.00603, 15th 0.00653, 20th 0.00720;
  14 teams below 0.0065, 38 in the 0.0095-0.0110 block.
- 27 Oct, read 12:05 (public board): 1st 0.00514, 2nd 0.00521, 3rd 0.00530, 10th 0.00604, 15th 0.00633, 20th 0.00658;
  v14 0.01048, rank 71 of 387 (no submission since 24 Oct). The ten leading scores are now at or below the
  free-heating estimate of 23 Oct (0.0060-0.0063 for v11, TUNING_LOG.md).
- 29 Oct: a probe of an accounting issue in the shipped simulator (reported on the forum by other teams; never used
  for a submission choice) is not part of this release.
- 29 Oct, read about 22:45 (public board, 434 teams): 1st 0.00470, 2nd 0.00514, 5th 0.00547, 10th 0.00597, 20th 0.00627,
  30th 0.00674; the user's team (best score: the tank probe) 32nd. With exact numbers the probe removes 0.00348 per step
  in public against 0.00227 in training; the size test predicts about 0.0022 (cold-window loss x0.95 at full size), so
  about 0.0013 per step, two fifths of v14's public gap (0.0032), is heating that size does not reproduce (opinion).
- 30 Oct, 06:00 (by `date`, 06:01 when logged): **v15 notebook imported** into the user's notebook `smartblabla` as
  version 14, "v15: v14 + empty_day (holidays)" (Save & Run All; the editor draft held the user's tank probe, which
  stays saved as version 13). Its commit run on the sample scenario started; not submitted until the full-length check
  of docs/HOLIDAY.md passes (43 of 43 holiday windows better, -1.79 %, read 05:55; the 27 windows without a holiday
  still running).
- 30 Oct, written before the submission (07:50 by `date`): **v15** = the frozen v14 file with V14_PARAMS plus
  `empty_day` 1, `empty_h` 1.0 (`submission/zonal_v15_submission.ipynb`, notebook `smartblabla` version 14, commit run
  777 s, successful; its PARAMS line read from the rendered notebook equals `submission/V15_PARAMS.json`). Evidence
  before sending: screen 10 of 10 better (-1.60 % of the 30-day loss); round 6 (blind, six full-size buildings,
  ten-day holiday windows) -2.67 %, 6 of 6 (docs/RESULTS_ROUND6.md); all 70 development windows at full length -1.28 %
  (43 with a weekday holiday all better, -1.79 %; the other 27 identical step for step; training 30: 0.007193 against
  0.007328, -1.85 %). Expected public: v14's 0.01048 times (1 - x) with x about 1-2 % if the hidden windows hold
  weekday US federal holidays about as often as ours (43 of 70), unchanged if they hold none. Reading: a public change
  from -0.5 % to +0.5 % means the public windows hold few weekday holidays (or the hidden schedule lists them); below
  -0.5 % confirms the rule there; above +0.5 % would mean harm we did not see, and v14 stays the final selection. Not a
  reason to tune anything.
- 30 Oct, 07:52 (by `date`): **v15 submitted** (notebook `smartblabla` version 14, output `submission.parquet`;
  description "v15 = v14 + empty_day 1, empty_h 1.0 (a work day nobody has entered by 07:00 runs as unoccupied: US
  federal holidays). Training 30: 0.00719 vs 0.00733 (-1.85 %); blind round 6: -2.67 %, 6 of 6."). Status on the
  submissions page: "Notebook Running". The final-selection boxes are empty (0 of 2), so Kaggle would pick the two best
  public scores, now the user's tank probe and v14; the selection is the user's.
- 30 Oct, read 15:20 (by `date`; still scoring at 13:20): **v15 public score 0.01035** (notebook `smartblabla`
  version 14, submitted 07:52). v14 0.01048, so -1.24 % (-1.15 to -1.34 % within the board's five-decimal rounding),
  against -1.85 % in training; expected about 0.0103 (1-2 % below v14, written at 07:50). By the rule written before
  (below -0.5 %), this confirms the holiday rule on the public windows. v15 matches v14 step for step on every day
  that is not an empty work day (27 of 27 development windows without a holiday), and the scoring is deterministic (v8
  scored the same twice), so the public windows hold work days on which nobody comes in, as the occupancy model's
  US federal holidays do. Public/training ratio 1.44 (0.01035 / 0.007193; v14 1.43). With no final selection made,
  Kaggle's automatic pick is now the user's tank probe and v15; the selection is the user's.
- 31 Oct, written before the submission (04:22 by `date`): **v16** = zonal_v16dev_ch.py copied unchanged to
  `frozen/zonal_v16f.py`, with V15_PARAMS plus `cool_hold` 2 and `margin_heat` 0.30 (`submission/V16_PARAMS.json`,
  notebook `submission/zonal_v16_submission.ipynb`, built by `sb/make_v16_submission.sh` after round 7 passed).
  Evidence before sending: screen (docs/CHATTER.md) training 30 at full length -0.40 % (0.007164 against 0.007193),
  six cold full-size development windows -1.63 %, six hot ones identical, five cold scaled ones -8.16 %; round 7
  (blind, six new full-size buildings, cold ten-day windows; docs/RESULTS_ROUND7.md) -7.64 %, 6 of 6, comfort 0.51
  times v15's, two buildings -10.6 % and -21.4 %. Expected public (opinion): v15's 0.01035 times (1 - x), x about
  0.3-5 %: hot windows do not change, cold ones changed by -0.2 to -21 % in round 7, and we do not know how many hidden
  buildings hold zones like those of New York and Chicago. Reading: a public change below -0.3 % confirms that v16
  carries over to the public windows; from -0.3 % to +0.3 % means they hold little of what changed; above +0.3 %
  would mean harm we did not see, and v15 stays the recommended final selection. Not a reason to tune anything.
  Submitted 31 Oct 14:52 by `date` (notebook smartblabla version 15, "v16 = v15 + cool_hold 2 + margin_heat 0.30",
  imported unchanged from `submission/zonal_v16_submission.ipynb`; its committed run took 13 min 41 s). Score (read 1 Nov 16:07 by `date`; scoring took about 7 hours): **0.01031**,
  against v15's 0.01035: -0.39 %. By the rule above (below -0.3 %), v16 carries over to the public windows; the
  change sits at the low end of the expected 0.3-5 %, so the public windows hold few zones like those of round 7's
  New York and Chicago. Recommended final selection (the author's choice on Kaggle): v16 and v15, not the tank probe. (Superseded: since
  8 Nov 2026 13:55 the selections are v16 and a tuned version: c6fhm30 until 15:37, c6fhm40 since; docs/TUNED_CHECK.md.)
