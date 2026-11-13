"""Round 6 (blind, full size, holidays; docs/PREREGISTRATION_6.md, rules written before this is run): new generator
seeds, raw (unscaled) buildings, each in one window that holds a weekday US federal holiday and that no earlier run used. After generating, gin's path
lines are fixed (sb.fix_heldout_paths), and a manifest of SHA-256 hashes is written.

    python -m sb.make_round6h --out D:/SmartBuildings_data/round6h
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

SEEDS = [7701, 7702, 7703, 7704, 7705, 7706]
SPARE_SEEDS = [7707, 7708, 7709, 7710, 7711, 7712, 7713, 7714, 7715]
# One window per building, each from a Sunday 06:00 (Chicago: Sunday before Thanksgiving), ten days, holding one
# weekday US federal holiday of 2023 and a work day after it; stations of the stress set, windows never used before.
ST = "D:/SmartBuildings_data/stress/weather/csv"
WINDOWS = {
    "houston_may28": (f"{ST}/houston.csv", 18.3, "2023-05-28 06:00"),     # Memorial Day, Monday 29 May
    "miami_jul02": (f"{ST}/miami.csv", 17.5, "2023-07-02 06:00"),         # Independence Day, Tuesday 4 July
    "dubai_sep03": (f"{ST}/dubai.csv", 22.3, "2023-09-03 06:00"),         # Labor Day, Monday 4 September
    "newyork_oct08": (f"{ST}/newyork.csv", 22.9, "2023-10-08 06:00"),     # Columbus Day, Monday 9 October
    "chicago_nov19": (f"{ST}/chicago.csv", 19.9, "2023-11-19 06:00"),     # Thanksgiving, Thursday 23 November
    "duluth_dec17": (f"{ST}/duluth.csv", 21.7, "2023-12-17 06:00"),       # Christmas, Monday 25 December
}
SLOT_WINDOW = list(WINDOWS)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from smart_buildings import evaluate

    kit = Path(evaluate.__file__).resolve().parents[1]
    out = Path(a.out).resolve()
    raw, wdir, scen = out / "buildings", out / "weather", out / "scenarios"
    for d in (raw, wdir, scen):
        d.mkdir(parents=True, exist_ok=True)
    for name, (csv, conv, start) in WINDOWS.items():
        (wdir / f"{name}.yaml").write_text(f"name: {name}\nweather_csv: {csv}\nconvection_coefficient: {conv}\n"
                                           f"start_timestamp: {start}\n", encoding="utf-8")
    spares = list(SPARE_SEEDS)
    lines = []
    for slot, w in enumerate(SLOT_WINDOW):
        seed = SEEDS[slot]
        while True:
            src = raw / f"building_{seed}.yaml"
            if not src.exists():
                subprocess.run([sys.executable, "-m", "smart_buildings.run_floor_generator", "--seeds", str(seed),
                                "--no-pdf", "--output-dir", str(raw)], cwd=kit, capture_output=True, text=True)
            r = subprocess.run([sys.executable, "-m", "smart_buildings.run_scenario_generator", "--buildings", str(src),
                                "--weathers", str(wdir / f"{w}.yaml"), "--output-dir", str(scen)],
                               cwd=kit, capture_output=True, text=True)
            if r.returncode == 0:
                lines.append(f"{sha(src)}  buildings/building_{seed}.yaml  (slot {slot + 1}, {w})")
                print(f"slot {slot + 1}: building_{seed} in {w} ok", flush=True)
                break
            reason = (r.stderr.strip().splitlines() or ["?"])[-1][:200]
            lines.append(f"# seed {seed} rejected by the generator's own check: {reason}")
            print(f"slot {slot + 1}: building_{seed} rejected ({reason}); next spare", flush=True)
            seed = spares.pop(0)
    from sb.fix_heldout_paths import main as fix_paths

    fix_paths(str(out))
    for cfg in sorted(scen.glob("*/*/config.gin")):
        lines.append(f"{sha(cfg)}  {cfg.relative_to(out).as_posix()}")
    (out / "MANIFEST.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
