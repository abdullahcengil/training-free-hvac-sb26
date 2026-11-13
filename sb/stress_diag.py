"""Diagnose the stress test's weak spots (docs/STRESS_TEST.md, rule 2): weather of each 30-day window and v13's loss
per degree-hour of heating need, same building across climates (training and stress scenarios).

    python -m sb.stress_diag
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

KIT = Path("D:/SmartBuildings_data/starter-kit")
TRAIN = KIT / "smart_buildings/training_scenarios"
STRESS = Path("D:/SmartBuildings_data/stress/scenarios")
RES = Path("D:/SmartBuildings_data/results")


def weather(scen: Path) -> pd.Series:
    """Hourly outside temperature (C) over the episode's 30 days, labels as the simulator reads them."""
    gin = (scen / "config.gin").read_text()
    csv = re.search(r"weather_csv_path = '([^']+)'", gin).group(1)
    start = pd.Timestamp(re.search(r"start_timestamp = '([^']+)'", gin).group(1))
    path = (KIT / csv) if not Path(csv).is_absolute() else Path(csv)
    df = pd.read_csv(path.resolve())
    t = pd.to_datetime(df["Time"], format="%Y%m%d-%H%M")
    s = pd.Series(df["TempC"].to_numpy(), index=t)
    return s[(s.index >= start) & (s.index < start + pd.Timedelta(days=30))]


def stats(s: pd.Series) -> dict:
    daily = s.resample("D").mean()
    rng = s.resample("D").max() - s.resample("D").min()
    return {"mean": s.mean(), "min": s.min(), "hdh": np.clip(18.0 - s, 0, None).sum(),
            "range": rng.mean(), "sd_daily": daily.std()}


def main() -> None:
    br = json.loads((KIT / "baseline_returns.json").read_text())
    rows = []
    for f in sorted((RES / "dev13_8640/v13_all30").glob("*.json")):
        a = json.loads(f.read_text())
        b, w = a["building"], a["weather"]
        rows.append(("train", b, w, abs(a["mean_reward"]), abs(br[f"{b}/{w}"]["pid_water"]) / 8640, a, TRAIN / b / w))
    for f in sorted((RES / "stress/v13").glob("*.json")):
        a = json.loads(f.read_text())
        b, w = a["building"], a["weather"]
        p = json.loads((RES / "stress/pid_water" / f.name).read_text())
        rows.append(("stress", b, w, abs(a["mean_reward"]), abs(p["mean_reward"]), a, STRESS / b / w))
    out = []
    for kind, b, w, lv, lp, a, scen in rows:
        st = stats(weather(scen))
        c = a["components"]
        ec = 0.2 * (c["energy"] + c["carbon"]) / 8640          # energy + carbon loss per step
        out.append({"set": kind, "building": b[-1], "weather": w, "v13": lv, "pid": lp, "ratio": lv / lp,
                    "ec_per_kdh": ec / max(st["hdh"], 1) * 1e6, **{k: round(v, 1) for k, v in st.items()}})
    df = pd.DataFrame(out)
    pd.set_option("display.width", 200)
    cold = df[df["mean"] < 5].sort_values(["building", "mean"])
    print("Cold windows (mean outside temperature below 5 C), v13 energy+carbon loss per step per 1000 degree-hours:")
    print(cold.to_string(index=False, float_format=lambda x: f"{x:.4f}" if x < 1 else f"{x:.1f}"))
    df.to_csv(Path(__file__).resolve().parents[1] / "analysis" / "stress_weather.csv", index=False)


if __name__ == "__main__":
    main()
