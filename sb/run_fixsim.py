"""v16 and pid_water on the simulator with both proposed fixes (docs/FIXSIM.md), against their runs on the shipped
simulator: six cold and six hot full-size development windows, first 2880 steps. Restartable (sb.memsched).

    PYTHONPATH=D:/SmartBuildings_data/kit_fixed python -m sb.run_fixsim >> D:/SmartBuildings_data/fixsim.log 2>&1
    python -m sb.run_fixsim --read
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
ROOT = DATA / "bigdev/scenarios"
OUT = R / "fixsim"
STEPS = 2880
COLD = ["building_7001__chicago_jan15", "building_7002__helena_jan15", "building_7003__duluth_jan15",
        "building_7005__chicago_jan15", "building_7007__newyork_jan15", "building_7008__seattle_jan15"]
HOT = ["building_7001__dubai_jul15", "building_7002__lasvegas_jul15", "building_7003__houston_jul15",
       "building_7005__lasvegas_jul15", "building_7007__miami_jul15", "building_7008__chicago_jul15"]
# (arm, policy, kwargs, shipped-simulator runs of the cold and of the hot windows)
ARMS = [("v16", POL, V16, R / "chatter/f_chm", R / "chatter/h_chm"),
        ("pid_water", "baseline:pid_water", None, R / "bigdev/pid_water", R / "bigdev/pid_water")]


def jobs() -> list[dict]:
    out = []
    for arm, pol, kw, _, _ in ARMS:
        for s in COLD + HOT:
            d = {"policy": pol, "base": "none", "out": str(OUT / arm), "scenario": s, "root": str(ROOT)}
            if kw is not None:
                d["kwargs"] = kw
            out.append(memsched.job(d, STEPS))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def loss(f: Path) -> float:
    return float(-np.load(f).astype(float)[:STEPS, 0].mean())


def read() -> None:
    for arm, _, _, rc, rh in ARMS:
        for name, ss, ref in (("cold", COLD, rc), ("hot", HOT, rh)):
            a, b = [], []
            for s in ss:
                f, g = OUT / arm / f"{s}.npy", ref / f"{s}.npy"
                if f.exists() and g.exists():
                    a.append(loss(g)), b.append(loss(f))
                    print(f"{arm:9s} {s:32s} shipped {a[-1]:.5f} fixed {b[-1]:.5f} ({100 * (b[-1] / a[-1] - 1):+.1f} %)")
            if a:
                print(f"== {arm} {name}: {len(a)} windows, shipped {np.mean(a):.5f} fixed {np.mean(b):.5f} "
                      f"({100 * (np.mean(b) / np.mean(a) - 1):+.1f} %)")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    assert "kit_fixed" in os.environ.get("PYTHONPATH", ""), "run on the patched copy"
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"fixsim starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("fixsim END")
    read()


if __name__ == "__main__":
    main()
