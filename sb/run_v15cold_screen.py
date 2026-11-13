"""v15 screen for deep cold at full size (docs/V15COLD.md; candidates and rules written before any screen run):
each candidate of frozen/zonal_v15dev_h.py with V14_PARAMS on the sixteen deep-cold full-size scenarios of the
deep-cold size test (spent as a test, now development), first 2880 steps; v14's runs there are the reference.
Restartable: finished runs are skipped (sb.memsched).

    python -m sb.run_v15cold_screen --window fairbanks_nov21 --cands cu rc curc hp12 >> D:/SmartBuildings_data/v15cold_screen.log 2>&1
    python -m sb.run_v15cold_screen --window fairbanks_nov21 --cands cu rc curc hp12 --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched
from sb.make_coldsize import BUILDINGS, WINDOWS

REPO = Path(__file__).resolve().parents[1]
V14 = json.loads((REPO / "submission/V14_PARAMS.json").read_text())
POL = "D:/SmartBuildings_data/frozen/zonal_v15dev_h.py:TransferPolicy"
DATA = Path("D:/SmartBuildings_data")
REF = DATA / "results/coldsize/full"
OUT = DATA / "results/v15cold"
STEPS = 2880
CANDS = json.loads((REPO / "docs/v15cold_candidates.json").read_text())


def _arg(flag: str, default: list[str]) -> list[str]:
    if flag not in sys.argv:
        return default
    i = sys.argv.index(flag) + 1
    vals = []
    while i < len(sys.argv) and not sys.argv[i].startswith("--"):
        vals.append(sys.argv[i])
        i += 1
    return vals


SEL_W = _arg("--window", list(WINDOWS))
SEL_C = _arg("--cands", list(CANDS))


def jobs() -> list[dict]:
    out = []
    for w in SEL_W:
        for b in BUILDINGS:
            for name in SEL_C:
                out.append(memsched.job({"policy": POL, "base": "none", "kwargs": dict(V14, **CANDS[name]),
                                         "out": str(OUT / name), "scenario": f"{b}__{w}",
                                         "root": str(DATA / "coldsize/full/scenarios")}, STEPS))
    return out


SKIP = DATA / "v15cold_skip.txt"   # candidates that already failed a stage rule (a scenario more than 2 % worse)


def plan() -> tuple[list[dict], list[dict]]:
    skip = set(SKIP.read_text().split()) if SKIP.exists() else set()
    return [j for j in jobs() if not Path(j["result"]).exists() and Path(j["out"]).name not in skip], []


def loss(d: Path, s: str) -> float | None:
    f = d / f"{s}.json"
    return -json.loads(f.read_text())["mean_reward"] if f.exists() else None


def read() -> None:
    scen = [f"{b}__{w}" for w in SEL_W for b in BUILDINGS]
    for name in SEL_C:
        rows = [(s, loss(REF, s), loss(OUT / name, s)) for s in scen]
        rows = [r for r in rows if r[1] is not None and r[2] is not None]
        if not rows:
            print(f"{name}: no runs yet")
            continue
        a = np.array([r[1] for r in rows])
        b = np.array([r[2] for r in rows])
        ch = 100 * (b / a - 1)
        worst = max(rows, key=lambda r: r[2] / r[1])
        mean = 100 * (b.mean() / a.mean() - 1)
        verdict = ""
        if len(rows) == len(scen):
            verdict = "PASS" if mean <= -2.0 and ch.max() <= 2.0 else "FAIL"
        print(f"{name}: {len(rows)}/{len(scen)} scenarios, mean {b.mean():.5f} vs v14 {a.mean():.5f} ({mean:+.2f} %), "
              f"better in {(ch < 0).sum()}, worst {worst[0]} {ch.max():+.2f} % {verdict}")
        for s, x, y in rows:
            print(f"    {s:34s} v14 {x:.5f}  {name} {y:.5f}  ({100 * (y / x - 1):+.2f} %)")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    log = DATA / "cold_diag.log"
    while "cold_diag END" not in (log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""):
        time.sleep(60)
    say(f"v15cold screen starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("v15cold screen END")
    read()


if __name__ == "__main__":
    main()
