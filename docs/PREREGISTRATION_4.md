# Pre-registration, round 4: does the re-tuned controller (v10) transfer?

Frozen 22 Oct 2026, about 02:00 (UTC+2), before any policy was run on a round-4 scenario. A frozen copy and the manifest are timestamped with OpenTimestamps (only their SHA-256 hashes leave the machine).

Note (30 Oct 2026, 15:55 by `date`): the first Bitcoin block that commits to the frozen copy (972,546) has the time
22 Oct 01:07 (UTC+2), so the frozen copy existed by then and "about 02:00" above was a time written ahead of the
clock. The frozen copy is unchanged; see docs/TIMESTAMPS.md.

## Why a fourth round

v9 passed three of four hypotheses in round 3 and scores 0.01199 on the 30 training scenarios at full length. Its Kaggle public score is 0.01623 (21 Oct). 84 % of its training loss is energy and carbon. This round tests what came out of a systematic search on training scenarios after a failed cooling-side mechanism.

What was tried, all on training scenarios only (`docs/TUNING_LOG.md`, section v10):
1. Diagnosis: in warm climates the loss is chiller electricity. Fans sit at the 200 Pa floor. 24-43 % of the loss falls outside occupied hours.
2. A cooling-side twin of the v9 night glide (`cool_glide`): float up at night and at weekends, then pull down just in time. In 7-day screens it cut the warm-set loss by 17-18 %. In a CMA-ES search over 14 parameters on six other training scenarios (7 days) the combination improved by a further 5.8 %.
3. At full length (30 days) the cooling glide failed. Building 1 / Phoenix 5 got 99 % worse, and warm scenarios were worse in 4 of 4 even with an added capacity guard. The floor slab stores the heat of a float, and a building near its cooling limit pays it back with interest. The cooling glide was dropped. Its code stays in the file, default off.
4. The search's other parameters, without the cooling glide (v10), are better than v9 in all four warm scenarios at full length, comfort included.

v10 therefore changes no mechanism of v9. It changes nine parameters, chosen by the search:
- comfort margins: heating 0.40 K, cooling 0.43 K, was 0.5 / 0.5;
- aim inside the band when acting: 0.08 K, was 0.3;
- damping: 0.74, was 0.7;
- daytime heating airflow cap: 0.245, was 0.2;
- night recovery cap: 0.268, was 0.3;
- night glide floor: eco band − 7.46 K, about 8.5 °C, was 11 °C;
- glide safety: 0.66, was 0.7;
- highest supply-air candidate: 295.35 K, was 295.

The training check below is the evidence for the pass marks.

## Training check before freezing (30 training scenarios, full length)

v10 (`results/train_8640/v10c`) against v9 (`results/train_8640/v9f`):
- Overall: 0.01092 against 0.01199 (-8.9 %).
- Per scenario: better in **30 of 30**. Median change -11.8 %, range -26.6 % to -0.4 %.
- Warm stations (Atlanta, Phoenix, Singapore; 18 scenarios): -12.6 %, better in 18 of 18.
- Cold stations (Denver, Fairbanks; 12 scenarios): -5.5 %, better in 12 of 12. Fairbanks alone: -4.4 %.
- Comfort regret per step: 0.00294 against 0.00324 (-9 %), so the saving is not bought with comfort.

The search scenarios (six of the 30) are part of this check. The other 24 were never used by the search. The cooling-glide screens used ten of them for 7 days, with a different mechanism that v10 does not contain.

Bit-for-bit check: the v10 code with the v9 parameters on four training scenarios (2016 steps) gives per-step rewards identical to the round-3 frozen v9 file (`results/cool_2016/{v9_frozen,v9_codeD}`).

## Held-out set 4 (fixed now)

**Buildings.** Six new buildings from the official floor generator, seeds 7301-7306 (spares 7307-7315 in order if the generator's own check rejects a scaled building), scaled exactly as in rounds 1-3 (`sb/make_heldout.py --round 4`; hashes in `heldout4/MANIFEST.txt`). The generator rejected 7301 and 7307 (slot 1), 7302 (slot 2), 7303 (slot 3), and 7305, 7311 and 7312 (slot 5) for zones below 20 m². The six buildings are therefore **7308, 7309, 7310, 7304, 7313 and 7306**, with 4 to 18 air handlers each. They were built on 21 Oct 2026, before this file was frozen; no policy has been run on them.

**Weather.** No strip was used for development in any round. Two kinds:
- Strips that were used only as test strips in rounds 1-3: singapore_2, singapore_5, atlanta_4 (round 1), fairbanks_3, minneapolis_1, denver_1 (round 1), minneapolis_2 (round 2), and fairbanks_dec, denver_dec (round 3; 1 December 2023 06:00).
- New 30-day summer windows that lie between two shipped strips: phoenix_jun25 (25 June 2023 06:00; 9 days overlap phoenix_4 and 9 days phoenix_5, both training strips), phoenix_aug06 (6 August; 9 days overlap phoenix_5, 9 days phoenix_6) and atlanta_jul30 (30 July; overlaps atlanta_5 and atlanta_6 by 9 days each). The buildings are new, so no building-weather pair has been seen.

| building | warm strip | cold strip |
|---|---|---|
| 7308 | phoenix_jun25 | fairbanks_3 |
| 7309 | singapore_2 | minneapolis_1 |
| 7310 | atlanta_jul30 | denver_1 |
| 7304 | phoenix_aug06 | fairbanks_dec |
| 7313 | singapore_5 | minneapolis_2 |
| 7306 | atlanta_4 | denver_dec |

All episodes run the full 30 days with the runner `sb/run.py`.

## Policies

1. v10: `policies/zonal.py` at the commit recorded in `RUN_INFO.json` (exported to a file before the run), with parameters `docs/preregistration4/V10_PARAMS.json`; every other parameter at its default. With the v9 parameters the v10 code gives bit-for-bit the frozen v9 result (`docs/TUNING_LOG.md`).
2. v9: the round-3 frozen file (`b7e5ec9`), with its round-3 parameters.
3. pid_water, the best official baseline in rounds 1-3, as a reference (descriptive; no hypothesis).

## Hypotheses and pass marks

The development evidence is the training check above (-12.6 % warm, -5.5 % cold, -8.9 % overall, 30 of 30 better, comfort -9 %). The marks are set about half-way to that evidence, so they are clearly passable only if the re-tuning transfers to new buildings, a station never used for training (Minneapolis) and new weather windows.

- **R4-H1 (warm).** v10's score on the six warm scenarios is at least 6 % lower than v9's.
- **R4-H2 (warm, broadly).** v10 is better than v9 in at least 5 of the 6 warm scenarios.
- **R4-H3 (cold).** v10's score on the six cold scenarios is at least 2 % lower than v9's.
- **R4-H4 (all).** v10's score on all 12 scenarios is at least 5 % lower than v9's.
- **R4-H5 (comfort).** v10's total comfort regret over all 12 scenarios is at most v9's.

Each hypothesis is reported as passed or failed, whatever the outcome.

## Rules

- **Order.** Run once: v10, then v9, then pid_water (`sb/heldout4.sh`), with at most four simulations at a time.
- **Scoring.** `sb/evaluate_round4.py` writes the scores into `docs/RESULTS_ROUND4.md`, whatever the outcome.
- **Crashes.** Crashes are reported, fixed and labelled, as in rounds 1-3.
- **Kaggle.** The v10 notebook is built from the frozen file only after round 4 is scored. The public leaderboard is never used to choose parameters.
