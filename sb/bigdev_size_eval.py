"""Read the replication of the size test (docs/BIG_BUILDINGS.md, rule of 27 Oct, 12:13): ten pairs on five more
buildings, v14 and pid_water at full size and scaled, first 2880 steps.

    python -m sb.bigdev_size_eval
"""

from __future__ import annotations

import json
from pathlib import Path

from sb.make_bigdev import PAIRS
from sb.make_bigdev_scaled import BUILDINGS

R = Path("D:/SmartBuildings_data/results")
DIRS = {("full", "v14"): R / "bigdev/v14", ("full", "pid"): R / "bigdev/pid_water",
        ("scaled", "v14"): R / "bigdev_scaled/v14", ("scaled", "pid"): R / "bigdev_scaled/pid_water"}


def main() -> None:
    names = [f"{b}__{w}" for b in BUILDINGS for w in PAIRS[b]]
    got = {k: {} for k in DIRS}
    for k, d in DIRS.items():
        for n in names:
            f = d / f"{n}.json"
            if f.exists():
                got[k][n] = abs(json.loads(f.read_text())["mean_reward"])
    done = [n for n in names if all(n in got[k] for k in DIRS)]
    print("| pair | full v14 | full pid_water | ratio | scaled v14 | scaled pid_water | ratio |")
    print("|---|---|---|---|---|---|---|")
    for n in done:
        fv, fp, sv, sp = (got[k][n] for k in DIRS)
        print(f"| {n.replace('building_', '').replace('__', ' ')} | {fv:.5f} | {fp:.5f} | {fv / fp:.3f} | {sv:.5f} | "
              f"{sp:.5f} | {sv / sp:.3f} |")
    if len(done) < len(names):
        print(f"\n{len(done)}/{len(names)} pairs complete")
        return

    def m(k: tuple[str, str], sel: list[str]) -> float:
        return sum(got[k][n] for n in sel) / len(sel)

    rf = m(("full", "v14"), names) / m(("full", "pid"), names)
    rs = m(("scaled", "v14"), names) / m(("scaled", "pid"), names)
    verdict = ("REPLICATED" if rf >= 0.160 and rf >= 1.15 * rs else
               "NOT replicated" if rf <= 1.05 * rs else "unclear")
    print(f"\nratio of means: full {rf:.3f}, scaled {rs:.3f} (x{rf / rs:.2f}) -> {verdict}")
    for label, sel in (("cold", [n for n in names if "jan" in n]), ("hot", [n for n in names if "jul" in n])):
        print(f"{label}: v14 full/scaled x{m(('full', 'v14'), sel) / m(('scaled', 'v14'), sel):.2f}, pid_water "
              f"x{m(('full', 'pid'), sel) / m(('scaled', 'pid'), sel):.2f}; ratio full "
              f"{m(('full', 'v14'), sel) / m(('full', 'pid'), sel):.3f}, scaled "
              f"{m(('scaled', 'v14'), sel) / m(('scaled', 'pid'), sel):.3f}")


if __name__ == "__main__":
    main()
