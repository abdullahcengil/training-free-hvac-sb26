"""Full-size development set (docs/BIG_BUILDINGS.md): generated buildings at the generator's own size, new climates.

Every blind round scaled its buildings to the shipped size (sb/make_heldout.py); the hidden buildings look full size
(docs/BIG_BUILDINGS.md). This set uses the raw round-1 YAMLs unscaled, each in one cold and one hot stress window
(stress cities, 2023, from 15 January and 15 July). Round 1 was opened on 17 Oct, so these buildings are spent as a
test and free for development. After generating, gin's path lines are fixed (sb.fix_heldout_paths).

    python -m sb.make_bigdev --out D:/SmartBuildings_data/bigdev
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAW = Path("D:/SmartBuildings_data/heldout/buildings")
STRESS_W = Path("D:/SmartBuildings_data/stress/weather")
PAIRS = {
    "building_7001": ["chicago_jan15", "dubai_jul15"],
    "building_7002": ["helena_jan15", "lasvegas_jul15"],
    "building_7003": ["duluth_jan15", "houston_jul15"],
    "building_7007": ["newyork_jan15", "miami_jul15"],
    "building_7008": ["seattle_jan15", "chicago_jul15"],
    "building_7009": ["chicago_jan15", "lasvegas_jul15"],
}
# The generator's own check rejects some seeds at full size (zones below 20 m2); the next spare takes the slot.
SPARES = ["building_7004", "building_7005", "building_7006"]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args(argv)
    from smart_buildings import evaluate

    kit = Path(evaluate.__file__).resolve().parents[1]
    out = Path(a.out).resolve()
    scen = out / "scenarios"
    spares = list(SPARES)
    for b, ws in PAIRS.items():
        if a.only and b not in a.only:
            continue
        while True:
            cmd = [sys.executable, "-m", "smart_buildings.run_scenario_generator", "--buildings",
                   str(RAW / f"{b}.yaml"), "--weathers", *[str(STRESS_W / f"{w}.yaml") for w in ws],
                   "--output-dir", str(scen)]
            r = subprocess.run(cmd, cwd=kit, capture_output=True, text=True)
            print(b, ws, "ok" if r.returncode == 0 else r.stderr.strip().splitlines()[-1][:300], flush=True)
            if r.returncode == 0 or not spares:
                break
            b = spares.pop(0)
    from sb.fix_heldout_paths import main as fix_paths
    fix_paths(str(out))


if __name__ == "__main__":
    main()
