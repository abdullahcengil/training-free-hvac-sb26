"""One scheduler for the night of 30 Oct, in order: the empty-holiday screen (docs/HOLIDAY.md), round 6 (blind, full
size; docs/PREREGISTRATION_6.md), the full-length holiday check on the 70 development windows, the v16 screen (docs/HOLIDAY.md), then the
full-size sensitivity sweep (docs/FULLSWEEP.md). Restartable; adopts runs started by an earlier scheduler.

    python -m sb.run_night >> D:/SmartBuildings_data/fullsweep.log 2>&1
"""

from __future__ import annotations

import time

from pathlib import Path

from sb import memsched, run_fullsweep, run_holiday, run_round6h

REPO = Path(__file__).resolve().parents[1]
NB_SCEN = "D:/SmartBuildings_data/stress/scenarios/building_train_7/duluth_jan15"   # first work day is a holiday
NB_RESULT = "D:/SmartBuildings_data/nbcheck_v15.txt"
NB_JOB = memsched.module_job(
    "sb.nbcheck_job",
    ["--result", NB_RESULT, "--", "--notebook", str(REPO / "submission/zonal_v15_submission.ipynb"),
     "--policy", "D:/SmartBuildings_data/frozen/zonal_v14f.py", "--params", str(REPO / "submission/V15_PARAMS.json"),
     "--scenario", NB_SCEN, "--steps", "576"],
    NB_SCEN, NB_RESULT, "nbcheck_v15")


def plan() -> tuple[list[dict], list[dict]]:
    nb = [] if Path(NB_RESULT).exists() else [NB_JOB]
    return (nb + run_holiday.plan()[0] + run_round6h.plan()[0] + run_holiday.full_plan()[0]
            + run_holiday.v16_plan()[0] + run_fullsweep.plan()[0], [])


def main() -> None:
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"night scheduler starts: {len(plan()[0])} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("night scheduler END")
    run_holiday.read()
    run_round6h.read()
    run_holiday.read_full()
    run_holiday.read_v16()
    run_fullsweep.read()


if __name__ == "__main__":
    main()
