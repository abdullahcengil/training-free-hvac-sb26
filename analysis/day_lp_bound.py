"""Offline bound (v2: zone air 15.85-29.85 C at all times, box cooling capacity) (training traces only): the cheapest heating/cooling schedule per zone and weekday
under the zone's identified M2 model (online replay, forgetting 0.998), compared with what v10 did.

Per zone and day (19:00 to 19:00): variables T, Tm, cooling u >= 0, heating h >= 0 (kW to the zone).
Dynamics: M2 with the parameters identified by 19:00. Comfort band only during occupied steps
(06:00-19:00, weekday); the slab must end no warmer (cooling season) or no colder (heating season)
than it started, so no free energy is borrowed from the next day. Cost per kW of cooling: electricity
price + carbon by hour (reward weights), / COP, times the outside-air factor; per kW of heating: gas
weights times the gas factor. AHU coupling (minimum flow, one supply temperature) is ignored.

    python analysis/day_lp_bound.py <trace.npz> "<start>" <n_zones_to_sample>
"""
import sys

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

fn, start, nsamp = sys.argv[1], sys.argv[2], int(sys.argv[3])
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

# Reward weights per kW per step for this building (energy 0.2, carbon 0.2), from the reward code.
n_ahu = d["sat"].shape[1]
price_wd = np.array([16] * 6 + [18] * 6 + [20] * 7 + [16] * 5) / 100.0
carbon = np.array([88.2, 87.8, 87.9, 87.8, 88.0, 88.2, 89.7, 94.0, 98.9, 100.8, 101.4, 101.8, 102.6, 103.4, 104.1, 104.7,
                   102.1, 97.0, 93.6, 92.5, 91.7, 90.7, 89.8, 89.0])
w_e_kw = 0.0023 / n_ahu   # reward per kW of electricity per step at a typical hour (from the policy's constants)
COP, SAT = 3.5, 285.35
lo_c, hi_c = 294.0 + 0.3952, 297.0 - 0.4251


def elec_w(h):
    # scale the typical weight by this hour's price and carbon relative to their means
    return w_e_kw * 0.5 * (price_wd[h] / price_wd.mean() + carbon[h] / carbon.mean())


rng = np.random.default_rng(0)
zones = rng.choice(nz, size=min(nsamp, nz), replace=False)
tot_lp = tot_v10 = 0.0
days = [dd for dd in pd.date_range(ts[0].normalize() + pd.Timedelta(days=2), ts[-1].normalize() - pd.Timedelta(days=1), freq="D")
        if dd.dayofweek < 5]
for day in days[:6]:
    k0 = ts.get_loc(day - pd.Timedelta(hours=5))
    H = 288
    ks = np.arange(k0, k0 + H)
    hrs = ts[ks].hour
    occ = cm[ks] > 0.5
    for z in zones:
        thz = TH[k0, z]
        # variables: T[0..H], Tm[0..H], u[0..H-1], h[0..H-1]
        nT = H + 1
        iT = lambda j: j
        iM = lambda j: nT + j
        iu = lambda j: 2 * nT + j
        ih = lambda j: 2 * nT + H + j
        nv = 2 * nT + 2 * H
        A = lil_matrix((2 * H + 2, nv)); b = np.zeros(2 * H + 2)
        r = 0
        for j in range(H):
            k = ks[j]
            # T[j+1] = T[j] + th0 (T[j]-Tm[j]) + th1 (h[j-1]-u[j-1]) + th2 + th3 (oat - T[j]) + th4 cm
            A[r, iT(j + 1)] = 1.0
            A[r, iT(j)] = -(1.0 + thz[0] - thz[3])
            A[r, iM(j)] = thz[0]
            if j >= 1:
                A[r, ih(j - 1)] = -thz[1]
                A[r, iu(j - 1)] = thz[1]
                b[r] = thz[2] + thz[3] * oat[k] + thz[4] * cm[k]
            else:
                b[r] = thz[2] + thz[3] * oat[k] + thz[4] * cm[k] + thz[1] * q[k - 1, z]
            r += 1
            A[r, iM(j + 1)] = 1.0
            A[r, iM(j)] = -(1 - 1 / 48.0)
            A[r, iT(j)] = -1 / 48.0
            r += 1
        A[r, iT(0)] = 1.0; b[r] = T[k0, z]; r += 1
        A[r, iM(0)] = 1.0; b[r] = TM[k0, z]; r += 1
        bounds = [(289.0, 303.0)] * nT + [(250, 330)] * nT + [(0, 60)] * H + [(0, 60)] * H
        for j in range(1, nT):
            if j - 1 < H and occ[j - 1]:
                bounds[iT(j)] = (lo_c, hi_c)
        heating = oat[ks].mean() < 291.0
        # slab end condition
        A_ub = lil_matrix((1 + H, nv)); b_ub = np.zeros(1 + H)
        for j in range(H):
            A_ub[1 + j, iu(j)] = 1.0
            A_ub[1 + j, iT(j)] = -2.0 * 1.206
            b_ub[1 + j] = -2.0 * 1.206 * 285.35
        if heating:
            A_ub[0, iM(H)] = -1.0; b_ub[0] = -TM[k0, z]
        else:
            A_ub[0, iM(H)] = 1.0; b_ub[0] = TM[k0, z]
        c = np.zeros(nv)
        for j in range(H):
            k = ks[j]
            s_mix = 0.7 * 296.0 + 0.3 * oat[k]
            oa = 1.0 + 0.3 * max(oat[k] - 296.0, 0.0) / (296.0 - SAT)
            c[iu(j)] = elec_w(hrs[j]) / COP * oa
            gasf = (308.15 - min(s_mix, 296.0)) / (308.15 - 294.5)
            c[ih(j)] = 0.00105 / n_ahu * gasf
        res = linprog(c, A_ub=A_ub.tocsr(), b_ub=b_ub, A_eq=A.tocsr(), b_eq=b, bounds=bounds, method="highs")
        if res.status != 0:
            continue
        # v10's cost for the same zone-day with the same cost model
        qq = q[ks, z]
        v10 = sum((elec_w(hrs[j]) / COP * (1.0 + 0.3 * max(oat[ks[j]] - 296.0, 0.0) / (296.0 - SAT))) * max(-qq[j], 0)
                  + 0.00105 / n_ahu * (308.15 - min(0.7 * 296 + 0.3 * oat[ks[j]], 296.0)) / (308.15 - 294.5) * max(qq[j], 0)
                  for j in range(H))
        tot_lp += res.fun
        tot_v10 += v10
    print(f"{day.date()}: cumulative v10 {tot_v10:.4f}  LP {tot_lp:.4f}  ratio {tot_lp / max(tot_v10, 1e-12):.2f}", flush=True)
