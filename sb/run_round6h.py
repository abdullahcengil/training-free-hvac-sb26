"""Round 6 (blind, full size, holidays; docs/PREREGISTRATION_6.md): v14 and v14 with the empty-holiday rule (ed1) on
the six scenarios of sb.make_round6h, first 2880 steps each. Restartable (sb.memsched).

    python -m sb.run_round6h >> D:/SmartBuildings_data/round6h.log 2>&1
    python -m sb.run_round6h --read
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
V14 = json.loads((REPO / "submission/V14_PARAMS.json").read_text())
POL = "D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy"
DATA = Path("D:/SmartBuildings_data")
ROOT = DATA / "round6h/scenarios"
OUT = DATA / "results/round6h"
STEPS = 2880
ARMS = {"v14": {}, "ed1": {"empty_day": 1, "empty_h": 1.0}}
HOL = set(USFederalHolidayCalendar().holidays("2023-01-01", "2023-12-31").date)


def scenarios() -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in ROOT.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    return [memsched.job({"policy": POL, "base": "none", "kwargs": dict(V14, **kw), "out": str(OUT / arm),
                          "scenario": s, "root": str(ROOT)}, STEPS)
            for s in scenarios() for arm, kw in ARMS.items()]


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def holiday_0700(s: str) -> int:
    b, w = s.split("__")
    t0 = pd.Timestamp(re.search(r"start_timestamp\s*=\s*'([^']+)'",
                                (ROOT / b / w / "config.gin").read_text()).group(1))
    ts = t0 + pd.to_timedelta(np.arange(STEPS) * 5, unit="min")
    hd = np.array([t.date() in HOL and t.weekday() < 5 for t in ts])
    return int(np.argmax(hd)) + 7 * 12


def read() -> None:
    rows = []
    for s in scenarios():
        f = {arm: OUT / arm / f"{s}.npy" for arm in ARMS}
        if not all(p.exists() for p in f.values()):
            print(f"{s}: not finished")
            continue
        a = np.load(f["v14"]).astype(float)
        b = np.load(f["ed1"]).astype(float)
        k = holiday_0700(s)
        same = float(np.max(np.abs(a[:k, 0] - b[:k, 0])))
        la, lb = -a[:, 0].mean(), -b[:, 0].mean()
        ca, cb = -0.6 * a[:, 1].mean(), -0.6 * b[:, 1].mean()
        rows.append((s, la, lb, ca, cb, same))
        print(f"{s:34s} v14 {la:.5f} ed1 {lb:.5f} ({100 * (lb / la - 1):+.2f} %)  comfort {ca:.5f} -> {cb:.5f}  "
              f"identity to 07:00 on the holiday {same:.1e}")
    if len(rows) < len(scenarios()) or not rows:
        return
    la = np.array([r[1] for r in rows])
    lb = np.array([r[2] for r in rows])
    ca = sum(r[3] for r in rows)
    cb = sum(r[4] for r in rows)
    h1 = lb.mean() <= 0.995 * la.mean()
    h2 = int((lb < la).sum()) >= 5
    h3 = cb <= 1.10 * ca
    h4 = max(r[5] for r in rows) == 0.0
    print(f"H1 mean {lb.mean():.6f} vs {la.mean():.6f} ({100 * (lb.mean() / la.mean() - 1):+.2f} %): "
          f"{'PASS' if h1 else 'FAIL'}")
    print(f"H2 better in {(lb < la).sum()} of {len(rows)}: {'PASS' if h2 else 'FAIL'}")
    print(f"H3 comfort {cb:.5f} vs {ca:.5f} (x{cb / max(ca, 1e-12):.2f}): {'PASS' if h3 else 'FAIL'}")
    print(f"H4 identical before 07:00 on the holiday: {'PASS' if h4 else 'FAIL'}")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"round 6 starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("round 6 END")
    read()


if __name__ == "__main__":
    main()
