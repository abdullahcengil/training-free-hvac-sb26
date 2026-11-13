"""Round 6 (blind, full size; docs/PREREGISTRATION_6.md): frozen v14 and the frozen v15 candidate on the six new
deep-cold buildings of sb/make_round6.py and on the twelve full-size scenarios of sb/make_bigtest.py (set aside on
25 Oct for v15's full check), first 2880 steps. Restartable (sb.memsched).

    python -m sb.run_round6 >> D:/SmartBuildings_data/round6.log 2>&1
    python -m sb.run_round6 --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
DATA = Path("D:/SmartBuildings_data")
CTRL = {
    "v14": ("D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy", REPO / "submission/V14_PARAMS.json"),
    "v15": ("D:/SmartBuildings_data/frozen/zonal_v15f.py:TransferPolicy", REPO / "submission/V15_PARAMS.json"),
}
SETS = {"cold": DATA / "round6/scenarios", "bigtest": DATA / "bigtest/scenarios"}
OUT = DATA / "results/round6"
STEPS = 2880


def scenarios(root: Path) -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in root.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    out = []
    for set_name, root in SETS.items():
        for s in scenarios(root):
            for c, (pol, params) in CTRL.items():
                out.append(memsched.job({"policy": pol, "base": "none", "kwargs": json.loads(params.read_text()),
                                         "out": str(OUT / set_name / c), "scenario": s, "root": str(root)}, STEPS))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def loss(d: Path, s: str) -> float | None:
    f = d / f"{s}.json"
    return -json.loads(f.read_text())["mean_reward"] if f.exists() else None


def read() -> None:
    for set_name, root in SETS.items():
        rows = []
        for s in scenarios(root):
            a, b = loss(OUT / set_name / "v14", s), loss(OUT / set_name / "v15", s)
            if a is not None and b is not None:
                rows.append((s, a, b))
                print(f"  {set_name:7s} {s:36s} v14 {a:.5f}  v15 {b:.5f}  ({100 * (b / a - 1):+.2f} %)")
        if rows:
            x, y = np.array([r[1] for r in rows]), np.array([r[2] for r in rows])
            print(f"{set_name}: {len(rows)}/{len(scenarios(root))} scenarios, v14 {x.mean():.5f}, v15 {y.mean():.5f} "
                  f"({100 * (y.mean() / x.mean() - 1):+.2f} %), v15 better in {(y < x).sum()}, worst "
                  f"{100 * (y / x - 1).max():+.2f} %")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"round6 starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("round6 END")
    read()


if __name__ == "__main__":
    main()
