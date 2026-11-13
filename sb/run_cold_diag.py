"""Deep-cold diagnosis traces (docs/BIG_BUILDINGS.md; description only): v14 on three deep-cold scenarios of the
deep-cold size test at full size and scaled, first 2016 steps, with sb.bigbld_dump. Waits for the size test to end
(its runs and these share the three simulation slots). Restartable: finished traces are skipped (sb.memsched).

    python -m sb.run_cold_diag >> D:/SmartBuildings_data/cold_diag.log 2>&1
    python -m sb.cold_diag_read D:/SmartBuildings_data/results/coldsize_diag/*.npz
"""

from __future__ import annotations

import time
from pathlib import Path

from sb import memsched

DATA = Path("D:/SmartBuildings_data")
OUT = DATA / "results/coldsize_diag"
PICK = [("building_7407", "fairbanks_nov21"), ("building_7408", "fairbanks_nov21"), ("building_7001", "duluth_jan25")]
STEPS = 2016


def jobs() -> list[dict]:
    out = []
    for b, w in PICK:
        for size in ("full", "scaled"):
            scen = DATA / "coldsize" / size / "scenarios" / b / w
            res = OUT / f"v14_{b[-4:]}_{w}_{size}.npz"
            out.append(memsched.module_job("sb.bigbld_dump", ["--scenario", str(scen), "--start", "0", "--end",
                                                              str(STEPS), "--out", str(res)],
                                           str(scen), str(res), f"colddiag_{b[-4:]}_{w}_{size}"))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def main() -> None:
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    log = DATA / "coldsize.log"
    while "coldsize END" not in (log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""):
        time.sleep(60)
    OUT.mkdir(parents=True, exist_ok=True)
    say(f"cold_diag starts: {len(plan()[0])} of {len(jobs())} traces to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("cold_diag END")


if __name__ == "__main__":
    main()
