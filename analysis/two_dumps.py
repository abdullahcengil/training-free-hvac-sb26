"""Compare two zone traces of the same scenario by weekday hour: mean zone temperature, excess above the
band, total flow, cooling, and the model parameters (training scenario)."""
import sys

import numpy as np
import pandas as pd

fa, fb, start = sys.argv[1], sys.argv[2], sys.argv[3]
res = {}
for name, fn in (("A", fa), ("B", fb)):
    d = np.load(fn)
    T, q, flow, th, hi = d["T"], d["q_plan"], d["flow"], d["theta"], d["hi"]
    n, nz = T.shape
    ts = pd.date_range(start, periods=n, freq="5min")
    zn = [str(z) for z in d["zone_names"]]
    pz = [str(z).replace("_zone_air_temperature_sensor", "").replace("VAV_", "room_") for z in d["policy_zones"]]
    perm = [zn.index(p) for p in pz]
    ex = np.clip(T - hi[:, perm], 0, None)
    df = pd.DataFrame({"h": ts.hour, "wk": ts.dayofweek >= 5, "T": T.mean(1) - 273.15, "Tmax": T.max(1) - 273.15,
                       "ex": ex.mean(1), "flow": flow.sum(1), "cool": np.clip(-q, 0, None).sum(1),
                       "lam": -th[:, :, 0].mean(1), "g": th[:, :, 1].mean(1), "c": th[:, :, 2].mean(1)})
    res[name] = df[~df.wk].groupby("h").mean()
tab = pd.concat(res, axis=1).round(3)
print(tab.to_string())
