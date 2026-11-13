"""Loss by time block and station from per-step component files (training runs only)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(sys.argv[1])
blocks = [("night 00-06", 0, 6), ("06-09", 6, 9), ("09-13", 9, 13), ("13-17", 13, 17), ("17-19", 17, 19), ("19-24", 19, 24)]
tab = {}
for f in sorted(root.glob("*.npy")):
    j = json.loads(f.with_suffix(".json").read_text())
    st = j["weather"].split("_")[0]
    gin = (Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios") / j["building"] / j["weather"] / "config.gin").read_text()
    start = gin.split("start_timestamp = '")[1].split("'")[0]
    a = np.load(f)
    ts = pd.date_range(start, periods=len(a), freq="5min")
    comfort = -0.6 * a[:, 1]
    energy = 0.2 * (a[:, 2] + a[:, 3])
    wk = ts.dayofweek >= 5
    row = tab.setdefault(st, {})
    for name, h0, h1 in blocks:
        m = (~wk) & (ts.hour >= h0) & (ts.hour < h1)
        row.setdefault(name, [0, 0])
        row[name][0] += comfort[m].sum() / len(a)
        row[name][1] += energy[m].sum() / len(a)
    m = wk
    row.setdefault("weekend", [0, 0])
    row["weekend"][0] += comfort[m].sum() / len(a)
    row["weekend"][1] += energy[m].sum() / len(a)
    row.setdefault("n", [0, 0])
    row["n"][0] += 1
for st, row in tab.items():
    n = row["n"][0]
    tot = sum(v[0] + v[1] for k, v in row.items() if k != "n") / n
    print(f"{st} (n={n}) mean {tot:.5f}")
    for k, v in row.items():
        if k == "n":
            continue
        print(f"   {k:12s} comfort {v[0] / n:.5f}  energy+carbon {v[1] / n:.5f}  share {100 * (v[0] + v[1]) / n / tot:5.1f}%")
