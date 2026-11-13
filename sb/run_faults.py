"""Sensor-fault test of v16 (docs/SENSOR_FAULTS.md) on the twelve full-size buildings of rounds 6 and 7, ten days each,
against v16's and pid_water's clean runs. The check job (no fault, 288 steps) must match v16 exactly. Restartable.

    python -m sb.run_faults >> D:/SmartBuildings_data/faults.log 2>&1
    python -m sb.run_faults --read
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
POL = f"{REPO.as_posix()}/policies/zonal_v16_faults.py:FaultPolicy"
DATA = Path("D:/SmartBuildings_data")
R = DATA / "results"
OUT = R / "faults"
STEPS = 2880
ARMS = {"noise02": ("noise", 0.2), "noise05": ("noise", 0.5), "bias05": ("bias", 0.5), "lag1": ("lag", 1),
        "stuck10": ("stuck", 0.10)}
# (set, scenario root, v16's clean runs, pid_water's clean runs)
SETS = [("r6", DATA / "round6h/scenarios", R / "round6h/v16", R / "round6h/pid_water"),
        ("r7", DATA / "round7/scenarios", R / "round7/chm", R / "round7/pid_water")]


def scen(root: Path) -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in root.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    r7 = SETS[1][1]
    out = [memsched.job({"policy": POL, "base": "none", "kwargs": dict(V16, fault="none", level=0.0),
                         "out": str(OUT / "check"), "scenario": scen(r7)[0], "root": str(r7)}, 288)]
    for arm, (f, lv) in ARMS.items():
        for name, root, _, _ in SETS:
            for s in scen(root):
                out.append(memsched.job({"policy": POL, "base": "none", "kwargs": dict(V16, fault=f, level=lv),
                                         "out": str(OUT / f"{name}_{arm}"), "scenario": s, "root": str(root)}, STEPS))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def load(f: Path) -> np.ndarray:
    return np.load(f).astype(float)[:STEPS]


def read() -> None:
    root, ref = SETS[1][1], SETS[1][2]
    c = OUT / "check" / f"{scen(root)[0]}.npy"
    if c.exists():
        x, y = np.load(c).astype(float), np.load(ref / c.name).astype(float)[:288]
        print("check (no fault, 288 steps, against v16):", "IDENTICAL" if np.array_equal(x, y) else "DIFFERENT")
    for arm in ARMS:
        a, b, p, ca = [], [], [], []
        for name, root, ref, pid in SETS:
            for s in scen(root):
                f = OUT / f"{name}_{arm}" / f"{s}.npy"
                if f.exists():
                    x = load(f)
                    a.append(-x[:, 0].mean()), ca.append(-0.6 * x[:, 1].mean())
                    b.append(-load(ref / f"{s}.npy")[:, 0].mean()), p.append(-load(pid / f"{s}.npy")[:, 0].mean())
        if a:
            a, b, p = map(np.array, (a, b, p))
            print(f"{arm:8s} n {len(a):2d}  loss / clean v16 {a.mean() / b.mean():.3f} (worst {(a / b).max():.2f})  "
                  f"comfort {np.mean(ca):.5f}  below clean pid_water in {int((a < p).sum())}, ratio {a.mean() / p.mean():.3f}")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"faults starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("faults END")
    read()


if __name__ == "__main__":
    main()
