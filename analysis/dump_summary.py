"""Summarise a v10 zone trace: heat, reheat, cooling by hour and AHU activity (training scenario)."""
import sys

import numpy as np
import pandas as pd

C_AIR = 1206.0
fn, start = sys.argv[1], sys.argv[2]
d = np.load(fn)
T, q, flow, dis, sat, oat = d["T"], d["q_plan"], d["flow"], d["dis"], d["sat"], d["oat"]
n, nz = T.shape
ts = pd.date_range(start, periods=n, freq="5min")
heat = np.clip(q, 0, None)
cool = np.clip(-q, 0, None)
reheat = dis > np.repeat(sat, [nz // sat.shape[1]] * sat.shape[1], axis=1)[:, :nz] + 0.5 if False else None
print(fn.split("/")[-1], "zones", nz, "mean oat", oat.mean() - 273.15)
print(" mean zone heat kW (sum over zones)", heat.sum(1).mean(), " cooling kW", cool.sum(1).mean())
print(" total flow m3/s mean", flow.sum(1).mean())
df = pd.DataFrame({"h": ts.hour, "wk": ts.dayofweek >= 5, "heat": heat.sum(1), "cool": cool.sum(1),
                   "flow": flow.sum(1), "oat": oat - 273.15, "T": T.mean(1) - 273.15, "Tmin": T.min(1) - 273.15, "Tmax": T.max(1) - 273.15})
print(df[~df.wk].groupby("h").mean().round(2).to_string())
print("weekend")
print(df[df.wk].groupby("h").mean().round(2).iloc[::3].to_string())
