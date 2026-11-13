"""First-work-day screen (docs/MONDAY.md). Restartable (sb.memsched, at most 3 runs at a time).

    python -m sb.run_mon check
    python -m sb.run_mon run >> D:/SmartBuildings_data/mon.log 2>&1
    python -m sb.run_mon read
"""
from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched
from sb.run_burst import B
from sb.run_tuned import BIG, COLD, DATA, R, REPO, STEPS, V16, scen

POL = f"{REPO.as_posix()}/policies/zonal_v16mon.py:TransferPolicy"
OUT = R / "mon"
ARMS = {"M1": dict(B, mon_mode=1),
        "M2": dict(B, mon_mode=1, mon_safety=0.80, mon_floor=-20.0, mon_margin=0.25)}


def jobs() -> list[dict]:
    return [memsched.job({"policy": POL, "base": "none", "kwargs": kw, "out": str(OUT / arm), "scenario": s,
                          "root": str(BIG)}, STEPS) for s in COLD for arm, kw in ARMS.items()]


def check() -> None:
    r7 = DATA / "round7/scenarios"
    s = scen(r7)[0]
    j = memsched.job({"policy": POL, "base": "none", "kwargs": dict(V16, mon_mode=0), "out": str(OUT / "check/k1"),
                      "scenario": s, "root": str(r7)}, 288)
    memsched.run(lambda: ([j] if not Path(j["result"]).exists() else [], []), max_jobs=1, reserve=0.5, say=print)
    x = np.load(OUT / "check/k1" / f"{s}.npy").astype(float)
    y = np.load(R / "round7/chm" / f"{s}.npy").astype(float)[:288]
    same = np.array_equal(x, y)
    print(f"{time.strftime('%d %b %H:%M:%S')} mon check k1: {'IDENTICAL' if same else 'DIFFERENT'} "
          f"(max diff {np.abs(x - y).max():.3g})", flush=True)
    sys.exit(0 if same else 1)


def read() -> None:
    loss = lambda a: -a[:STEPS, 0].mean()
    comf = lambda a: -0.6 * a[:STEPS, 1].mean()
    rows = {}
    for s in COLD:
        fb = R / "burst/B" / f"{s}.npy"
        if not fb.exists():
            continue
        rows[s] = {"B": np.load(fb).astype(float)}
        for arm in ARMS:
            f = OUT / arm / f"{s}.npy"
            if f.exists():
                rows[s][arm] = np.load(f).astype(float)
        print(s, f"B {loss(rows[s]['B']):.5f}",
              "  ".join(f"{a}/B {loss(rows[s][a]) / loss(rows[s]['B']):.4f}" for a in ARMS if a in rows[s]))
    for arm in ARMS:
        both = [s for s in rows if arm in rows[s]]
        if not both:
            continue
        lb = np.mean([loss(rows[s]["B"]) for s in both]); la = np.mean([loss(rows[s][arm]) for s in both])
        cb = np.mean([comf(rows[s]["B"]) for s in both]); ca = np.mean([comf(rows[s][arm]) for s in both])
        worse = sum(loss(rows[s][arm]) > loss(rows[s]["B"]) for s in both)
        print(f"{arm}: n {len(both)}  mean loss {la:.5f} vs B {lb:.5f} ({100 * (la / lb - 1):+.2f} %)  comfort x{ca / max(cb, 1e-12):.2f}"
              f"  worse in {worse}")


def main() -> None:
    cmd = sys.argv[1]
    if cmd == "check":
        check()
    elif cmd == "read":
        read()
    elif cmd == "run":
        say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
        plan = lambda: ([j for j in jobs() if not Path(j["result"]).exists()], [])
        say(f"mon starts: {len(plan()[0])} of {len(jobs())} runs to do")
        memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
        say("mon END")
        read()


if __name__ == "__main__":
    main()
