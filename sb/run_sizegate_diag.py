"""Size-gate diagnostic (docs/SIZEGATE.md; description only): v15 unchanged on the first 864 steps of the cold window
of every shipped training building, every full-size development building and its scaled twin, with sb.bigbld_dump
(each zone's identified mass-model parameters and the true room areas). Restartable: finished traces are skipped
(sb.memsched).

    python -m sb.run_sizegate_diag >> D:/SmartBuildings_data/sizegate.log 2>&1
    python -m sb.sizegate_read
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from sb import memsched

DATA = Path("D:/SmartBuildings_data")
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
OUT = DATA / "results/sizegate"
STEPS = 864
V15_EXTRA = json.dumps({"empty_day": 1, "empty_h": 1.0})   # V15_PARAMS = V14_PARAMS + these two
TRAIN_COLD = [(f"building_train_{b}", w) for b, w in
              ((1, "fairbanks_1"), (2, "fairbanks_2"), (4, "fairbanks_4"), (5, "fairbanks_5"), (7, "fairbanks_7"),
               (8, "fairbanks_8"))]
FULL_COLD = [("building_7001", "chicago_jan15"), ("building_7002", "helena_jan15"), ("building_7003", "duluth_jan15"),
             ("building_7005", "chicago_jan15"), ("building_7007", "newyork_jan15"), ("building_7008", "seattle_jan15")]
SCALED_COLD = [p for p in FULL_COLD if p[0] != "building_7005"]   # bigdev_scaled has no 7005


def scenarios() -> list[tuple[str, Path]]:
    out = [("train", TRAIN / b / w) for b, w in TRAIN_COLD]
    out += [("full", DATA / "bigdev/scenarios" / b / w) for b, w in FULL_COLD]
    out += [("scaled", DATA / "bigdev_scaled/scenarios" / b / w) for b, w in SCALED_COLD]
    return out


def jobs() -> list[dict]:
    out = []
    for tag, scen in scenarios():
        res = OUT / f"{tag}__{scen.parent.name}__{scen.name}.npz"
        out.append(memsched.module_job("sb.bigbld_dump", ["--scenario", str(scen), "--start", "0", "--end",
                                                          str(STEPS), "--kwargs", V15_EXTRA, "--out", str(res)],
                                       str(scen), str(res), f"sizegate_{res.stem}"))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def main() -> None:
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    say(f"sizegate starts: {len(plan()[0])} of {len(jobs())} traces to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("sizegate END")


if __name__ == "__main__":
    main()
