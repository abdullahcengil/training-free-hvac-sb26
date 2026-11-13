"""Does setting the measured delay fix v16's extra-lag weakness? (docs/LAG_SETTING.md). Restartable (sb.memsched).

    python -m sb.run_lagset >> D:/SmartBuildings_data/lagset.log 2>&1
    python -m sb.run_lagset --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched
from sb.run_faults import OUT as FAULTS, SETS, load, scen

REPO = Path(__file__).resolve().parents[1]
V16 = json.loads((REPO / "submission/V16_PARAMS.json").read_text())
POL = f"{REPO.as_posix()}/policies/zonal_v16lag_faults.py:FaultPolicy"
R = Path("D:/SmartBuildings_data/results")
OUT = R / "lagset"
STEPS = 2880
# arm: (fault, level, extra_lag)
ARMS = {"lagcomp": ("lag", 1, 1),    # one extra step of reading delay, and the controller told so
        "overset": ("none", 0.0, 1)}  # no extra delay, but the controller told there is one (a wrong setting)


def jobs() -> list[dict]:
    r7 = SETS[1][1]
    out = [memsched.job({"policy": POL, "base": "none", "kwargs": dict(V16, fault="none", level=0.0, extra_lag=0),
                         "out": str(OUT / "check"), "scenario": scen(r7)[0], "root": str(r7)}, 288)]
    for arm, (f, lv, d) in ARMS.items():
        for name, root, _, _ in SETS:
            for s in scen(root):
                out.append(memsched.job({"policy": POL, "base": "none",
                                         "kwargs": dict(V16, fault=f, level=lv, extra_lag=d),
                                         "out": str(OUT / f"{name}_{arm}"), "scenario": s, "root": str(root)}, STEPS))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def read() -> None:
    root, ref = SETS[1][1], SETS[1][2]
    c = OUT / "check" / f"{scen(root)[0]}.npy"
    if c.exists():
        x, y = np.load(c).astype(float), np.load(ref / c.name).astype(float)[:288]
        print("check (extra_lag 0, no fault, 288 steps, against v16):", "IDENTICAL" if np.array_equal(x, y) else "DIFFERENT")
    rows = [("lag1 (v16, from the fault test)", FAULTS, "lag1")] + [(a, OUT, a) for a in ARMS]
    for label, base, arm in rows:
        a, b, p, ca = [], [], [], []
        for name, root, ref, pid in SETS:
            for s in scen(root):
                f = base / f"{name}_{arm}" / f"{s}.npy"
                if f.exists():
                    x = load(f)
                    a.append(-x[:, 0].mean()), ca.append(-0.6 * x[:, 1].mean())
                    b.append(-load(ref / f"{s}.npy")[:, 0].mean()), p.append(-load(pid / f"{s}.npy")[:, 0].mean())
        if a:
            a, b, p = map(np.array, (a, b, p))
            print(f"{label:32s} n {len(a):2d}  loss / clean v16 {a.mean() / b.mean():.3f} (worst {(a / b).max():.2f})  "
                  f"comfort {np.mean(ca):.5f}  below clean pid_water in {int((a < p).sum())}")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"lagset starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("lagset END")
    read()


if __name__ == "__main__":
    main()
