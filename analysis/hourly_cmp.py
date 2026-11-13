"""Hour-of-day profile of comfort and energy+carbon for one scenario in several result folders."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

scen = sys.argv[1]
dirs = [Path(x) for x in sys.argv[2:]]
b, w = scen.split("__")
gin = (Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios") / b / w / "config.gin").read_text()
start = gin.split("start_timestamp = '")[1].split("'")[0]
out = {}
for d in dirs:
    a = np.load(d / f"{scen}.npy")
    ts = pd.date_range(start, periods=len(a), freq="5min")
    df = pd.DataFrame({"h": ts.hour, "wk": ts.dayofweek >= 5, "comfort": -0.6 * a[:, 1], "ec": 0.2 * (a[:, 2] + a[:, 3])})
    wd = df[~df.wk].groupby("h")[["comfort", "ec"]].mean()
    out[d.name] = wd
    print(f"{d.name}: weekday comfort {df[~df.wk].comfort.mean():.5f}  e+c {df[~df.wk].ec.mean():.5f};  weekend e+c {df[df.wk].ec.mean():.5f}")
names = list(out)
tab = pd.concat({n: out[n] for n in names}, axis=1).round(5)
print(tab.to_string())
