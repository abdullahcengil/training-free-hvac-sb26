"""Exploration, no decision (docs/RESULTS_ROUND7.md): does a delay-aware heating net (safety_pred 1, an existing option:
the heating net fires only if the zone is still far below its band after the heat in the pipe) remove the heating-only
cycle that v16 leaves in small rooms during the morning recovery? Arm `sp1` = V16_PARAMS + safety_pred 1, against v16's
existing runs: the two round-7 buildings with small rooms (no longer blind), the scaled Duluth twin (163 small rooms),
the six cold full-size development windows (slow recoveries, the risk) and two training windows at full length
(building_train_8 atlanta_1 with one small room; building_train_1 fairbanks_1, deep cold). Runs after the round-7
ablation (three simulations at most).

    python -m sb.run_explore_sp1 >> D:/SmartBuildings_data/explore_sp1.log 2>&1
    python -m sb.run_explore_sp1 --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
V16 = json.loads((REPO / "submission/V16_PARAMS.json").read_text())
POLICY = "D:/SmartBuildings_data/frozen/zonal_v16f.py:TransferPolicy"
KW = dict(V16, safety_pred=1)
DATA = Path("D:/SmartBuildings_data")
R = DATA / "results"
OUT = R / "explore_sp1"
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
# (set, scenario root, scenarios, steps, v16 reference folder)
SETS = [
    ("r7", DATA / "round7/scenarios", ["building_7804__chicago_dec03", "building_7803__newyork_jan29"], 2880,
     R / "round7/chm"),
    ("scaled", DATA / "bigdev_scaled/scenarios", ["building_7003__duluth_jan15"], 2880, R / "chatter/s_chm"),
    ("fullcold", DATA / "bigdev/scenarios", [f"building_{b}__{w}_jan15" for b, w in
                                             (("7001", "chicago"), ("7002", "helena"), ("7003", "duluth"),
                                              ("7005", "chicago"), ("7007", "newyork"), ("7008", "seattle"))],
     2880, R / "chatter/f_chm"),
    ("train", TRAIN, ["building_train_8__atlanta_1", "building_train_1__fairbanks_1"], 8640, R / "chatter/t_chm"),
]


def jobs() -> list[dict]:
    return [memsched.job({"policy": POLICY, "base": "none", "kwargs": KW, "out": str(OUT / name), "scenario": s,
                          "root": str(root)}, steps)
            for name, root, scen, steps, _ in SETS for s in scen]


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def terms(f: Path, n: int) -> tuple[float, float]:
    a = np.load(f).astype(float)[:n]
    return -a[:, 0].mean(), -0.6 * a[:, 1].mean()


def read() -> None:
    for name, _, scen, steps, ref in SETS:
        for s in scen:
            f = OUT / name / f"{s}.npy"
            if not f.exists():
                print(f"{name:8s} {s}: not finished")
                continue
            (l0, c0), (l1, c1) = terms(ref / f"{s}.npy", steps), terms(f, steps)
            print(f"{name:8s} {s:36s} v16 {l0:.5f} sp1 {l1:.5f} ({100 * (l1 / l0 - 1):+.2f} %)  comfort {c0:.5f} -> {c1:.5f}")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"explore sp1 starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("explore sp1 END")
    read()


if __name__ == "__main__":
    main()
