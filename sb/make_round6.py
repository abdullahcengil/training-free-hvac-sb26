"""Round 6 (blind, full size, deep cold; docs/PREREGISTRATION_6.md, rules written before this is run): new generator
seeds, raw (unscaled) buildings, each in one deep-cold window that no earlier run used. After generating, gin's path
lines are fixed (sb.fix_heldout_paths), and a manifest of SHA-256 hashes is written.

    python -m sb.make_round6 --out D:/SmartBuildings_data/round6
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

SEEDS = [7601, 7602, 7603, 7604, 7605, 7606]
SPARE_SEEDS = [7607, 7608, 7609, 7610, 7611, 7612, 7613, 7614, 7615]
# Mean outside temperature over the first ten days: Fairbanks -30.6 C (between training windows fairbanks_1 and
# fairbanks_2), Duluth -11.2 C and Chicago -8.2 C (after the windows of the size tests).
WINDOWS = {
    "fairbanks_feb01": ("D:/SmartBuildings_data/starter-kit/smart_buildings/weather/csv/fairbanks.csv", 8.8,
                        "2023-02-01 06:00"),
    "duluth_feb15": ("D:/SmartBuildings_data/stress/weather/csv/duluth.csv", 21.7, "2023-02-15 06:00"),
    "chicago_jan25": ("D:/SmartBuildings_data/stress/weather/csv/chicago.csv", 19.9, "2023-01-25 06:00"),
}
SLOT_WINDOW = ["fairbanks_feb01", "duluth_feb15", "chicago_jan25", "fairbanks_feb01", "duluth_feb15", "chicago_jan25"]


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
