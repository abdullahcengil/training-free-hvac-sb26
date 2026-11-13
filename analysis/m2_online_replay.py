"""Replay the policy's online mass-model identification (_identify_m2) on recorded v10 traces
(training scenarios only): prediction quality and bound hits for several settings.

    python analysis/m2_online_replay.py <trace.npz> "<start>" [forget ...]
"""
import sys

import numpy as np
import pandas as pd

fn, start = sys.argv[1], sys.argv[2]
forgets = [float(x) for x in sys.argv[3:]] or [0.995]
d = np.load(fn)
T, q, oat = d["T"], d["q_plan"], d["oat"]
n, nz = T.shape
ts = pd.date_range(start, periods=n, freq="5min")
cm = (((ts.hour >= 6) & (ts.hour < 19)) & (ts.dayofweek < 5)).astype(float)
PRIOR = np.array([-0.33, 0.27, 0.09, 0.016, 0.25])
LO = np.array([float(x) for x in __import__("os").environ.get("M2LO", "-0.8,0.05,-0.5,0.0,-0.2").split(",")])
HI = np.array([float(x) for x in __import__("os").environ.get("M2HI", "-0.1,0.8,0.6,0.08,0.8").split(",")])
PVAR = np.array([1e-3, 1e-3, 1e-2, 1e-5, 1e-2])
N = 48.0


def step(th, t, tm, qq, o, c):
    return t + th[:, 0] * (t - tm) + th[:, 1] * qq + th[:, 2] + th[:, 3] * (o - t) + th[:, 4] * c


for lam in forgets:
    th = np.tile(PRIOR, (nz, 1))
    P = np.tile(np.diag(PVAR), (nz, 1, 1))
    tm = T[0].copy()
    dhat = np.zeros(nz)
    e1, at_b = [], []
    multi = {12: [], 36: [], 72: []}
    for k in range(1, n):
        # transition k-1 -> k, heat commanded at k-2 (prev_q2)
        if k >= 2:
            phi = np.stack([T[k - 1] - tm, q[k - 2], np.ones(nz), oat[k - 1] - T[k - 1], np.full(nz, cm[k - 1])], 1)
            y = T[k] - T[k - 1]
            Pphi = np.einsum("nij,nj->ni", P, phi)
            den = lam + np.einsum("ni,ni->n", phi, Pphi)
            g = Pphi / den[:, None]
            err = y - np.einsum("ni,ni->n", phi, th)
            if k > 288:
                e1.append(err - dhat)       # one-step error of the prediction the policy would have made
            dhat = np.clip(0.9 * dhat + 0.1 * err, -1.5, 1.5)
            err = np.clip(err, -0.5, 0.5)
            th = np.clip(th + g * err[:, None], LO, HI)
            P = (P - np.einsum("ni,nj->nij", g, Pphi)) / lam
            tr = np.trace(P, axis1=1, axis2=2)
            big = tr > 1.0
            if big.any():
                P[big] *= (1.0 / tr[big])[:, None, None]
            at_b.append(((th <= LO + 1e-9) | (th >= HI - 1e-9)).mean(0))
        tm = tm + (T[k - 1] - tm) / N
        if k > 288 * 3 and k % 11 == 0 and k + 73 < n:
            t, m = T[k].copy(), tm.copy()
            for j in range(72):
                kk = k + j
                t_new = step(th, t, m, q[kk - 1], oat[kk], cm[kk]) + dhat
                m = m + (t - m) / N
                t = t_new
                if j + 1 in multi:
                    multi[j + 1].append(t - T[kk + 1])
    e1 = np.array(e1)
    at_b = np.array(at_b).mean(0)
    r = {h: float(np.sqrt(np.mean(np.square(v)))) for h, v in multi.items()}
    print(f"{fn.split('/')[-1][:30]} forget {lam}: 1-step {np.sqrt(np.mean(e1 ** 2)):.3f}  1 h {r[12]:.3f}  3 h {r[36]:.3f}  6 h {r[72]:.3f} K;"
          f"  at bounds -lam {at_b[0]:.2f} g {at_b[1]:.2f} c {at_b[2]:.2f} b {at_b[3]:.2f} ccm {at_b[4]:.2f}")
    print("   final theta medians:", np.round(np.median(th, 0), 4))

# Steady-state heat (kW) each zone needs to hold 21.3 °C at the trace's mean occupied outside temperature,
# from the final identified parameters (Tm = T in steady state).
occ = cm > 0.5
o = float(np.mean(oat[occ]))
T_t = 294.47
q_ss = -(th[:, 2] + th[:, 3] * (o - T_t) + th[:, 4]) / th[:, 1]
cap_kw = 0.2453 * 2.0 * 1206.0 * (308.15 - T_t) / 1000.0
print(f"   steady-state heat to hold 21.3 C at oat {o - 273.15:.1f} C: median {np.median(q_ss):.2f} kW, max {q_ss.max():.2f} kW;"
      f" zones above the daytime cap ({cap_kw:.1f} kW): {(q_ss > cap_kw).sum()} of {nz}")
