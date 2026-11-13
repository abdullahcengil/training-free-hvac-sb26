"""Offline check (training traces only): does a second-order zone model predict hours ahead
much better than the first-order one the controller uses?

Per zone, least squares on days 1-20 of a 30-day v10 trace, multi-step open-loop prediction
(given the heat actually planned) on days 21-29.

    python analysis/arx_offline.py D:/SmartBuildings_data/results/zdump_v10/<trace>.npz <start>
"""
import sys

import numpy as np
import pandas as pd

fn, start = sys.argv[1], sys.argv[2]
d = np.load(fn)
T, q, oat = d["T"], d["q_plan"] , d["oat"]
n, nz = T.shape
ts = pd.date_range(start, periods=n, freq="5min")
cm = (((ts.hour >= 6) & (ts.hour < 19)) & (ts.dayofweek < 5)).astype(float)
train = slice(288, 288 * 21)
test0, test1 = 288 * 21, n - 80


def design(order, z, k):
    """Regressors for predicting T[k+1]."""
    row = [T[k - i, z] for i in range(order)]
    row += [q[k - 1 - i, z] for i in range(order)]
    row += [oat[k], cm[k], 1.0]
    return row


def fit(order, z):
    ks = np.arange(train.start + 4, train.stop - 1)
    X = np.array([design(order, z, k) for k in ks])
    y = T[ks + 1, z]
    th, *_ = np.linalg.lstsq(X, y, rcond=None)
    return th


def predict(order, th, z, k0, h):
    """Open-loop h-step prediction from k0, using true q, oat, cm."""
    Tp = list(T[k0 - order + 1:k0 + 1, z])  # history
    for j in range(h):
        k = k0 + j
        row = Tp[::-1][:order] + [q[k - 1 - i, z] for i in range(order)] + [oat[k], cm[k], 1.0]
        Tp.append(float(np.dot(th, row)))
    return Tp[-1]


res = {}
for order in (1, 2, 3):
    errs = {h: [] for h in (1, 12, 36, 72)}
    for z in range(nz):
        th = fit(order, z)
        for k0 in range(test0, test1, 7):
            for h in errs:
                if k0 + h < n:
                    errs[h].append(predict(order, th, z, k0, h) - T[k0 + h, z])
    res[order] = {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}
print(fn.split("/")[-1])
for order, r in res.items():
    print(f"  ARX({order}) RMSE  1 step {r[1]:.3f}  1 h {r[12]:.3f}  3 h {r[36]:.3f}  6 h {r[72]:.3f}  K")
