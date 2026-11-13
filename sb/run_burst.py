"""Air-handler skip screen (docs/BURST.md). Restartable (sb.memsched, at most 3 runs at a time).

    python -m sb.run_burst check
    python -m sb.run_burst run >> D:/SmartBuildings_data/burst.log 2>&1
    python -m sb.run_burst read
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
from sb.run_tuned import BIG, COLD, DATA, HOT, R, REPO, STEPS, V16, scen

POL = f"{REPO.as_posix()}/policies/zonal_v16burst.py:TransferPolicy"
OUT = R / "burst"
B = dict(V16, glide_safety=1.20, glide_floor=-26.0, margin_heat=0.20, f_heat_rec=0.45, f_heat_max=0.40)
ARMS = {"B": B, "S1": dict(B, skip_ahu=1), "S2": dict(B, skip_ahu=2)}
WIN = COLD + HOT


def jobs() -> list[dict]:
    return [memsched.job({"policy": POL, "base": "none", "kwargs": kw, "out": str(OUT / arm), "scenario": s,
                          "root": str(BIG)}, STEPS) for s in WIN for arm, kw in ARMS.items()]


def check() -> None:
    r7 = DATA / "round7/scenarios"
    s = scen(r7)[0]
    j = memsched.job({"policy": POL, "base": "none", "kwargs": dict(V16, skip_ahu=0), "out": str(OUT / "check/k1"),
                      "scenario": s, "root": str(r7)}, 288)
    memsched.run(lambda: ([j] if not Path(j["result"]).exists() else [], []), max_jobs=1, reserve=0.5, say=print)
    x = np.load(OUT / "check/k1" / f"{s}.npy").astype(float)
    y = np.load(R / "round7/chm" / f"{s}.npy").astype(float)[:288]
    same = np.array_equal(x, y)
    print(f"{time.strftime('%d %b %H:%M:%S')} burst check k1: {'IDENTICAL' if same else 'DIFFERENT'} "
          f"(max diff {np.abs(x - y).max():.3g})", flush=True)
    sys.exit(0 if same else 1)


def read() -> None:
    loss = lambda a: -a[:STEPS, 0].mean()
    comf = lambda a: -0.6 * a[:STEPS, 1].mean()
    res = {}
    print("window                                   B         S1/B     S2/B    comfort B  S1  S2 (x1e5)")
    for s in WIN:
        row = {}
        for arm in ARMS:
            f = OUT / arm / f"{s}.npy"
            if f.exists():
                row[arm] = np.load(f).astype(float)
        res[s] = row
        if "B" in row:
            b = row["B"]
            r1 = f"{loss(row['S1']) / loss(b):8.4f}" if "S1" in row else "       -"
            r2 = f"{loss(row['S2']) / loss(b):8.4f}" if "S2" in row else "       -"
            cs = "  ".join(f"{1e5 * comf(row[a]):6.1f}" if a in row else "     -" for a in ARMS)
            print(f"{s:38s} {loss(b):.5f}  {r1} {r2}   {cs}")
    for arm in ("S1", "S2"):
        both = [s for s in WIN if "B" in res[s] and arm in res[s]]
        if not both:
            continue
        lb = np.mean([loss(res[s]["B"]) for s in both]); la = np.mean([loss(res[s][arm]) for s in both])
        cb = np.mean([comf(res[s]["B"]) for s in both]); ca = np.mean([comf(res[s][arm]) for s in both])
        worse = sum(loss(res[s][arm]) > loss(res[s]["B"]) for s in both)
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
        say(f"burst starts: {len(plan()[0])} of {len(jobs())} runs to do")
        memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
        say("burst END")
        read()


if __name__ == "__main__":
    main()
