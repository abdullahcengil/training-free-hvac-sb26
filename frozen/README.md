# Frozen controller code of each pre-registered round

Every round tested code that was fixed before its scenarios were generated or run. Rounds 1-5 name a git commit of
this repository; round 6 and the Kaggle submissions of v14 and v15 name a file by its SHA-256, kept here byte for byte
(`-text` in `.gitattributes`, so git does not change its line endings).

| round | version | code | SHA-256 (first 16 hex digits) |
|---|---|---|---|
| 1 | v7 | `git show ad59466:policies/zonal.py` | ed09634eb1f0486a |
| 2 | v8 | `git show e8dbcd3:policies/zonal.py` | f612994c6adc3eeb |
| 3 | v9 | `git show b7e5ec9:policies/zonal.py` | a54725705237603d |
| 4 | v10 | `git show 24f07c3:policies/zonal.py` | 56090bd0d7877de6 |
| 5 | v11 (also v12, v13 with other parameters) | `git show aa71ade:policies/zonal.py` | 3b6c1135c9ff4028 |
| 6 | v14, v15 | `frozen/zonal_v14f.py` | 0a31d331ee3dd867 |

The full hash of `zonal_v14f.py`, as stamped in `docs/preregistration6h/PREREGISTRATION_6_2026-10-30.md`, is
0a31d331ee3dd867b73577f1f8c0d4624725db847aa9ed80b3a416c186232b13. Check with `sha256sum frozen/zonal_v14f.py`, and
for rounds 1-5 with `git show <commit>:policies/zonal.py | sha256sum`.

Reproduction check (30 Oct 2026, read 16:05 by `date`): `zonal_v14f.py` from this folder with
`submission/V15_PARAMS.json`, run on building_train_1 / atlanta_2 for the full 8640 steps, gave every reward term
identical to the recorded v15 run (`results/holiday/ed1_full`, made from a copy with the same hash) at every step;
mean reward -0.0031278791107019464 both times (`python -m sb.repro_check`, 904 s).

Each version is one of these files plus a parameter file (`docs/preregistration*/V*_PARAMS.json`,
`submission/V*_PARAMS.json`). The Kaggle notebooks in `submission/` hold the same code after a short Kaggle header,
without its `from __future__ import annotations` line (`sb/make_notebook.py`).
