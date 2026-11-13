"""Scaled counterparts of five full-size development buildings (docs/BIG_BUILDINGS.md, replication of 27 Oct).

Round 1's scaled YAMLs (`heldout/buildings_scaled`, the size of every blind round) in the same stress windows as the
full-size development set (sb/make_bigdev.py), so the size test can be repeated on buildings it has not used. After
generating, gin's path lines are fixed (sb.fix_heldout_paths).

    python -m sb.make_bigdev_scaled --out D:/SmartBuildings_data/bigdev_scaled
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from sb.make_bigdev import PAIRS, STRESS_W

RAW = Path("D:/SmartBuildings_data/heldout/buildings_scaled")
BUILDINGS = ["building_7001", "building_7002", "building_7003", "building_7007", "building_7008"]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from smart_buildings import evaluate

    kit = Path(evaluate.__file__).resolve().parents[1]
    out = Path(a.out).resolve()
    scen = out / "scenarios"
    for b in BUILDINGS:
        cmd = [sys.executable, "-m", "smart_buildings.run_scenario_generator", "--buildings", str(RAW / f"{b}.yaml"),
               "--weathers", *[str(STRESS_W / f"{w}.yaml") for w in PAIRS[b]], "--output-dir", str(scen)]
        r = subprocess.run(cmd, cwd=kit, capture_output=True, text=True)
        print(b, PAIRS[b], "ok" if r.returncode == 0 else r.stderr.strip().splitlines()[-1][:300], flush=True)
    from sb.fix_heldout_paths import main as fix_paths
    fix_paths(str(out))


if __name__ == "__main__":
    main()
