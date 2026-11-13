"""Offline bound (training trace only): with each zone's M2 model (online replay, forgetting 0.998),
how much heat would a just-in-time recovery need on each weekday night, compared with what v10 used?

For every weekday night and zone: start from the zone's state at 19:00, float with no heat (only the
parasitic flow v10 actually gave is ignored), and find the latest start for heating at the recovery cap
that reaches the target at 06:00. Heat is summed in kWh (zone heat, not gas).
"""
import sys

import numpy as np
import pandas as pd

fn, start = sys.argv[1], sys.argv[2]
d = np.load(fn)
T, q, oat = d["T"], d["q_plan"], d["oat"]
n, nz = T.shape
ts = pd.date_range(start, periods=n, freq="5min")
cm = (((ts.hour >= 6) & (ts.hour < 19)) & (ts.dayofweek < 5)).astype(float)
LO = np.array([-0.8, 0.05, -2.0, 0.0, -0.5]); HI = np.array([-0.05, 0.8, 1.5, 0.12, 1.0])
th = np.tile(np.array([-0.33, 0.27, 0.09, 0.016, 0.25]), (nz, 1))
P = np.tile(np.diag([1e-3, 1e-3, 1e-2, 1e-5, 1e-2]), (nz, 1, 1))
tm = T[0].copy(); TM = np.zeros_like(T); TH = np.zeros((n, nz, 5))
for k in range(1, n):
    if k >= 2:
        phi = np.stack([T[k - 1] - tm, q[k - 2], np.ones(nz), oat[k - 1] - T[k - 1], np.full(nz, cm[k - 1])], 1)
        Pphi = np.einsum("nij,nj->ni", P, phi)
        g = Pphi / (0.998 + np.einsum("ni,ni->n", phi, Pphi))[:, None]
        err = np.clip(T[k] - T[k - 1] - np.einsum("ni,ni->n", phi, th), -0.5, 0.5)
        th = np.clip(th + g * err[:, None], LO, HI)
        P = (P - np.einsum("ni,nj->nij", g, Pphi)) / 0.998
        tr = np.trace(P, axis1=1, axis2=2); big = tr > 1
        P[big] *= (1 / tr[big])[:, None, None]
    tm = tm + (T[k - 1] - tm) / 48.0
    TM[k] = tm; TH[k] = th
target = 294.47
cap = 0.2682
res = []
for day in pd.date_range(ts[0].normalize() + pd.Timedelta(days=1), ts[-1].normalize() - pd.Timedelta(days=1), freq="D"):
    if day.dayofweek >= 5 or (day - pd.Timedelta(days=1)).dayofweek >= 5:
        continue   # weekday nights only (Mon-Thu evenings to Tue-Fri mornings)
    k19 = ts.get_loc(day - pd.Timedelta(hours=5))
    k06 = ts.get_loc(day + pd.Timedelta(hours=6))
    used = np.clip(q[k19:k06], 0, None).sum() / 12.0
    thz = TH[k19]
    best = 0.0
    for z in range(nz):
        # latest start s (steps after 19:00) such that heating at the cap from s reaches target at 06:00
        lo_s, hi_s = 0, k06 - k19
        def reach(s):
            t, m, e = T[k19, z], TM[k19, z], 0.0
            for j in range(k06 - k19):
                k = k19 + j
                dis = min(308.15, 0.7 * T[k].mean() + 0.3 * oat[k] + 0.9 * (350 - (0.7 * T[k].mean() + 0.3 * oat[k])))
                qq = cap * 2.0 * max(dis - t, 0) * 1206 / 1000 if j >= s else 0.0
                tn = t + thz[z, 0] * (t - m) + thz[z, 1] * qq + thz[z, 2] + thz[z, 3] * (oat[k] - t)
                m = m + (t - m) / 48.0
                t = tn
                e += qq / 12.0
            return t, e
        while lo_s < hi_s:
            mid = (lo_s + hi_s + 1) // 2
            if reach(mid)[0] >= target:
                lo_s = mid
            else:
                hi_s = mid - 1
        t_end, e = reach(lo_s)
        best += e
    res.append((day.date(), used, best))
r = np.array([(u, b) for _, u, b in res])
for dte, u, b in res:
    print(f"{dte}: v10 night zone heat {u:7.1f} kWh, just-in-time (M2) {b:7.1f} kWh")
print(f"mean: v10 {r[:, 0].mean():.1f} kWh, just-in-time {r[:, 1].mean():.1f} kWh ({100 * (r[:, 1].mean() / r[:, 0].mean() - 1):+.0f} %)")
