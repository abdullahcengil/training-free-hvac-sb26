"""Offline check (training traces only): can a second-order zone model be identified ONLINE (RLS with
forgetting, from a cold start), and how good are its multi-step predictions compared with the first-order
model the controller uses?

Model (per zone, 5-min steps), with the controller's one-step actuation delay:
    T[k+1] = a1 T[k] + a2 T[k-1] + b1 q[k-1] + b2 q[k-2] + d1 oat[k] + d2 cm[k] + e
RLS runs causally through the trace; at each test origin k0 (from day 3 on) the current estimate predicts
h steps ahead with the heat that was actually applied.

    python analysis/arx_online.py <trace.npz> "<start timestamp>"
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
H = (12, 36, 72)


def regress(order, k, z):
    row = [T[k - i, z] for i in range(order)] + [q[k - 1 - i, z] for i in range(order)] + [oat[k], cm[k], 1.0]
    return np.array(row)


def predict(order, th, z, k0, h):
    hist = list(T[k0 - order + 1:k0 + 1, z])
    for j in range(h):
        k = k0 + j
        row = hist[::-1][:order] + [q[k - 1 - i, z] for i in range(order)] + [oat[k], cm[k], 1.0]
        hist.append(float(np.dot(th, row)))
    return hist[-1]


for order in (1, 2):
    for lam in (0.995, 0.999):
        errs = {h: [] for h in H}
        for z in range(nz):
            m = 2 * order + 3
            th = np.zeros(m)
            th[0] = 1.0
            P = np.eye(m) * 10.0
            P[-1, -1] = 1e4
            for k in range(3, n - 1):
                phi = regress(order, k, z)
                # scale-friendly: temperatures relative to 295 K inside the regressor
                y = T[k + 1, z]
                Pphi = P @ phi
                g = Pphi / (lam + phi @ Pphi)
                th = th + g * (y - phi @ th)
                P = (P - np.outer(g, Pphi)) / lam
                if k >= 288 * 3 and k % 7 == 0:
                    for h in H:
                        if k + h < n:
                            errs[h].append(predict(order, th, z, k, h) - T[k + h, z])
        r = {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}
        print(f"{fn.split('/')[-1][:28]} ARX({order}) lam {lam}: 1 h {r[12]:.3f}  3 h {r[36]:.3f}  6 h {r[72]:.3f} K")
