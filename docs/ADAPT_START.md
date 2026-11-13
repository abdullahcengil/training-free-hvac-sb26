# Each zone learns how deep it may set back (written 7 Nov 2026, 14:58 by `date`; before any run)

## Why (measured on runs already made; `docs/TUNED_CHECK.md`)

On the 30 full-size windows of the tuned check (dev, rounds 6-8), v16's loss falls mostly in the morning: 03:00-07:59
(first arrivals at 06:00) carry about 41 % of it, 35 % of the cold windows' loss falls before 06:00. A deeper night
setback (the tuned c8: glide_safety 1.20, glide_floor -26, margin_heat 0.20, f_heat_rec 0.45, f_heat_max 0.30) cuts
energy and carbon by 5-8 % in every cold window, but fails the comfort mark (1.70x v16 over 42 windows). Its extra
comfort regret falls in 06:00-10:00 of the coldest mornings (for example day 9 of Chicago 15 Jan: v16 65.7, c8 141.4 per
step x 1e4), and the same zones keep failing on later cold mornings. So one setting for all zones and all nights is
wrong both ways: deep is right on most nights, shallow on the few hard ones, and which zones are hard differs.

## What (`sb/make_v17ad.py` builds `policies/zonal_v17ad.py` = the frozen v16 file plus one option)

`glide_adapt` 1: each zone has a setback level a in [0, 1]. Level 1 uses the glide settings given (`glide_safety`,
`glide_floor`; here c8's 1.20 and -26), level 0 uses `ga_gs0`, `ga_gf0` (v16's 0.6606 and -16); between, linear. Every
morning the zone's comfort deficit over the first `ga_h` hours of comfort time (mean K below the comfort band's lower
edge) is measured; above `ga_tol` the level drops by `ga_down`, otherwise it rises by `ga_up` (clipped to [0, 1]).
Settings fixed now: ga_h 3, ga_tol 0.02 K, ga_down 0.5, ga_up 0.25, start level ga_init 0.5. Nothing else changes.
With `glide_adapt` 0 every new line is skipped.

Known-answer checks (required before reading anything else; 288 steps of the first round-7 building):
- K1: glide_adapt 0 with v16's parameters gives v16's actions exactly.
- K2: glide_adapt 1 with ga_init 1, ga_down 0, ga_up 0 and c8's parameters gives c8's actions exactly.

## Runs

Candidate `c8ad` = c8's parameters + glide_adapt 1, on the same 42 windows as the tuned check (30 on the shipped
simulator, 12 on the corrected copy), against the v16 and c8 runs already made.

## Reading rule (fixed now)

- A1: c8ad's mean loss over all 42 windows at or below c8's, and below c8 in more than half of the windows where the
  two differ.
- A2: comfort over all 42 windows at most 1.5x v16's (the tuned check's G4, which c8 failed at 1.70x).
- A3: the tuned check's G1-G3 against v16 (dev at most 1.01x; r6-r8 at most 1.01x with no window above 1.10x; corrected
  simulator at most 1.01x).
If A1-A3 all pass, c8ad (i) goes to the public leaderboard as a probe and, if its score is at or below c4fhm30's
0.01015, replaces c4fhm30 as the recommended tuned selection; (ii) becomes the candidate for a v17, which needs its own
pre-registered blind round on new buildings before the paper may report it. If any mark fails, it is reported as a
failure and nothing changes. v16 and the paper's claims about v16 do not change either way.

## Known-answer checks (read 7 Nov 2026, 15:02 by the run log)

- K1 (glide_adapt 0, v16 parameters): IDENTICAL to v16, 288 steps.
- K2 (level fixed at 1, c8 parameters): IDENTICAL to c8, 288 steps.

The 42 candidate runs started 15:02.

## Result (read 7 Nov 2026, 18:21 by `date`)

| set | n | loss / v16 | worst | better in | comfort c8ad vs v16 |
|---|---|---|---|---|---|
| dev | 12 | 0.9891 | 1.000 | 6 | 0.00022 vs 0.00019 |
| r6 | 6 | 0.9899 | 1.000 | 3 | 0.00017 vs 0.00013 |
| r7 | 6 | 0.9824 | 0.991 | 6 | 0.00097 vs 0.00083 |
| r8 | 6 | 0.9684 | 0.974 | 6 | 0.00022 vs 0.00020 |
| fixed | 12 | 0.9887 | 1.000 | 6 | 0.00022 vs 0.00019 |

- A1: mean loss over 42 windows 0.013610 (c8ad) vs 0.013562 (c8), 1.0035x; better than c8 in 6 of the 27 windows
  where they differ. **FAIL** (both parts).
- A2: comfort over 42 windows 1.16x v16 (c8 1.70x). PASS.
- A3: G1 0.989, G2 r6-r8 worst 1.000, G3 0.989. PASS.

**c8ad fails.** By the rule above it is not submitted, c4fhm30 stays the recommended tuned selection, and there is no
v17. What it shows: the learned level does what it was built for (comfort regret 1.70x -> 1.16x of v16) but gives
back about a fifth of c8's gain over v16 (0.986x vs 0.982x), because a missed morning costs less in the score than the
energy and carbon a shallower night costs. Comfort-driven adaptation moves the wrong way for the score; any further
per-zone adaptation has to be driven by the zone's own loss, not by its comfort alone. (Descriptive only, not a
reason to submit: c8ad would pass the tuned check G1-G4 and sits within 0.3 % of c4fhm30 in every set.)
