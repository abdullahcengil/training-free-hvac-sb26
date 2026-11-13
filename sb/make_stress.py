"""Climate stress test: the six training buildings in ten climates no run has used (docs/STRESS_TEST.md).

The hidden test set uses five weather stations that appear nowhere in training (organisers' paper, arXiv
2610.18511). This builds scenarios from hourly 2023 weather for ten other cities (Open-Meteo archive, ERA5,
downloaded once as raw JSON into <root>/download), in the shipped format: local standard time, labels read by
the simulator as given, one convection coefficient per station. Two 30-day windows per city (from 15 January and
from 15 July, 06:00), each with two of the six training buildings.

    python -m sb.make_stress --root D:/SmartBuildings_data/stress
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LOCATION = {
    "miami": "Miami, USA", "houston": "Houston, USA", "lasvegas": "Las Vegas, USA",
    "sanfrancisco": "San Francisco, USA", "newyork": "New York, USA", "seattle": "Seattle, USA",
    "chicago": "Chicago, USA", "helena": "Helena, USA", "duluth": "Duluth, USA", "dubai": "Dubai, ARE",
}
WINDOWS = {"jan15": "2023-01-15 06:00", "jul15": "2023-07-15 06:00"}
BUILDINGS = ["building_train_1", "building_train_2", "building_train_4", "building_train_5", "building_train_7",
             "building_train_8"]
# Convection coefficient against the station's annual mean wind (m/s), least squares over the six shipped
# stations (atlanta 19.1 at 3.54, denver 26.7 at 4.45, fairbanks 8.8 at 1.74, phoenix 19.5 at 2.90, singapore 17.6
# at 2.56, minneapolis 21.5 at 4.14), clipped to the shipped range.
SHIPPED = [(3.54, 19.1), (4.45, 26.7), (1.74, 8.8), (2.90, 19.5), (2.56, 17.6), (4.14, 21.5)]


def convection(v: float) -> float:
    x, y = np.array(SHIPPED).T
    b, a = np.polyfit(x, y, 1)
    return float(np.clip(a + b * v, 8.8, 26.7))


def to_csv(raw: Path, out: Path) -> float:
    """Raw Open-Meteo JSON (UTC) -> shipped CSV (local standard time, 2023); returns the mean wind in m/s."""
    d = json.loads(raw.read_text())
    m = d["_meta"]
    h = d["hourly"]
    t = pd.to_datetime(h["time"]) + pd.Timedelta(hours=m["std_utc_offset_h"])
    df = pd.DataFrame({"t": t, "TempC": h["temperature_2m"], "DewPointC": h["dew_point_2m"],
                       "WindspeedKmph": h["wind_speed_10m"], "Humidity": h["relative_humidity_2m"]})
    df = df[(df.t >= "2023-01-01") & (df.t < "2024-01-01")].reset_index(drop=True)
    assert len(df) == 8760 and df[["TempC", "DewPointC", "WindspeedKmph", "Humidity"]].notna().all().all(), raw
    station = m["name"]
    out_df = pd.DataFrame({
        "Time": df.t.dt.strftime("%Y%m%d-%H%M"), "StationName": f"{station}-OpenMeteo-ERA5",
        "Location": f"{station}-OpenMeteo-ERA5, {LOCATION[station]}", "TempC": df.TempC.round(1),
        "DewPointC": df.DewPointC.round(1), "WindspeedKmph": df.WindspeedKmph.round(2),
        "Humidity": df.Humidity.round(0), "TempF": df.TempC * 9 / 5 + 32})
    out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out)
    return float(df.WindspeedKmph.mean() / 3.6)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    wdir = root / "weather"
    strips = []
    for raw in sorted((root / "download").glob("*.json")):
        city = raw.stem
        csv = wdir / "csv" / f"{city}.csv"
        v = to_csv(raw, csv)
        h = convection(v)
        for tag, start in WINDOWS.items():
            name = f"{city}_{tag}"
            (wdir / f"{name}.yaml").write_text(f"name: {name}\nweather_csv: {csv.as_posix()}\n"
                                               f"convection_coefficient: {h:.1f}\nstart_timestamp: {start}\n")
            strips.append(name)
        print(f"{city}: mean wind {v:.2f} m/s, convection {h:.1f}")
    # Two buildings per strip, round robin, so each building meets cold and warm strips.
    plan = {b: [] for b in BUILDINGS}
    for i, s in enumerate(strips):
        for j in (0, 3):
            plan[BUILDINGS[(i + j) % len(BUILDINGS)]].append(s)
    from smart_buildings import evaluate
    kit = Path(evaluate.__file__).resolve().parents[1]
    scen = root / "scenarios"
    for b, ws in plan.items():
        subprocess.run([sys.executable, "-m", "smart_buildings.run_scenario_generator", "--buildings", b,
                        "--weathers", *[str(wdir / f"{w}.yaml") for w in ws], "--output-dir", str(scen)],
                       cwd=kit, check=True)
    (root / "PLAN.json").write_text(json.dumps(plan, indent=1))
    print(sum(len(v) for v in plan.values()), "scenarios in", scen)


if __name__ == "__main__":
    main()
