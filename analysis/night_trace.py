"""Print one zone's trajectory through selected nights (training trace)."""
import sys

import numpy as np
import pandas as pd

fn, start, z = sys.argv[1], sys.argv[2], int(sys.argv[3])
days = sys.argv[4].split(",")
d = np.load(fn)
T, q, flow, lo_env, th = d["T"], d["q_plan"], d["flow"], d["lo"], d["theta"]
oat = d["oat"]
ts = pd.date_range(start, periods=len(T), freq="5min")
for day in days:
    m = (ts >= pd.Timestamp(day) - pd.Timedelta(hours=6)) & (ts < pd.Timestamp(day) + pd.Timedelta(hours=9))
    idx = np.where(m)[0][::3]
    print(f"--- zone {z}, night before {day}")
    for k in idx:
        print(f"{ts[k]:%a %H:%M}  T {T[k, z] - 273.15:6.2f}  q {q[k, z]:6.2f} kW  flow/max {flow[k, z] / 2:.3f}  "
              f"-lam {th[k, z, 0]:.3f} g {th[k, z, 1]:.3f} c {th[k, z, 2]:.3f}  oat {oat[k] - 273.15:6.1f}")
