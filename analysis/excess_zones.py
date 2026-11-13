"""Which zones exceed the comfort band (too warm) during occupied weekday hours (training trace)."""
import sys

import numpy as np
import pandas as pd

fn, start = sys.argv[1], sys.argv[2]
d = np.load(fn)
T, q, flow, th, hi, occ = d["T"], d["q_plan"], d["flow"], d["theta"], d["hi"], d["occ"]
n, nz = T.shape
ts = pd.date_range(start, periods=n, freq="5min")
occh = ((ts.hour >= 6) & (ts.hour < 19) & (ts.dayofweek < 5))
zn = [str(z) for z in d["zone_names"]]
pz = [str(z).replace("_zone_air_temperature_sensor", "").replace("VAV_", "room_") for z in d["policy_zones"]]
perm = [zn.index(p) for p in pz]
hi_p = hi[:, perm]
ex = np.clip(T - hi_p, 0, None)
rows = []
for z in range(nz):
    m = occh
    rows.append((z, ex[m, z].mean(), (ex[m, z] > 0.5).mean(), flow[m, z].mean() / 2.0, q[m, z].mean(),
                 th[m, z, 0].mean(), th[m, z, 1].mean(), th[m, z, 2].mean(), T[m, z].mean() - 273.15))
print("zone mean_excess frac>0.5 flow/max q_kW -lam g c T")
for r in sorted(rows, key=lambda r: -r[1])[:10]:
    print("%3d  %.3f  %.2f  %.3f  %7.2f  %.3f %.3f %.3f  %.2f" % r)
print("all zones mean excess occupied %.3f" % ex[occh].mean())
df = pd.DataFrame({"h": ts.hour, "wk": ts.dayofweek >= 5, "ex": ex.mean(1), "flowfrac": flow.sum(1) / (2.0 * nz),
                   "sat": d["sat"].mean(1) - 273.15, "oat": d["oat"] - 273.15})
print(df[~df.wk].groupby("h").mean().round(3).to_string())
