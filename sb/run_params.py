"""What the controller learns about each zone (docs/PARAMS.md): v15's five per-zone numbers after one week, on the six
shipped training buildings (one cold window each) and the six full-size buildings of round 7 (their round-7
windows). Restartable (sb.memsched); start it after the round-7 and pid_water jobs.

    python -m sb.run_params >> D:/SmartBuildings_data/params.log 2>&1
"""

from __future__ import annotations

import time
from pathlib import Path

from sb import memsched

DATA = Path("D:/SmartBuildings_data")
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
OUT = DATA / "results/params/v15"
STEPS = 2016
SCENARIOS = [TRAIN / s for s in ("building_train_1/fairbanks_1", "building_train_2/fairbanks_2",
                                 "building_train_4/denver_2", "building_train_5/denver_3",
                                 "building_train_7/fairbanks_7", "building_train_8/fairbanks_8")]
SCENARIOS += sorted(c.parent for c in (DATA / "round7/scenarios").glob("*/*/config.gin"))


def jobs() -> list[dict]:
    out = []
    for s in SCENARIOS:
        res = OUT / f"{s.parent.name}__{s.name}.json"
        out.append(memsched.module_job("sb.param_dump", ["--scenario", str(s), "--steps", str(STEPS), "--out", str(res)],
                                       str(s), str(res), f"params_{s.parent.name}__{s.name}"))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def main() -> None:
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"params starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("params END")


if __name__ == "__main__":
    main()
