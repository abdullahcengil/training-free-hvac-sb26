"""Exploration, no decision (docs/TRANSFER_ABLATION.md, "What next"): does faster initial learning help? The transfer
ablation showed that learning carries the transfer and that twofold wrong priors cost 11 % on the first day; in
full-size buildings the learned gains differ from the prior by building (medians 0.14-0.30 against 0.27) and by zone.
Arm `pv10` = V16_PARAMS with the RLS prior variances (m2_pvar) ten times larger, so the five numbers move faster in the
first hours (the covariance cap is not reached: initial trace 0.22 against 1.0). Against v16's existing runs: the six
cold and six hot full-size development windows (first 2880 steps) and four training scenarios at full length. Runs
after the delay-aware heating-net exploration (three simulations at most). Only if it shows a gain above 1 % without
large losses does a candidate follow, with its screen and pass marks written before any run.

    python -m sb.run_explore_learn >> D:/SmartBuildings_data/explore_learn.log 2>&1
    python -m sb.run_explore_learn --read
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
PVAR = (1e-3, 1e-3, 1e-2, 1e-5, 1e-2)   # m2_pvar of frozen/zonal_v16f.py
KW = dict(V16, m2_pvar=[10 * x for x in PVAR])
DATA = Path("D:/SmartBuildings_data")
R = DATA / "results"
OUT = R / "explore_learn"
BIG = DATA / "bigdev/scenarios"
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
COLD = ["building_7001__chicago_jan15", "building_7002__helena_jan15", "building_7003__duluth_jan15",
        "building_7005__chicago_jan15", "building_7007__newyork_jan15", "building_7008__seattle_jan15"]
HOT = ["building_7001__dubai_jul15", "building_7002__lasvegas_jul15", "building_7003__houston_jul15",
       "building_7005__lasvegas_jul15", "building_7007__miami_jul15", "building_7008__chicago_jul15"]
TRN = ["building_train_1__fairbanks_1", "building_train_8__atlanta_1", "building_train_4__denver_2",
       "building_train_5__singapore_4"]
# (set, scenario root, scenarios, steps, v16 reference folder)
SETS = [("cold", BIG, COLD, 2880, R / "chatter/f_chm"), ("hot", BIG, HOT, 2880, R / "chatter/h_chm"),
        ("train", TRAIN, TRN, 8640, R / "chatter/t_chm")]


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
        l0s, l1s = [], []
        for s in scen:
            f = OUT / name / f"{s}.npy"
            if not f.exists():
                print(f"{name:6s} {s}: not finished")
                continue
            (l0, c0), (l1, c1) = terms(ref / f"{s}.npy", steps), terms(f, steps)
            l0s.append(l0), l1s.append(l1)
            print(f"{name:6s} {s:36s} v16 {l0:.5f} pv10 {l1:.5f} ({100 * (l1 / l0 - 1):+.2f} %)  comfort {c0:.5f} -> {c1:.5f}")
        if l0s:
            print(f"== {name}: {len(l0s)} of {len(scen)}, mean v16 {np.mean(l0s):.6f} pv10 {np.mean(l1s):.6f} "
                  f"({100 * (np.mean(l1s) / np.mean(l0s) - 1):+.2f} %), better in {sum(b < a for a, b in zip(l0s, l1s))}")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"explore learn starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("explore learn END")
    read()


if __name__ == "__main__":
    main()
