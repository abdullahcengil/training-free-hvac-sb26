"""Build the pre-registered held-out set (docs/PREREGISTRATION.md).

Scales the generated buildings to the shipped size range, writes the scenario
configs for the fixed pairing and a manifest of SHA-256 hashes.

    python -m sb.make_heldout --raw D:/SmartBuildings_data/heldout/buildings \
        --out D:/SmartBuildings_data/heldout

Round 2 (docs/PREREGISTRATION_2.md) uses new seeds and the strips below:
the six Minneapolis strips no run has used (a station absent from training)
and six training-period strips that were never used for development.

    python -m sb.make_heldout --round 2 --raw D:/SmartBuildings_data/heldout2/buildings \
        --out D:/SmartBuildings_data/heldout2
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import yaml

SEEDS = [7001, 7002, 7003, 7004, 7005, 7006]
SPARE_SEEDS = [7007, 7008, 7009, 7010, 7011, 7012]
STRIPS = [
    ["atlanta_4", "phoenix_2"],
    ["denver_1", "singapore_2"],
    ["fairbanks_3", "minneapolis_1"],
    ["atlanta_7", "phoenix_7"],
    ["denver_4", "singapore_5"],
    ["fairbanks_6", "minneapolis_5"],
]
SEEDS_2 = [7101, 7102, 7103, 7104, 7105, 7106]
SPARE_SEEDS_2 = [7107, 7108, 7109, 7110, 7111, 7112, 7113, 7114, 7115]
STRIPS_2 = [
    ["minneapolis_2", "atlanta_5"],
    ["minneapolis_3", "denver_3"],
    ["minneapolis_4", "fairbanks_4"],
    ["minneapolis_6", "phoenix_1"],
    ["minneapolis_7", "singapore_3"],
    ["minneapolis_8", "fairbanks_7"],
]
# Round 3 (docs/PREREGISTRATION_3.md): cold-climate test of v9. Every shipped
# strip is used by now, so the cold strips are new 30-day windows in December,
# which no shipped strip covers for these stations (weather/*.yaml in heldout3).
SEEDS_3 = [7201, 7202, 7203, 7204, 7205, 7206]
SPARE_SEEDS_3 = [7207, 7208, 7209, 7210, 7211, 7212, 7213, 7214, 7215]
WEATHER_3 = {  # name: (csv, convection coefficient as in the shipped strips, start)
    "fairbanks_dec": ("csv/fairbanks.csv", 8.8, "2023-12-01 06:00"),
    "minneapolis_dec": ("csv/minneapolis.csv", 21.5, "2023-12-01 06:00"),
    "denver_dec": ("csv/denver.csv", 26.7, "2023-12-01 06:00"),
}
STRIPS_3 = [
    ["fairbanks_dec", "phoenix_5"],
    ["minneapolis_dec", "singapore_6"],
    ["denver_dec", "atlanta_6"],
    ["fairbanks_dec", "phoenix_8"],
    ["minneapolis_dec", "singapore_1"],
    ["denver_dec", "atlanta_3"],
]
# Round 4 (docs/PREREGISTRATION_4.md): warm-climate test of v10. Summer windows at
# Phoenix and Atlanta lie between two shipped strips (new 30-day windows; about 9
# days overlap each neighbour); the other strips were only ever used as test strips
# in rounds 1-3, never for development.
SEEDS_4 = [7301, 7302, 7303, 7304, 7305, 7306]
SPARE_SEEDS_4 = [7307, 7308, 7309, 7310, 7311, 7312, 7313, 7314, 7315]
WEATHER_4 = {
    "phoenix_jun25": ("csv/phoenix.csv", 19.5, "2023-06-25 06:00"),
    "phoenix_aug06": ("csv/phoenix.csv", 19.5, "2023-08-06 06:00"),
    "atlanta_jul30": ("csv/atlanta.csv", 19.1, "2023-07-30 06:00"),
    "fairbanks_dec": ("csv/fairbanks.csv", 8.8, "2023-12-01 06:00"),
    "denver_dec": ("csv/denver.csv", 26.7, "2023-12-01 06:00"),
}
STRIPS_4 = [
    ["phoenix_jun25", "fairbanks_3"],
    ["singapore_2", "minneapolis_1"],
    ["atlanta_jul30", "denver_1"],
    ["phoenix_aug06", "fairbanks_dec"],
    ["singapore_5", "minneapolis_2"],
    ["atlanta_4", "denver_dec"],
]
# Round 5 (docs/PREREGISTRATION_5.md): does the mass-model controller (v11) transfer? New 30-day windows,
# at most 9 days overlap with any window used so far (the shipped strips sit 42 days apart, so every
# 30-day window overlaps one by at least 9 days; singapore_jan01 overlaps none), all six stations.
SEEDS_5 = [7401, 7402, 7403, 7404, 7405, 7406]
SPARE_SEEDS_5 = [7407, 7408, 7409, 7410, 7411, 7412, 7413, 7414, 7415, 7416, 7417, 7418]
WEATHER_5 = {
    "minneapolis_jan29": ("csv/minneapolis.csv", 21.5, "2023-01-29 06:00"),
    "fairbanks_jan22": ("csv/fairbanks.csv", 8.8, "2023-01-22 06:00"),
    "denver_feb05": ("csv/denver.csv", 26.7, "2023-02-05 06:00"),
    "minneapolis_mar12": ("csv/minneapolis.csv", 21.5, "2023-03-12 06:00"),
    "fairbanks_apr16": ("csv/fairbanks.csv", 8.8, "2023-04-16 06:00"),
    "denver_sep03": ("csv/denver.csv", 26.7, "2023-09-03 06:00"),
    "phoenix_may14": ("csv/phoenix.csv", 19.5, "2023-05-14 06:00"),
    "singapore_may21": ("csv/singapore.csv", 17.6, "2023-05-21 06:00"),
    "atlanta_jun18": ("csv/atlanta.csv", 19.1, "2023-06-18 06:00"),
    "singapore_jan01": ("csv/singapore.csv", 17.6, "2023-01-01 06:00"),
    "phoenix_sep17": ("csv/phoenix.csv", 19.5, "2023-09-17 06:00"),
    "atlanta_sep10": ("csv/atlanta.csv", 19.1, "2023-09-10 06:00"),
}
STRIPS_5 = [
    ["minneapolis_jan29", "phoenix_may14"],
    ["fairbanks_jan22", "singapore_may21"],
    ["denver_feb05", "atlanta_jun18"],
    ["minneapolis_mar12", "singapore_jan01"],
    ["fairbanks_apr16", "phoenix_sep17"],
    ["denver_sep03", "atlanta_sep10"],
]
MAX_W, MAX_H = 430, 301


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--round", type=int, default=1, choices=[1, 2, 3, 4, 5])
    a = ap.parse_args(argv)
    seeds, spare_seeds, all_strips = {1: (SEEDS, SPARE_SEEDS, STRIPS),
                                      2: (SEEDS_2, SPARE_SEEDS_2, STRIPS_2),
                                      3: (SEEDS_3, SPARE_SEEDS_3, STRIPS_3),
                                      4: (SEEDS_4, SPARE_SEEDS_4, STRIPS_4),
                                      5: (SEEDS_5, SPARE_SEEDS_5, STRIPS_5)}[a.round]
    raw, out = Path(a.raw).resolve(), Path(a.out).resolve()
    wdir = out / "weather"
    if a.round >= 3:
        wdir.mkdir(parents=True, exist_ok=True)
        for name, (csv, conv, start) in {3: WEATHER_3, 4: WEATHER_4, 5: WEATHER_5}[a.round].items():
            (wdir / f"{name}.yaml").write_text(
                f"name: {name}\nweather_csv: {csv}\nconvection_coefficient: {conv}\n"
                f"start_timestamp: {start}\n")
    bdir = out / "buildings_scaled"
    bdir.mkdir(parents=True, exist_ok=True)
    lines = []
    from smart_buildings import evaluate

    kit = Path(evaluate.__file__).resolve().parents[1]
    scen = out / "scenarios"
    spares = list(spare_seeds)
    for slot, strips in enumerate(all_strips):
        seed = seeds[slot]
        while True:
            src = raw / f"building_{seed}.yaml"
            if not src.exists():
                subprocess.run([sys.executable, "-m", "smart_buildings.run_floor_generator",
                                "--seeds", str(seed), "--no-pdf", "--output-dir", str(raw)],
                               cwd=kit, check=True)
            cfg = yaml.safe_load(src.read_text())
            fp = cfg["floor_plan"]
            s = min(1.0, MAX_W / fp["width"], MAX_H / fp["height"])
            for key in ("width", "height", "min_room_size", "max_room_size"):
                fp[key] = int(round(fp[key] * s))
            dst = bdir / f"building_{seed}.yaml"
            dst.write_text(yaml.safe_dump(cfg, sort_keys=False))
            wx = [str(wdir / f"{w}.yaml") if (wdir / f"{w}.yaml").exists() else w for w in strips]
            cmd = [sys.executable, "-m", "smart_buildings.run_scenario_generator",
                   "--buildings", str(dst), "--weathers", *wx, "--output-dir", str(scen)]
            r = subprocess.run(cmd, cwd=kit, capture_output=True, text=True)
            if r.returncode == 0:
                lines.append(f"{sha(src)}  raw/building_{seed}.yaml")
                lines.append(f"{sha(dst)}  scaled/building_{seed}.yaml  (s={s:.4f}; slot {slot + 1})")
                break
            reason = r.stderr.strip().splitlines()[-1][:200]
            lines.append(f"# seed {seed} rejected by the generator's own check: {reason}")
            dst.unlink()
            import shutil
            shutil.rmtree(scen / f"building_{seed}", ignore_errors=True)
            seed = spares.pop(0)
    if a.round >= 2:
        # Round 1, deviation 1: gin reads backslashes in Windows paths as
        # escapes, so the path lines are fixed before hashing.
        from sb.fix_heldout_paths import main as fix_paths
        fix_paths(str(out))
    for w in sorted(wdir.glob("*.yaml")):
        lines.append(f"{sha(w)}  weather/{w.name}")
    for cfg in sorted(scen.glob("*/*/config.gin")):
        lines.append(f"{sha(cfg)}  scenarios/{cfg.parent.parent.name}/{cfg.parent.name}/config.gin")
    (out / "MANIFEST.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
