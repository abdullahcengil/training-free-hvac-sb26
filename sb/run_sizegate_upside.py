"""Upside check of docs/SIZEGATE.md (rule written before any run; not a candidate): v14 + margin_heat 0.30 +
glide_safety 0.80 on the six cold full-size development windows, first 2880 steps, against v14's runs there. Waits for
the size-gate diagnostic to end (three simulations at most). Restartable (sb.memsched).

    python -m sb.run_sizegate_upside >> D:/SmartBuildings_data/sizegate.log 2>&1
    python -m sb.run_sizegate_upside --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
V14 = json.loads((REPO / "submission/V14_PARAMS.json").read_text())
POL = "D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy"
DATA = Path("D:/SmartBuildings_data")
ROOT = DATA / "bigdev/scenarios"
REF = DATA / "results/bigdev/v14"
OUT = DATA / "results/sizegate_upside/hl2"
LOG = DATA / "sizegate.log"
STEPS = 2880
HL2 = {"margin_heat": 0.30, "glide_safety": 0.80}
COLD = ["building_7001__chicago_jan15", "building_7002__helena_jan15", "building_7003__duluth_jan15",
        "building_7005__chicago_jan15", "building_7007__newyork_jan15", "building_7008__seattle_jan15"]


def jobs() -> list[dict]:
    return [memsched.job({"policy": POL, "base": "none", "kwargs": dict(V14, **HL2), "out": str(OUT),
                          "scenario": s, "root": str(ROOT)}, STEPS) for s in COLD]


# Fillers (diagnostic, docs/SIZEGATE.md): v15 unchanged on the six shipped training buildings in their Fairbanks
# windows at full length, with the internal trace, to see where each one's median 1/g goes over a month.
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
TRAIN_COLD = [(f"building_train_{b}", f"fairbanks_{w}") for b, w in ((1, 1), (2, 2), (4, 4), (5, 5), (7, 7), (8, 8))]
LONG = DATA / "results/sizegate"


def fillers() -> list[dict]:
    out = []
    for b, w in TRAIN_COLD:
        scen = TRAIN / b / w
        res = LONG / f"train30__{b}__{w}.npz"
        out.append(memsched.module_job("sb.bigbld_dump", ["--scenario", str(scen), "--start", "0", "--end", "8640",
                                                          "--kwargs", json.dumps({"empty_day": 1, "empty_h": 1.0}),
                                                          "--out", str(res)], str(scen), str(res),
                                       f"sizegate_{res.stem}"))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    # --no-fillers (30 Oct 18:20): the month-long training traces only served the room-size gate, which the upside
    # check's first results no longer support (docs/SIZEGATE.md); they are dropped to free the machine.
    keep = "--no-fillers" not in sys.argv
    return ([j for j in jobs() if not Path(j["result"]).exists()],
            [j for j in fillers() if keep and not Path(j["result"]).exists()])


def loss(d: Path, s: str) -> float | None:
    f = d / f"{s}.json"
    return -json.loads(f.read_text())["mean_reward"] if f.exists() else None


def read() -> None:
    rows = [(s, loss(REF, s), loss(OUT, s)) for s in COLD]
    rows = [r for r in rows if r[1] is not None and r[2] is not None]
    if not rows:
        print("no runs yet")
        return
    a = np.array([r[1] for r in rows])
    b = np.array([r[2] for r in rows])
    mean = 100 * (b.mean() / a.mean() - 1)
    verdict = ("GO ON (size-aware rule)" if mean <= -1.5 else "STOP (v15 stays)") if len(rows) == len(COLD) else ""
    print(f"hl2 {HL2}: {len(rows)}/{len(COLD)}, mean {b.mean():.5f} vs v14 {a.mean():.5f} ({mean:+.2f} %), "
          f"better in {int((b < a).sum())} {verdict}")
    for s, x, y in rows:
        print(f"    {s:34s} v14 {x:.5f}  hl2 {y:.5f}  ({100 * (y / x - 1):+.2f} %)")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    while "sizegate END" not in (LOG.read_text(encoding="utf-8", errors="replace") if LOG.exists() else ""):
        time.sleep(60)
    say(f"upside starts: {len(plan()[0])} of {len(jobs())} runs to do, {len(plan()[1])} month-long training traces")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("upside END")
    read()


if __name__ == "__main__":
    main()
