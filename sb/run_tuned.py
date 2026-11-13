"""Safety check of a leaderboard-tuned candidate before it becomes the second Kaggle final selection
(docs/TUNED_CHECK.md). Same frozen v16 file, only parameters change. Restartable (sb.memsched).

    python -m sb.run_tuned c4 >> D:/SmartBuildings_data/tuned.log 2>&1                 # shipped simulator sets
    PYTHONPATH=D:/SmartBuildings_data/kit_fixed python -m sb.run_tuned c4 --fixed >> ... # corrected copy
    python -m sb.run_tuned c4 --read
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
V16 = json.loads((REPO / "submission/V16_PARAMS.json").read_text())
POL = "D:/SmartBuildings_data/frozen/zonal_v16f.py:TransferPolicy"
DATA = Path("D:/SmartBuildings_data")
R = DATA / "results"
OUT = R / "tuned"
STEPS = 2880
# leaderboard-probe candidates (docs/LEADERBOARD_PROBE.md); overrides of V16_PARAMS
CANDS = {
    "c4": dict(glide_safety=0.80, glide_floor=-20.0, margin_heat=0.20, f_heat_rec=0.45),
    "c6": dict(glide_safety=0.95, glide_floor=-26.0, margin_heat=0.20, f_heat_rec=0.45),
    "c6gs120": dict(glide_safety=1.20, glide_floor=-26.0, margin_heat=0.20, f_heat_rec=0.45),
    "c6gf34": dict(glide_safety=0.95, glide_floor=-34.0, margin_heat=0.20, f_heat_rec=0.45),
    "c6mh10": dict(glide_safety=0.95, glide_floor=-26.0, margin_heat=0.10, f_heat_rec=0.45),
    "c6fr60": dict(glide_safety=0.95, glide_floor=-26.0, margin_heat=0.20, f_heat_rec=0.60),
    "c8": dict(glide_safety=1.20, glide_floor=-26.0, margin_heat=0.20, f_heat_rec=0.45, f_heat_max=0.30),
    "c4fhm30": dict(glide_safety=0.80, glide_floor=-20.0, margin_heat=0.20, f_heat_rec=0.45, f_heat_max=0.30),
    "v16fhm30": dict(f_heat_max=0.30),
    # 8 Nov (docs/TUNED_CHECK.md, docs/LEADERBOARD_PROBE.md)
    "c6fhm30": dict(glide_safety=0.95, glide_floor=-26.0, margin_heat=0.20, f_heat_rec=0.45, f_heat_max=0.30),
    "c6fhm40": dict(glide_safety=0.95, glide_floor=-26.0, margin_heat=0.20, f_heat_rec=0.45, f_heat_max=0.40),
    "c4fhm40": dict(glide_safety=0.80, glide_floor=-20.0, margin_heat=0.20, f_heat_rec=0.45, f_heat_max=0.40),
    "c5fhm40": dict(glide_safety=0.95, glide_floor=-20.0, margin_heat=0.20, f_heat_rec=0.45, f_heat_max=0.40),
    "c6fhm40s40": dict(glide_safety=0.95, glide_floor=-26.0, margin_heat=0.20, f_heat_rec=0.45, f_heat_max=0.40,
                       f_heat_safety=0.40),
    # docs/ADAPT_START.md: c8 + each zone learns its setback level (policies/zonal_v17ad.py)
    "c8ad": dict(glide_safety=1.20, glide_floor=-26.0, margin_heat=0.20, f_heat_rec=0.45, f_heat_max=0.30, glide_adapt=1),
}
# candidates that need a policy file other than the frozen v16 one
POLS = {"c8ad": f"{REPO.as_posix()}/policies/zonal_v17ad.py:TransferPolicy"}
BIG = DATA / "bigdev/scenarios"
COLD = ["building_7001__chicago_jan15", "building_7002__helena_jan15", "building_7003__duluth_jan15",
        "building_7005__chicago_jan15", "building_7007__newyork_jan15", "building_7008__seattle_jan15"]
HOT = ["building_7001__dubai_jul15", "building_7002__lasvegas_jul15", "building_7003__houston_jul15",
       "building_7005__lasvegas_jul15", "building_7007__miami_jul15", "building_7008__chicago_jul15"]


def scen(root: Path) -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in root.glob("*/*/config.gin"))


def sets(fixed: bool) -> list[tuple[str, Path, list[str], dict[str, Path]]]:
    """(set name, scenario root, scenarios, v16 reference run folder for each scenario)."""
    if fixed:
        return [("fixed", BIG, COLD + HOT, {s: R / "fixsim/v16" for s in COLD + HOT})]
    out = [("dev", BIG, COLD + HOT, {**{s: R / "chatter/f_chm" for s in COLD}, **{s: R / "chatter/h_chm" for s in HOT}})]
    for name, root, ref in (("r6", DATA / "round6h/scenarios", R / "round6h/v16"),
                            ("r7", DATA / "round7/scenarios", R / "round7/chm"),
                            ("r8", DATA / "round8/scenarios", R / "round8/v16")):
        ss = scen(root)
        out.append((name, root, ss, {s: ref for s in ss}))
    return out


def jobs(cand: str, fixed: bool) -> list[dict]:
    kw = {**V16, **CANDS[cand]}
    return [memsched.job({"policy": POLS.get(cand, POL), "base": "none", "kwargs": kw, "out": str(OUT / cand / name),
                          "scenario": s, "root": str(root)}, STEPS)
            for name, root, ss, _ in sets(fixed) for s in ss]


def load(f: Path) -> np.ndarray:
    return np.load(f).astype(float)[:STEPS]


def read(cand: str) -> None:
    for name, _, ss, ref in sets(False) + sets(True):
        a, b, ca, cb = [], [], [], []
        for s in ss:
            f, g = OUT / cand / name / f"{s}.npy", ref[s] / f"{s}.npy"
            if f.exists() and g.exists():
                x, y = load(f), load(g)
                a.append(-x[:, 0].mean()), b.append(-y[:, 0].mean())
                ca.append(-0.6 * x[:, 1].mean()), cb.append(-0.6 * y[:, 1].mean())
        if a:
            a, b = np.array(a), np.array(b)
            print(f"{cand} {name:5s} n {len(a):2d}/{len(ss):2d}  loss / v16 {a.mean() / b.mean():.4f}  "
                  f"worst {(a / b).max():.3f}  better in {int((a < b).sum())}  comfort {np.mean(ca):.5f} vs {np.mean(cb):.5f}")


def main() -> None:
    cand = sys.argv[1]
    assert cand in CANDS, f"unknown candidate {cand}"
    if "--read" in sys.argv:
        read(cand)
        return
    fixed = "--fixed" in sys.argv
    assert fixed == ("kit_fixed" in os.environ.get("PYTHONPATH", "")), "--fixed needs the patched copy and only it"
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    plan = lambda: ([j for j in jobs(cand, fixed) if not Path(j["result"]).exists()], [])
    say(f"tuned {cand}{' fixed' if fixed else ''} starts: {len(plan()[0])} of {len(jobs(cand, fixed))} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say(f"tuned {cand}{' fixed' if fixed else ''} END")
    read(cand)


if __name__ == "__main__":
    main()
