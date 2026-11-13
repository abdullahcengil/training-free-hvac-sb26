"""Offline check (training traces only): zone model structures for multi-step prediction.

M0  dT = -lam (T - 295) + g q[k-1] + c                         (the controller's model)
M1  dT = -lam (T - Tm) + g q[k-1] + c,  Tm = EMA of T over N steps (a slow mass node driven by the air)
M2  M1 + b (oat - T) + c1 cm                                    (envelope and internal-gain terms)
Least squares on days 1-20 per zone; open-loop prediction (Tm rolled forward too) on days 21-29.
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
k_tr = np.arange(288 + 2, 288 * 21)
origins = np.arange(288 * 21, n - 80, 5)
H = (1, 12, 36, 72)


def ema(x, N):
    m = np.empty_like(x)
    m[0] = x[0]
    a = 1.0 / N
    for k in range(1, len(x)):
        m[k] = m[k - 1] + a * (x[k - 1] - m[k - 1])   # driven by the previous air temperature
    return m


def feats(kind, Tk, Tmk, qk1, k):
    if kind == "M0":
        return [Tk - 295.0, qk1, 1.0]
    if kind == "M1":
        return [Tk - Tmk, qk1, 1.0]
    return [Tk - Tmk, qk1, 1.0, oat[k] - Tk, cm[k]]


def run(kind, N):
    errs = {h: [] for h in H}
    for z in range(nz):
        Tz = T[:, z]
        Tm = ema(Tz, N) if N else np.full(n, 295.0)
        X = np.array([feats(kind, Tz[k], Tm[k], q[k - 1, z], k) for k in k_tr])
        y = Tz[k_tr + 1] - Tz[k_tr]
        th, *_ = np.linalg.lstsq(X, y, rcond=None)
        a = 1.0 / N if N else 0.0
        for k0 in origins:
            t, tm = Tz[k0], Tm[k0]
            for j in range(max(H)):
                k = k0 + j
                t_new = t + float(np.dot(th, feats(kind, t, tm, q[k - 1, z], k)))
                tm = tm + a * (t - tm) if N else tm
                t = t_new
                if j + 1 in errs:
                    errs[j + 1].append(t - Tz[k + 1])
    return {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in errs.items()}


print(fn.split("/")[-1])
for kind, N in [("M0", 0), ("M1", 24), ("M1", 48), ("M1", 96), ("M2", 48), ("M2", 96)]:
    r = run(kind, N)
    print(f"  {kind} N={N:3d}: 5 min {r[1]:.3f}  1 h {r[12]:.3f}  3 h {r[36]:.3f}  6 h {r[72]:.3f} K")
