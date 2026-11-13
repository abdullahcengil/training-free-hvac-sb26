"""Offline check (training traces only): does a second, slower mass node help multi-step prediction?

M2: dT = -lam (T - Tm) + g q[k-1] + c + b (oat - T) + c_cm cm,           Tm = EMA(T, 48)
M3: M2 + (-lam2) (T - Tm2),                                              Tm2 = EMA(T, N2)
Least squares on days 1-20, open-loop prediction on days 21-29 (12 h horizon too).
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
k_tr = np.arange(288 * 2, 288 * 21)
origins = np.arange(288 * 21, n - 150, 7)
H = (12, 36, 72, 144)


def ema(x, N):
    m = np.empty_like(x)
    m[0] = x[0]
    for k in range(1, len(x)):
        m[k] = m[k - 1] + (x[k - 1] - m[k - 1]) / N
    return m


def run(N2):
    errs = {h: [] for h in H}
    for z in range(nz):
        Tz = T[:, z]
        m1 = ema(Tz, 48.0)
        m2 = ema(Tz, N2) if N2 else None
        cols = [Tz[k_tr] - m1[k_tr], q[k_tr - 1, z], np.ones(len(k_tr)), oat[k_tr] - Tz[k_tr], cm[k_tr]]
        if N2:
            cols.append(Tz[k_tr] - m2[k_tr])
        X = np.stack(cols, 1)
        th, *_ = np.linalg.lstsq(X, Tz[k_tr + 1] - Tz[k_tr], rcond=None)
        for k0 in origins:
            t, a1, a2 = Tz[k0], m1[k0], (m2[k0] if N2 else 0.0)
            for j in range(max(H)):
                k = k0 + j
                f = [t - a1, q[k - 1, z], 1.0, oat[k] - t, cm[k]] + ([t - a2] if N2 else [])
                tn = t + float(np.dot(th, f))
                a1 = a1 + (t - a1) / 48.0
                if N2:
                    a2 = a2 + (t - a2) / N2
                t = tn
                if j + 1 in errs:
                    errs[j + 1].append(t - Tz[k + 1])
    return {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}


print(fn.split("/")[-1])
for N2 in (0, 288, 864):
    r = run(N2)
    print(f"  N2={N2:4d}: 1 h {r[12]:.3f}  3 h {r[36]:.3f}  6 h {r[72]:.3f}  12 h {r[144]:.3f} K")
