"""Offline least-squares M2 coefficients per zone (training traces only), to set priors and bounds."""
import sys

import numpy as np
import pandas as pd

N = 48
for fn, start in [("building_train_1_fairbanks_1", "2023-01-01 06:00"), ("building_train_4_denver_2", "2023-02-26 06:00"),
                  ("building_train_8_phoenix_4", "2023-06-04 06:00"), ("building_train_8_singapore_7", "2023-10-15 06:00")]:
    d = np.load(f"D:/SmartBuildings_data/results/zdump_v10/{fn}.npz")
    T, q, oat = d["T"], d["q_plan"], d["oat"]
    n, nz = T.shape
    ts = pd.date_range(start, periods=n, freq="5min")
    cm = (((ts.hour >= 6) & (ts.hour < 19)) & (ts.dayofweek < 5)).astype(float)
    k = np.arange(290, n - 1)
    coefs = []
    for z in range(nz):
        Tz = T[:, z]
        Tm = np.empty(n); Tm[0] = Tz[0]
        for j in range(1, n):
            Tm[j] = Tm[j - 1] + (Tz[j - 1] - Tm[j - 1]) / N
        X = np.stack([Tz[k] - Tm[k], q[k - 1, z], np.ones(len(k)), oat[k] - Tz[k], cm[k]], 1)
        th, *_ = np.linalg.lstsq(X, Tz[k + 1] - Tz[k], rcond=None)
        coefs.append(th)
    c = np.array(coefs)
    pct = lambda j: " ".join(f"{v:7.4f}" for v in np.percentile(c[:, j], [5, 25, 50, 75, 95]))
    print(fn)
    for j, name in enumerate(["-lam", "g", "c", "b", "c_cm"]):
        print(f"   {name:5s} p5..p95: {pct(j)}")
