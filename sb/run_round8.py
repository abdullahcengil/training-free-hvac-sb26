"""Round 8 (blind, full size; docs/PREREGISTRATION_8.md): v16 and sp1 (v16 + safety_pred 1, the candidate of
docs/HEATNET.md) on the six scenarios of sb.make_round8, first 2880 steps each. Run only if the screen of
docs/HEATNET.md passes and after the plan is stamped and the buildings generated. Restartable (sb.memsched).

    python -m sb.run_round8 >> D:/SmartBuildings_data/round8.log 2>&1
    python -m sb.run_round8 --read
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
POL = "D:/SmartBuildings_data/frozen/zonal_v16f.py:TransferPolicy"
ARMS = {"v16": (POL, V16), "sp1": (POL, dict(V16, safety_pred=1))}
DATA = Path("D:/SmartBuildings_data")
ROOT = DATA / "round8/scenarios"
OUT = DATA / "results/round8"
STEPS = 2880


def scenarios() -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in ROOT.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    main = [memsched.job({"policy": pol, "base": "none", "kwargs": kw, "out": str(OUT / arm), "scenario": s,
                          "root": str(ROOT)}, STEPS)
            for s in scenarios() for arm, (pol, kw) in ARMS.items()]
    # pid_water, descriptive and queued after both arms: no hypothesis, only the transfer figure's count (as
    # docs/BASELINE_R67.md for rounds 6 and 7).
    return main + [memsched.job({"policy": "baseline:pid_water", "base": "none", "out": str(OUT / "pid_water"),
                                 "scenario": s, "root": str(ROOT)}, STEPS) for s in scenarios()]


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def read() -> None:
    rows = []
    for s in scenarios():
        f = {arm: OUT / arm / f"{s}.npy" for arm in ARMS}
        if not all(p.exists() for p in f.values()):
            print(f"{s}: not finished")
            continue
        a = np.load(f["v16"]).astype(float)
        b = np.load(f["sp1"]).astype(float)
        la, lb = -a[:, 0].mean(), -b[:, 0].mean()
        ca, cb = -0.6 * a[:, 1].mean(), -0.6 * b[:, 1].mean()
        rows.append((s, la, lb, ca, cb))
        print(f"{s:40s} v16 {la:.5f} sp1 {lb:.5f} ({100 * (lb / la - 1):+.2f} %)  comfort {ca:.5f} -> {cb:.5f}")
    if len(rows) < len(scenarios()) or not rows:
        return
    la = np.array([r[1] for r in rows])
    lb = np.array([r[2] for r in rows])
    ch = 100 * (lb / la - 1)
    ca = sum(r[3] for r in rows)
    cb = sum(r[4] for r in rows)
    h1 = lb.mean() <= 0.997 * la.mean()
    h2 = int((lb <= la).sum()) >= 5
    h3 = float(ch.max()) <= 1.0
    h4 = cb <= 1.0 * ca
    print(f"H1 mean {lb.mean():.6f} vs {la.mean():.6f} ({100 * (lb.mean() / la.mean() - 1):+.2f} %; mark -0.3 %): "
          f"{'PASS' if h1 else 'FAIL'}")
    print(f"H2 at or below v16 in {(lb <= la).sum()} of {len(rows)} (mark 5): {'PASS' if h2 else 'FAIL'}")
    print(f"H3 worst building {ch.max():+.2f} % (mark +1 %): {'PASS' if h3 else 'FAIL'}")
    print(f"H4 comfort {cb:.5f} vs {ca:.5f} (x{cb / max(ca, 1e-12):.2f}; mark x1.0): {'PASS' if h4 else 'FAIL'}")
    p = [OUT / "pid_water" / f"{r[0]}.npy" for r in rows]
    if all(f.exists() for f in p):
        lp = np.array([-np.load(f).astype(float)[:, 0].mean() for f in p])
        fin, name = (lb, "sp1") if h1 and h2 and h3 else (la, "v16")
        print(f"pid_water (descriptive): {name} below it in {int((fin < lp).sum())} of {len(rows)}; ratios "
              + ", ".join(f"{x:.3f}" for x in fin / lp))


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"round 8 starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("round 8 END")
    read()


if __name__ == "__main__":
    main()
