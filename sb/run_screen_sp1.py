"""Heating-net screen (docs/HEATNET.md; candidate and pass marks written there before any screen run): sp1 = v16 +
safety_pred 1 (the heating safety net, like the cooling one, fires only if the zone is still far below its band after
the heat already in the pipe). Four sets against v16's existing runs: S, the five cold windows of the scaled twins;
F, the six cold full-size development windows; H, the six hot full-size development windows (first 2880 steps); T, the
30 shipped training scenarios at full length. Runs that the exploration (sb/run_explore_sp1.py) already made with the
same policy file and settings are reused, not repeated (runs are deterministic). Restartable (sb.memsched).

    python -m sb.run_screen_sp1 >> D:/SmartBuildings_data/screen_sp1.log 2>&1
    python -m sb.run_screen_sp1 --read
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
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
BIG = DATA / "bigdev/scenarios"
SCALED = DATA / "bigdev_scaled/scenarios"
OUT = R / "heatnet"
EXP = R / "explore_sp1"
COLD = ["building_7001__chicago_jan15", "building_7002__helena_jan15", "building_7003__duluth_jan15",
        "building_7005__chicago_jan15", "building_7007__newyork_jan15", "building_7008__seattle_jan15"]
HOT = ["building_7001__dubai_jul15", "building_7002__lasvegas_jul15", "building_7003__houston_jul15",
       "building_7005__lasvegas_jul15", "building_7007__miami_jul15", "building_7008__chicago_jul15"]
SCOLD = ["building_7001__chicago_jan15", "building_7002__helena_jan15", "building_7003__duluth_jan15",
         "building_7007__newyork_jan15", "building_7008__seattle_jan15"]


def training() -> list[str]:
    return sorted(f"{d.parent.name}__{d.name}" for d in TRAIN.glob("building_train_*/*") if (d / "config.gin").exists())


# (set, scenario root, scenarios, steps, v16 reference folder, exploration folder with the same runs or None)
SETS = [("S", SCALED, SCOLD, 2880, R / "chatter/s_chm", EXP / "scaled"),
        ("F", BIG, COLD, 2880, R / "chatter/f_chm", EXP / "fullcold"),
        ("H", BIG, HOT, 2880, R / "chatter/h_chm", None),
        ("T", TRAIN, None, 8640, R / "chatter/t_chm", EXP / "train")]


def scen(entry) -> list[str]:
    return entry[2] if entry[2] is not None else training()


def result(name: str, s: str) -> Path | None:
    """The candidate's run of scenario s in set name: the screen's own, else the exploration's."""
    for f in (OUT / name / f"{s}.npy",) + (() if dict((n, e) for n, *_, e in SETS)[name] is None
                                         else (dict((n, e) for n, *_, e in SETS)[name] / f"{s}.npy",)):
        if f.exists():
            return f
    return None


def jobs() -> list[dict]:
    return [memsched.job({"policy": POLICY, "base": "none", "kwargs": KW, "out": str(OUT / e[0]), "scenario": s,
                          "root": str(e[1])}, e[3]) for e in SETS for s in scen(e)]


def plan() -> tuple[list[dict], list[dict]]:
    todo = []
    for j in jobs():
        name = Path(j["out"]).name
        s = Path(j["result"]).stem
        if result(name, s) is None:
            todo.append(j)
    return todo, []


def read() -> None:
    for e in SETS:
        name, _, _, steps, ref, _ = e
        a, b, worst, better, n = [], [], -1e9, 0, 0
        for s in scen(e):
            f = result(name, s)
            if f is None:
                continue
            x0 = np.load(ref / f"{s}.npy").astype(float)[:steps]
            x1 = np.load(f).astype(float)[:steps]
            l0, l1 = -x0[:, 0].mean(), -x1[:, 0].mean()
            a.append(l0), b.append(l1)
            d = 100 * (l1 / l0 - 1)
            worst, better, n = max(worst, d), better + (l1 < l0), n + 1
            print(f"{name} {s:36s} v16 {l0:.6f} sp1 {l1:.6f} ({d:+.2f} %)  comfort {-0.6 * x0[:, 1].mean():.5f} -> "
                  f"{-0.6 * x1[:, 1].mean():.5f}")
        if n:
            print(f"== {name}: {n} of {len(scen(e))}, mean v16 {np.mean(a):.6f} sp1 {np.mean(b):.6f} "
                  f"({100 * (np.mean(b) / np.mean(a) - 1):+.2f} %), better in {better}, worst {worst:+.2f} %")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"screen sp1 starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("screen sp1 END")
    read()


if __name__ == "__main__":
    main()
