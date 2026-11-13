"""One-parameter sensitivity of v14 at full size (docs/FULLSWEEP.md; variants and rule written before any run):
each variant of V14_PARAMS with the frozen v14 file on four full-size development scenarios (docs/BIGDEV.md), first
2880 steps; v14's runs there are the reference. Restartable: finished runs are skipped (sb.memsched).

    python -m sb.run_fullsweep >> D:/SmartBuildings_data/fullsweep.log 2>&1
    python -m sb.run_fullsweep --read
    python -m sb.run_fullsweep --all --vars fhm316 >> D:/SmartBuildings_data/fullsweep.log 2>&1   (all twelve)
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
OUT = DATA / "results/fullsweep"
STEPS = 2880
VARS = {
    "fhm316": {"f_heat_max": 0.316},
    "fhm20": {"f_heat_max": 0.20},
    "gs50": {"glide_safety": 0.50},
    "gs80": {"glide_safety": 0.80},
    "dmp90": {"damping": 0.90},
    "dmp60": {"damping": 0.60},
    "cs70": {"cool_safety": 0.70},
    "mh30": {"margin_heat": 0.30},
}
FOUR = ["building_7001__dubai_jul15", "building_7005__lasvegas_jul15",
        "building_7001__chicago_jan15", "building_7007__newyork_jan15"]
TWELVE = [j["scenario"] for j in json.loads((REPO / "sb/jobs_bigdev_v14.json").read_text())]


def _arg(flag: str, default: list[str]) -> list[str]:
    if flag not in sys.argv:
        return default
    i = sys.argv.index(flag) + 1
    vals = []
    while i < len(sys.argv) and not sys.argv[i].startswith("--"):
        vals.append(sys.argv[i])
        i += 1
    return vals


SEL_V = _arg("--vars", list(VARS))
SCEN = TWELVE if "--all" in sys.argv else FOUR


# Heating-only variants gave exactly v14's loss in Dubai in July (fhm316, fhm20, gs50: 0.00 %), so they are not run
# in the two July windows; read() counts them there at v14's loss (docs/FULLSWEEP.md, deviation of 30 Oct 02:21).
HEAT_ONLY = {"fhm316", "fhm20", "gs50", "gs80", "mh30"}
HOT = {"building_7001__dubai_jul15", "building_7005__lasvegas_jul15"}


def skipped(v: str, s: str) -> bool:
    return v in HEAT_ONLY and s in HOT and s != "building_7001__dubai_jul15"


def jobs() -> list[dict]:
    # Scenario-major order: every variant's run on the first scenario before any second one.
    return [memsched.job({"policy": POL, "base": "none", "kwargs": dict(V14, **VARS[v]), "out": str(OUT / v),
                          "scenario": s, "root": str(ROOT)}, STEPS)
            for s in SCEN for v in SEL_V if not skipped(v, s)]


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def loss(d: Path, s: str) -> float | None:
    f = d / f"{s}.json"
    return -json.loads(f.read_text())["mean_reward"] if f.exists() else None


def read() -> None:
    for v in SEL_V:
        rows = [(s, loss(REF, s), loss(REF, s) if skipped(v, s) else loss(OUT / v, s)) for s in SCEN]
        rows = [r for r in rows if r[1] is not None and r[2] is not None]
        if not rows:
            print(f"{v}: no runs yet")
            continue
        a = np.array([r[1] for r in rows])
        b = np.array([r[2] for r in rows])
        ch = 100 * (b / a - 1)
        mean = 100 * (b.mean() / a.mean() - 1)
        verdict = ""
        if len(rows) == len(SCEN):
            verdict = "CANDIDATE" if mean <= -1.0 and ch.max() <= 2.0 else "no"
        print(f"{v:7s} {VARS[v]}: {len(rows)}/{len(SCEN)}, mean {b.mean():.5f} vs v14 {a.mean():.5f} ({mean:+.2f} %), "
              f"better in {(ch < 0).sum()}, worst {ch.max():+.2f} % {verdict}")
        for s, x, y in rows:
            print(f"    {s:34s} v14 {x:.5f}  {v} {y:.5f}  ({100 * (y / x - 1):+.2f} %)")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"fullsweep starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("fullsweep END")
    read()


if __name__ == "__main__":
    main()
