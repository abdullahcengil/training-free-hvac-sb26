# Round 6 (blind, full size, empty holidays): results (runs 30 Oct 2026 02:25-03:14; read 03:14 by `date`)

Plan: docs/PREREGISTRATION_6.md (fixed 02:18, frozen copy `docs/preregistration6h/PREREGISTRATION_6_2026-10-30.md`
with its OpenTimestamps proof), scenarios generated after it (02:19-02:20; manifest
`docs/preregistration6h/MANIFEST6_2026-10-30.txt`; no building rejected). Runs `results/round6h/{v14,ed1}`, first 2880
steps; `python -m sb.run_round6h --read`.

| scenario | holiday | v14 | ed1 | change | comfort v14 -> ed1 |
|---|---|---|---|---|---|
| building_7701 houston_may28 | Memorial Day (Mon) | 0.00688 | 0.00650 | -5.52 % | 0.00001 -> 0.00005 |
| building_7702 miami_jul02 | Independence Day (Tue) | 0.01208 | 0.01170 | -3.15 % | 0.00008 -> 0.00008 |
| building_7703 dubai_sep03 | Labor Day (Mon) | 0.02861 | 0.02832 | -1.03 % | 0.00004 -> 0.00003 |
| building_7704 newyork_oct08 | Columbus Day (Mon) | 0.00318 | 0.00312 | -1.75 % | 0.00002 -> 0.00004 |
| building_7705 chicago_nov19 | Thanksgiving (Thu) | 0.01415 | 0.01360 | -3.92 % | 0.00011 -> 0.00015 |
| building_7706 duluth_dec17 | Christmas (Mon) | 0.01060 | 0.01025 | -3.34 % | 0.00013 -> 0.00013 |

Loss and comfort are mean per step over the ten days.

- **H1 PASS**: mean 0.012247 against 0.012583, -2.67 % (mark: at least 0.5 % lower).
- **H2 PASS**: better in 6 of 6 (mark 5).
- **H3: counted as FAILED.** Comfort regret summed over the six 0.00048 against 0.00039, 1.22 times v14's. The plan's
  text sets the mark at 1.5 times (pass); the runner it names (`sb/run_round6h.py`, hash in the plan) checks 1.10
  times, a constant left from the draft (fail). We count the stricter reading (DEVIATIONS.md, deviation 6). In
  absolute terms the rise is 0.000086 per step summed over the six, 4.2 % of the loss saved (0.002019).
- **H4 PASS**: the two arms' per-step rewards are identical until 07:00 on every holiday.

Decision (plan): H1, H2 and H4 pass, so ed1 becomes v15 once the full-length development check of docs/HOLIDAY.md
passes (all 70 windows, running since 03:14). H3 is reported with it.
