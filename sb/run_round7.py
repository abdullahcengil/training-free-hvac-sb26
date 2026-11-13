"""Round 7 (blind, full size; docs/PREREGISTRATION_7.md): v15 and chm (v15 + cool_hold 2 + margin_heat 0.30, the
candidate of docs/CHATTER.md) on the six scenarios of sb.make_round7, first 2880 steps each. Run only if the screen
of docs/CHATTER.md passes and after the plan is stamped and the buildings generated. Restartable (sb.memsched).

    python -m sb.run_round7 >> D:/SmartBuildings_data/round7.log 2>&1
    python -m sb.run_round7 --read
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
ARMS = {"v15": ("D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy", V15),
        "chm": ("D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py:TransferPolicy",
                dict(V15, cool_hold=2, margin_heat=0.30))}
DATA = Path("D:/SmartBuildings_data")
ROOT = DATA / "round7/scenarios"
OUT = DATA / "results/round7"
STEPS = 2880


def scenarios() -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in ROOT.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    return [memsched.job({"policy": pol, "base": "none", "kwargs": kw, "out": str(OUT / arm), "scenario": s,
                          "root": str(ROOT)}, STEPS)
            for s in scenarios() for arm, (pol, kw) in ARMS.items()]


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def read() -> None:
    rows = []
    for s in scenarios():
        f = {arm: OUT / arm / f"{s}.npy" for arm in ARMS}
        if not all(p.exists() for p in f.values()):
            print(f"{s}: not finished")
            continue
        a = np.load(f["v15"]).astype(float)
        b = np.load(f["chm"]).astype(float)
        la, lb = -a[:, 0].mean(), -b[:, 0].mean()
        ca, cb = -0.6 * a[:, 1].mean(), -0.6 * b[:, 1].mean()
        rows.append((s, la, lb, ca, cb))
        print(f"{s:40s} v15 {la:.5f} chm {lb:.5f} ({100 * (lb / la - 1):+.2f} %)  comfort {ca:.5f} -> {cb:.5f}")
    if len(rows) < len(scenarios()) or not rows:
        return
    la = np.array([r[1] for r in rows])
    lb = np.array([r[2] for r in rows])
    ch = 100 * (lb / la - 1)
    ca = sum(r[3] for r in rows)
    cb = sum(r[4] for r in rows)
    h1 = lb.mean() <= 0.995 * la.mean()
    h2 = int((lb < la).sum()) >= 4
    h3 = float(ch.max()) <= 2.0
    h4 = cb <= 1.5 * ca
    print(f"H1 mean {lb.mean():.6f} vs {la.mean():.6f} ({100 * (lb.mean() / la.mean() - 1):+.2f} %; mark -0.5 %): "
          f"{'PASS' if h1 else 'FAIL'}")
    print(f"H2 better in {(lb < la).sum()} of {len(rows)} (mark 4): {'PASS' if h2 else 'FAIL'}")
    print(f"H3 worst building {ch.max():+.2f} % (mark +2 %): {'PASS' if h3 else 'FAIL'}")
    print(f"H4 comfort {cb:.5f} vs {ca:.5f} (x{cb / max(ca, 1e-12):.2f}; mark x1.5): {'PASS' if h4 else 'FAIL'}")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"round 7 starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("round 7 END")
    read()


if __name__ == "__main__":
    main()
