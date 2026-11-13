"""Compare result folders written by sb/run.py.

    python -m sb.compare D:/SmartBuildings_data/results/dev_2880/pid_water D:/.../zonal_v3
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load(folder: Path) -> dict[str, dict]:
    out = {}
    for f in sorted(folder.glob("*.json")):
        r = json.loads(f.read_text())
        out[f.stem] = r
    return out


def main(argv=None) -> None:
    folders = [Path(x) for x in (argv or sys.argv[1:])]
    runs = {f.name: load(f) for f in folders}
    keys = sorted(set().union(*[set(r) for r in runs.values()]))
    names = list(runs)
    print("scenario".ljust(34) + "".join(n[:16].rjust(17) for n in names))
    for k in keys:
        row = k.ljust(34)
        for n in names:
            r = runs[n].get(k)
            row += (f"{r['mean_reward']:.5f}" if r else "-").rjust(17)
        print(row)
    print("-" * (34 + 17 * len(names)))
    for label, fn in (("SCORE (mean |r|)", lambda r: abs(r["mean_reward"])),):
        row = label.ljust(34)
        for n in names:
            vals = [fn(runs[n][k]) for k in keys if k in runs[n]]
            row += (f"{sum(vals) / len(vals):.5f}" if vals else "-").rjust(17)
        print(row)
    for comp, w in (("prod", 0.6), ("energy", 0.2), ("carbon", 0.2)):
        row = f"  {comp} share of loss".ljust(34)
        for n in names:
            rs = [runs[n][k] for k in keys if k in runs[n] and runs[n][k].get("components")]
            if not rs:
                row += "-".rjust(17)
                continue
            tot = sum(abs(r["total_reward"]) for r in rs)
            part = sum(abs(r["components"][comp]) * w for r in rs)
            row += f"{part / tot:.3f}".rjust(17)
        print(row)


if __name__ == "__main__":
    main()
