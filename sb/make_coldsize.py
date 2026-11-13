"""Deep-cold size test (docs/BIG_BUILDINGS.md, rule of 29 Oct): the eight size-test buildings at full size and scaled,
in two deep-cold windows that no earlier run used. The size test's January windows were mild (mean outside temperature
-4.5 to +4.1 C), so it never saw full-size buildings in deep cold. After generating, gin's path lines are fixed
(sb.fix_heldout_paths).

    python -m sb.make_coldsize --out D:/SmartBuildings_data/coldsize
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# building -> folder with its raw (full-size) and scaled YAMLs; the same eight buildings as both size tests
BUILDINGS = {
    "building_7402": "heldout5", "building_7407": "heldout5", "building_7408": "heldout5",
    "building_7001": "heldout", "building_7002": "heldout", "building_7003": "heldout",
    "building_7007": "heldout", "building_7008": "heldout",
}
# Mean outside temperature over the first ten days: Fairbanks -21.8 C (starts when training window fairbanks_8 ends),
# Duluth -17.7 C (starts when the size test's duluth_jan15 window ends). Both leave 30 days inside the 2023 file.
WINDOWS = {
    "fairbanks_nov21": ("D:/SmartBuildings_data/starter-kit/smart_buildings/weather/csv/fairbanks.csv", 8.8,
                        "2023-11-21 06:00"),
    "duluth_jan25": ("D:/SmartBuildings_data/stress/weather/csv/duluth.csv", 21.7, "2023-01-25 06:00"),
}
SIZES = {"full": "buildings", "scaled": "buildings_scaled"}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from smart_buildings import evaluate

    kit = Path(evaluate.__file__).resolve().parents[1]
    out = Path(a.out).resolve()
    wdir = out / "weather"
    wdir.mkdir(parents=True, exist_ok=True)
    for name, (csv, conv, start) in WINDOWS.items():
        (wdir / f"{name}.yaml").write_text(f"name: {name}\nweather_csv: {csv}\nconvection_coefficient: {conv}\n"
                                           f"start_timestamp: {start}\n", encoding="utf-8")
    for size, sub in SIZES.items():
        scen = out / size / "scenarios"
        for b, src in BUILDINGS.items():
            yml = Path("D:/SmartBuildings_data") / src / sub / f"{b}.yaml"
            cmd = [sys.executable, "-m", "smart_buildings.run_scenario_generator", "--buildings", str(yml),
                   "--weathers", *[str(wdir / f"{w}.yaml") for w in WINDOWS], "--output-dir", str(scen)]
            r = subprocess.run(cmd, cwd=kit, capture_output=True, text=True)
            print(size, b, "ok" if r.returncode == 0 else r.stderr.strip().splitlines()[-1][:300], flush=True)
        from sb.fix_heldout_paths import main as fix_paths
        fix_paths(str(out / size))


if __name__ == "__main__":
    main()
