"""Why chm won in round 7 (docs/RESULTS_ROUND7.md): trace dumps (sb.bigbld_dump, internal state included) of v15
and chm on the two round-7 buildings with the largest change (7804 chicago_dec03, 7803 newyork_jan29), first 2880
steps, and a scan for zones whose planned heat flips between heating and cooling (the relay of docs/CHATTER.md).
Descriptive; runs after round 7 and the pid_water runs (three simulations at most).

    python -m sb.run_r7_traces >> D:/SmartBuildings_data/r7_traces.log 2>&1
    python -m sb.run_r7_traces --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

DATA = Path("D:/SmartBuildings_data")
ROOT = DATA / "round7/scenarios"
OUT = DATA / "results/round7_diag"
V15_EXTRA = {"empty_day": 1, "empty_h": 1.0}   # V15_PARAMS = V14_PARAMS + these (bigbld_dump merges over V14)
ARMS = {"v15": ("D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy", V15_EXTRA),
        "chm": ("D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py:TransferPolicy",
                dict(V15_EXTRA, cool_hold=2, margin_heat=0.30))}
SCEN = ["building_7804/chicago_dec03", "building_7803/newyork_jan29"]
STEPS = 2880


def jobs() -> list[dict]:
    out = []
    for s in SCEN:
        b, w = s.split("/")
        for arm, (pol, kw) in ARMS.items():
            res = OUT / f"{arm}__{b}__{w}.npz"
            args = ["--policy", pol, "--kwargs", json.dumps(kw), "--scenario", str(ROOT / s), "--start", "0",
                    "--end", str(STEPS), "--out", str(res)]
            out.append(memsched.module_job("sb.bigbld_dump", args, str(ROOT / s), str(res), f"r7diag_{arm}__{b}__{w}"))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def scan(f: Path) -> str:
    """Zones whose planned heat changes sign (|q| > 0.5 kW) within three steps, and heating spent against cooling."""
    z = np.load(f)
    q, T, lo, hi, occ = z["p_q"], z["T"], z["lo"], z["hi"], z["occ"]
    n, nz = q.shape
    s = np.sign(np.where(np.abs(q) > 0.5, q, 0.0))
    flips = sum(((s[k:] * s[:-k]) < 0).sum(0) for k in (1, 2, 3))
    per_day = flips / (n / 288)
    heat, cool = np.clip(q, 0, None).sum(0), np.clip(-q, 0, None).sum(0)
    out_band = (np.maximum(lo - T, 0) + np.maximum(T - hi, 0)) * (occ > 0)
    bad = per_day > 5
    return (f"{f.stem:42s} zones {nz:3d}, >5 flips/day {int(bad.sum()):3d}, heat-cool overlap "
            f"{np.minimum(heat, cool).sum() / max(heat.sum(), 1e-9):6.1%} of heating, occupied K-steps outside the band "
            f"{out_band.sum():7.0f} (in flipping zones {out_band[:, bad].sum():7.0f})")


def read() -> None:
    for f in sorted(OUT.glob("*.npz")):
        print(scan(f))


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"r7 traces start: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("r7 traces END")
    read()


if __name__ == "__main__":
    main()
