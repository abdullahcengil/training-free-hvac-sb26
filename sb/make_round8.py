"""Round 8 (blind, full size; docs/PREREGISTRATION_8.md, rules written and stamped before this is run): new generator
seeds, raw (unscaled) buildings, each in one cold or mild window that no earlier run used. After generating, gin's path
lines are fixed (sb.fix_heldout_paths), and a manifest of SHA-256 hashes is written. Same procedure as sb/make_round7.py;
only the seeds and the windows differ (fixed 31 Oct 13:03 by `date`, before any result of the heating-net screen).

    python -m sb.make_round8 --out D:/SmartBuildings_data/round8
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

SEEDS = [7901, 7902, 7903, 7904, 7905, 7906]
SPARE_SEEDS = [7907, 7908, 7909, 7910, 7911, 7912, 7913, 7914, 7915]
# One window per building, each from a Sunday 06:00, ten days, from deep cold to mild (2023 ERA5 data of the stress
# set; convection coefficients as in sb/make_round7.py); none used before at any size. Ten-day means and minima of the
# outside temperature (computed 31 Oct from the csv files) in the comments; chicago_jan08 holds Martin Luther King Day
# (Mon 16 Jan) and newyork_feb12 Presidents' Day (Mon 20 Feb).
ST = "D:/SmartBuildings_data/stress/weather/csv"
WINDOWS = {
    "duluth_jan29": (f"{ST}/duluth.csv", 21.7, "2023-01-29 06:00"),              # -14.8 C (min -29.4)
    "helena_dec10": (f"{ST}/helena.csv", 13.3, "2023-12-10 06:00"),              # -0.4 C (min -6.7)
    "chicago_jan08": (f"{ST}/chicago.csv", 19.9, "2023-01-08 06:00"),            # 1.6 C (min -6.9)
    "newyork_feb12": (f"{ST}/newyork.csv", 22.9, "2023-02-12 06:00"),            # 6.8 C (min -2.8)
    "seattle_dec10": (f"{ST}/seattle.csv", 17.5, "2023-12-10 06:00"),            # 6.0 C (min 0.6)
    "sanfrancisco_feb05": (f"{ST}/sanfrancisco.csv", 19.8, "2023-02-05 06:00"),  # 9.3 C (min 3.9)
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
