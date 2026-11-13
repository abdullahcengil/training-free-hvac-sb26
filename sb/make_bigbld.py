"""Full-size (unscaled) round-5 buildings in stress windows (docs/BIG_BUILDINGS.md).

    python -m sb.make_bigbld --out D:/SmartBuildings_data/bigbld
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAW = Path("D:/SmartBuildings_data/heldout5/buildings")
STRESS_W = Path("D:/SmartBuildings_data/stress/weather")
BUILDINGS = ["building_7402", "building_7407", "building_7408"]
WINDOWS = ["chicago_jan15", "dubai_jul15"]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from smart_buildings import evaluate

    kit = Path(evaluate.__file__).resolve().parents[1]
    scen = Path(a.out) / "scenarios"
    for b in BUILDINGS:
        cmd = [sys.executable, "-m", "smart_buildings.run_scenario_generator", "--buildings", str(RAW / f"{b}.yaml"),
               "--weathers", *[str(STRESS_W / f"{w}.yaml") for w in WINDOWS], "--output-dir", str(scen)]
        r = subprocess.run(cmd, cwd=kit, capture_output=True, text=True)
        print(b, "ok" if r.returncode == 0 else r.stderr.strip().splitlines()[-1][:300])


if __name__ == "__main__":
    main()
