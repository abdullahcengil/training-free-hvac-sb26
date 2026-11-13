"""Which zones miss the comfort band during occupied weekday hours, and why (training trace)."""
import sys

import numpy as np
import pandas as pd

fn, start = sys.argv[1], sys.argv[2]
d = np.load(fn)
T, q, flow, dis, th, lo, occ = d["T"], d["q_plan"], d["flow"], d["dis"], d["theta"], d["lo"], d["occ"]
n, nz = T.shape
ts = pd.date_range(start, periods=n, freq="5min")
occh = ((ts.hour >= 6) & (ts.hour < 19) & (ts.dayofweek < 5))
# zone order in lo/occ is the env's zone order; T is the policy order: map by name
zn = [str(z) for z in d["zone_names"]]
pz = [str(z).replace("_zone_air_temperature_sensor", "").replace("VAV_", "room_") for z in d["policy_zones"]]
perm = [zn.index(p) if p in zn else -1 for p in pz]
lo_p = lo[:, perm]
occ_p = occ[:, perm]
deficit = np.clip(lo_p - T, 0, None)
w = occ_p > 0
print("zone  mean_def_occ  frac_steps_def>0.5  occ_weighted_def  flow/max  q_kW  -lam  g  c  T_occ")
rows = []
for z in range(nz):
    m = occh
    rows.append((z, deficit[m, z].mean(), (deficit[m, z] > 0.5).mean(), (deficit[:, z] * occ_p[:, z]).sum() / max(occ_p[:, z].sum(), 1e-9),
                 flow[m, z].mean() / 2.0, q[m, z].mean(), th[m, z, 0].mean(), th[m, z, 1].mean(), th[m, z, 2].mean(), T[m, z].mean() - 273.15))
for r in sorted(rows, key=lambda r: -r[1])[:14]:
    print("%3d  %.3f  %.2f  %.3f  %.3f  %6.2f  %.3f %.3f %.3f  %.2f" % r)
print("all zones: mean deficit occupied %.3f" % deficit[occh].mean())
# hour profile of deficits for the worst zones
worst = [r[0] for r in sorted(rows, key=lambda r: -r[1])[:8]]
df = pd.DataFrame({"h": ts.hour, "wk": ts.dayofweek >= 5})
for z in worst:
    df[f"z{z}"] = deficit[:, z]
print(df[~df.wk].groupby("h").mean().round(2).iloc[5:20].to_string())
