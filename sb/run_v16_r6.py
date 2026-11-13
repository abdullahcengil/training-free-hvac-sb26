"""v16 on the six full-size buildings of round 6 (post hoc, docs/RESULTS_ROUND7.md): does the rule of round 7 change
anything in hot and mild windows of new buildings? Against v15's round-6 runs (`results/round6h/ed1`), first 2880
steps. Descriptive; whatever it shows is reported. Runs after the round-7 traces (three simulations at most).

    python -m sb.run_v16_r6 >> D:/SmartBuildings_data/v16_r6.log 2>&1
    python -m sb.run_v16_r6 --read
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
DATA = Path("D:/SmartBuildings_data")
ROOT = DATA / "round6h/scenarios"
REF = DATA / "results/round6h/ed1"
OUT = DATA / "results/round6h/v16"
STEPS = 2880


def scenarios() -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in ROOT.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    return [memsched.job({"policy": POLICY, "base": "none", "kwargs": V16, "out": str(OUT), "scenario": s,
                          "root": str(ROOT)}, STEPS) for s in scenarios()]


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def read() -> None:
    a_all, b_all = [], []
    for s in scenarios():
        fa, fb = REF / f"{s}.npy", OUT / f"{s}.npy"
        if not (fa.exists() and fb.exists()):
            print(f"{s}: not finished")
            continue
        a, b = np.load(fa).astype(float)[:STEPS], np.load(fb).astype(float)[:STEPS]
        la, lb = -a[:, 0].mean(), -b[:, 0].mean()
        a_all.append(la)
        b_all.append(lb)
        same = int((a[:, 0] == b[:, 0]).all())
        print(f"{s:36s} v15 {la:.5f} v16 {lb:.5f} ({100 * (lb / la - 1):+.2f} %)  comfort "
              f"{-0.6 * a[:, 1].mean():.5f} -> {-0.6 * b[:, 1].mean():.5f}  identical {bool(same)}")
    if a_all:
        print(f"mean v15 {np.mean(a_all):.6f} v16 {np.mean(b_all):.6f} ({100 * (np.mean(b_all) / np.mean(a_all) - 1):+.2f} %)")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"v16 r6 starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("v16 r6 END")
    read()


if __name__ == "__main__":
    main()
