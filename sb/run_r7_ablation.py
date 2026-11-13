"""Which half of v16 won round 7? (post hoc, docs/RESULTS_ROUND7.md): the two changes of v16 one at a time on the six
round-7 buildings, first 2880 steps: `ch` = V15 + cool_hold 2 (the margin unchanged) and `mh` = V15 + margin_heat 0.30
(no cool_hold), against v15 and v16 (chm) of the round. Descriptive; whatever it shows is reported. Runs after the
post-hoc v16 runs on round 6 (three simulations at most).

    python -m sb.run_r7_ablation >> D:/SmartBuildings_data/r7_ablation.log 2>&1
    python -m sb.run_r7_ablation --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
V15 = json.loads((REPO / "submission/V15_PARAMS.json").read_text())
POLICY = "D:/SmartBuildings_data/frozen/zonal_v16f.py:TransferPolicy"   # with cool_hold 0 it computes what v15 computes
ARMS = {"ch": dict(V15, cool_hold=2), "mh": dict(V15, margin_heat=0.30)}
DATA = Path("D:/SmartBuildings_data")
ROOT = DATA / "round7/scenarios"
OUT = DATA / "results/round7"
STEPS = 2880


def scenarios() -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in ROOT.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    return [memsched.job({"policy": POLICY, "base": "none", "kwargs": kw, "out": str(OUT / arm), "scenario": s,
                          "root": str(ROOT)}, STEPS) for s in scenarios() for arm, kw in ARMS.items()]


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def read() -> None:
    arms = ["v15", "ch", "mh", "chm"]
    tot = {a: [] for a in arms}
    for s in scenarios():
        f = {a: OUT / a / f"{s}.npy" for a in arms}
        if not all(p.exists() for p in f.values()):
            print(f"{s}: not finished")
            continue
        l = {a: float(-np.load(p).astype(float)[:STEPS, 0].mean()) for a, p in f.items()}
        for a in arms:
            tot[a].append(l[a])
        print(f"{s:36s} " + "  ".join(f"{a} {l[a]:.5f} ({100 * (l[a] / l['v15'] - 1):+.2f} %)" for a in arms))
    if tot["v15"]:
        m = {a: np.mean(v) for a, v in tot.items()}
        print("mean " + "  ".join(f"{a} {m[a]:.6f} ({100 * (m[a] / m['v15'] - 1):+.2f} %)" for a in arms))


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"r7 ablation starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("r7 ablation END")
    read()


if __name__ == "__main__":
    main()
