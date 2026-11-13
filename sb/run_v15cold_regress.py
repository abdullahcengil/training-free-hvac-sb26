"""v15 deep-cold screen, step 3 (docs/V15COLD.md): regression checks of one candidate before any blind round:
the twelve full-size development scenarios of docs/BIGDEV.md (first 2880 steps; v14 in results/bigdev/v14) and the
30 training scenarios at full length (8640 steps; v14 in results/dev14_8640/of3). Restartable (sb.memsched).

    python -m sb.run_v15cold_regress --cand cu >> D:/SmartBuildings_data/v15cold_regress.log 2>&1
    python -m sb.run_v15cold_regress --cand cu --read
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
CANDS = json.loads((REPO / "docs/v15cold_candidates.json").read_text())
POL = "D:/SmartBuildings_data/frozen/zonal_v15dev_h.py:TransferPolicy"
DATA = Path("D:/SmartBuildings_data")
CAND = sys.argv[sys.argv.index("--cand") + 1] if "--cand" in sys.argv else "cu"
SETS = {
    # name: (jobs file entries, steps, v14 reference folder, output folder)
    "bigdev": ([j["scenario"] for j in json.loads((REPO / "sb/jobs_bigdev_v14.json").read_text())], 2880,
               DATA / "results/bigdev/v14", DATA / f"results/v15cold_regress/{CAND}/bigdev",
               str(DATA / "bigdev/scenarios")),
    "train30": ([j["scenario"] for j in json.loads((REPO / "sb/jobs_v14_full.json").read_text()) if "root" not in j],
                8640, DATA / "results/dev14_8640/of3", DATA / f"results/v15cold_regress/{CAND}/train30", None),
}


def jobs() -> list[dict]:
    out = []
    for name, (scen, steps, _ref, outdir, root) in SETS.items():
        for s in scen:
            j = {"policy": POL, "base": "none", "kwargs": dict(V14, **CANDS[CAND]), "out": str(outdir), "scenario": s}
            if root:
                j["root"] = root
            out.append(memsched.job(j, steps))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def read() -> None:
    for name, (scen, _steps, ref, outdir, _root) in SETS.items():
        rows = []
        for s in scen:
            a, b = ref / f"{s}.json", outdir / f"{s}.json"
            if a.exists() and b.exists():
                rows.append((s, -json.loads(a.read_text())["mean_reward"], -json.loads(b.read_text())["mean_reward"]))
        if not rows:
            print(f"{name}: no runs yet")
            continue
        x = np.array([r[1] for r in rows])
        y = np.array([r[2] for r in rows])
        ch = 100 * (y / x - 1)
        print(f"{name}: {len(rows)}/{len(scen)}, mean {y.mean():.6f} vs v14 {x.mean():.6f} ({100 * (y.mean() / x.mean() - 1):+.2f} %), "
              f"worst {rows[int(np.argmax(ch))][0]} {ch.max():+.2f} %, better in {(ch < -1e-9).sum()}, equal in {(np.abs(ch) <= 1e-9).sum()}")
        for s, a, b in rows:
            if abs(b / a - 1) > 1e-9:
                print(f"    {s:40s} v14 {a:.5f}  {CAND} {b:.5f}  ({100 * (b / a - 1):+.2f} %)")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"v15cold regress ({CAND}) starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say(f"v15cold regress ({CAND}) END")
    read()


if __name__ == "__main__":
    main()
