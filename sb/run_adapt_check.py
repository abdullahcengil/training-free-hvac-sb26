"""Known-answer checks K1 and K2 of docs/ADAPT_START.md (288 steps, first round-7 building), then exit non-zero on
failure so the chain stops before any candidate run.

    python -m sb.run_adapt_check >> D:/SmartBuildings_data/tuned.log 2>&1
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched
from sb.run_tuned import CANDS, DATA, OUT, POLS, R, V16, scen

R7 = DATA / "round7/scenarios"
CHK = OUT / "adapt_check"
POL = POLS["c8ad"]
C8 = {k: v for k, v in CANDS["c8ad"].items() if k != "glide_adapt"}
ARMS = {"k1": (dict(V16, glide_adapt=0), R / "round7/chm"),
        "k2": (dict(V16, **C8, glide_adapt=1, ga_init=1.0, ga_down=0.0, ga_up=0.0), OUT / "c8/r7")}


def jobs() -> list[dict]:
    s = scen(R7)[0]
    return [memsched.job({"policy": POL, "base": "none", "kwargs": kw, "out": str(CHK / k), "scenario": s,
                          "root": str(R7)}, 288) for k, (kw, _) in ARMS.items()]


def main() -> None:
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say("adapt check starts")
    memsched.run(lambda: ([j for j in jobs() if not Path(j["result"]).exists()], []), max_jobs=2, reserve=0.5, say=say)
    s = scen(R7)[0]
    ok = True
    for k, (_, ref) in ARMS.items():
        x = np.load(CHK / k / f"{s}.npy").astype(float)
        y = np.load(ref / f"{s}.npy").astype(float)[:288]
        same = np.array_equal(x, y)
        ok &= same
        say(f"adapt check {k}: {'IDENTICAL' if same else 'DIFFERENT'} (max diff {np.abs(x - y).max():.3g})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
