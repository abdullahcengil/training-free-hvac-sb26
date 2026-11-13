"""Full-size held-out set (docs/BIGDEV.md, fixed 25 Oct 21:47 before it was generated): round-2 raw YAMLs unscaled.

Each building in one cold and one hot stress window (2023, from 15 January and 15 July); used only for item 3 of the
v15 full check (v14 against the chosen candidate, 2880 steps). After generating, gin's path lines are fixed.

    python -m sb.make_bigtest --out D:/SmartBuildings_data/bigtest
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAW = Path("D:/SmartBuildings_data/heldout2/buildings")
STRESS_W = Path("D:/SmartBuildings_data/stress/weather")
PAIRS = {
    "building_7111": ["duluth_jan15", "dubai_jul15"],
    "building_7102": ["chicago_jan15", "houston_jul15"],
    "building_7112": ["helena_jan15", "miami_jul15"],
    "building_7104": ["newyork_jan15", "lasvegas_jul15"],
    "building_7105": ["seattle_jan15", "newyork_jul15"],
    "building_7106": ["chicago_jan15", "seattle_jul15"],
}
# The generator's own check rejects some seeds at full size (zones below 20 m2); the next spare takes the slot.
SPARES = ["building_7101", "building_7103", "building_7107", "building_7108", "building_7109", "building_7110"]


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
