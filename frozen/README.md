# Frozen controller code of each pre-registered round

Every round tested code that was fixed before its scenarios were generated or run. Every round's code is kept here byte for byte and named by its SHA-256 (rounds 1-5 were frozen as commits of the private
working repository; the files below are those commits' `policies/zonal.py`, unchanged)
(`-text` in `.gitattributes`, so git does not change its line endings).

| round | version | code | SHA-256 (first 16 hex digits) |
|---|---|---|---|
| 1 | v7 | `frozen/zonal_v7_round.py` (commit ad59466) | ed09634eb1f0486a |
| 2 | v8 | `frozen/zonal_v8_round.py` (commit e8dbcd3) | f612994c6adc3eeb |
| 3 | v9 | `frozen/zonal_v9_round.py` (commit b7e5ec9) | a54725705237603d |
| 4 | v10 | `frozen/zonal_v10_round.py` (commit 24f07c3) | 56090bd0d7877de6 |
| 5 | v11 (also v12, v13 with other parameters) | `frozen/zonal_v11_round.py` (commit aa71ade) | 3b6c1135c9ff4028 |
| 6 | v14, v15 | `frozen/zonal_v14f.py` | 0a31d331ee3dd867 |
| 7, 8 | v16 (round 8: v16 with one option on) | `frozen/zonal_v16f.py` | af9c0d2bff35568b |

The full hash of `zonal_v14f.py`, as stamped in `docs/preregistration6h/PREREGISTRATION_6_2026-10-30.md`, is
0a31d331ee3dd867b73577f1f8c0d4624725db847aa9ed80b3a416c186232b13. Check any of them with `sha256sum frozen/<file>`.

Reproduction check (30 Oct 2026, read 16:05 by `date`): `zonal_v14f.py` from this folder with
`submission/V15_PARAMS.json`, run on building_train_1 / atlanta_2 for the full 8640 steps, gave every reward term
identical to the recorded v15 run (`results/holiday/ed1_full`, made from a copy with the same hash) at every step;
mean reward -0.0031278791107019464 both times (`python -m sb.repro_check`, 904 s).

Each version is one of these files plus a parameter file (`docs/preregistration*/V*_PARAMS.json`,
`submission/V*_PARAMS.json`). The Kaggle notebooks in `submission/` hold the same code after a short Kaggle header,
without its `from __future__ import annotations` line (`sb/make_notebook.py`).
