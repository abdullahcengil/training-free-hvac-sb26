"""New buildings in new climates at once, as in the hidden test (docs/HIDLIKE.md).

Each round-5 building (held-out, generated from new seeds) gets four stress-test windows (ten cities no tuning run has
used); the scenario is the round-5 scenario with only its weather lines changed.

    python -m sb.make_hidlike --out D:/SmartBuildings_data/hidlike
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

H5 = Path("D:/SmartBuildings_data/heldout5/scenarios")
STRESS_W = Path("D:/SmartBuildings_data/stress/weather")
WINDOWS = ["chicago_jan15", "helena_jan15", "dubai_jul15", "lasvegas_jul15"]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out) / "scenarios"
    for b in sorted(p for p in H5.iterdir() if p.is_dir()):
        src = sorted(p for p in b.iterdir() if (p / "config.gin").exists())[0]
        for w in WINDOWS:
            y = (STRESS_W / f"{w}.yaml").read_text()
            csv = re.search(r"weather_csv: (.+)", y).group(1).strip()
            conv = re.search(r"convection_coefficient: (.+)", y).group(1).strip()
            start = re.search(r"start_timestamp: (.+)", y).group(1).strip()
            dst = out / b.name / w
            dst.mkdir(parents=True, exist_ok=True)
            for f in ("floor_plan.npy", "zone_map.npy", "config.yaml"):
                shutil.copy2(src / f, dst / f)
            g = (src / "config.gin").read_text()
            g, n1 = re.subn(r"^convection_coefficient = .*$", f"convection_coefficient = {conv}", g, flags=re.M)
            g, n2 = re.subn(r"^weather_csv_path = .*$", f"weather_csv_path = '{csv}'", g, flags=re.M)
            g, n3 = re.subn(r"^start_timestamp = .*$", f"start_timestamp = '{start}'", g, flags=re.M)
            g = g.replace(str(src.as_posix()), dst.as_posix())
            assert n1 == n2 == n3 == 1, (b.name, w)
            (dst / "config.gin").write_text(g)
    print("scenarios in", out)


if __name__ == "__main__":
    main()
