"""Fit candidate zone models to probe data and report R^2 per model.

Step k moves T[k-1] -> T[k]. The heat delivered by a box during step j is
q[j] = flow[j] * c_air * (discharge[j] - T[j-1]) in kW.

    python -m sb.fit_probe D:/SmartBuildings_data/results/probe_b1_atl.npz
"""

from __future__ import annotations

import json
import sys

import numpy as np

C_AIR = 1005.0 * 1.2


def r2(y, yhat):
    return 1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def fit(path: str) -> dict:
    d = np.load(path)
    T, Q = d["T"], d["Q"]
    F, D = Q[..., 0], Q[..., 1]
    q = np.zeros_like(T)
    q[1:] = F[1:] * (D[1:] - T[:-1]) * C_AIR / 1e3
    y = T[2:] - T[1:-1]            # change during step k (k = 2..)
    q_now, q_prev = q[2:], q[1:-1]
    t_prev = T[1:-1] - 295.0
    models = {
        "no_delay": lambda z: np.c_[q_now[:, z], np.ones(len(y))],
        "delay": lambda z: np.c_[q_prev[:, z], np.ones(len(y))],
        "delay_relax": lambda z: np.c_[t_prev[:, z], q_prev[:, z], np.ones(len(y))],
        "both_relax": lambda z: np.c_[t_prev[:, z], q_now[:, z], q_prev[:, z], np.ones(len(y))],
    }
    out = {}
    for name, X_of in models.items():
        scores, coefs = [], []
        for z in range(T.shape[1]):
            X = X_of(z)
            c, *_ = np.linalg.lstsq(X, y[:, z], rcond=None)
            scores.append(r2(y[:, z], X @ c))
            coefs.append(c.tolist())
        coefs = np.array(coefs)
        out[name] = {"r2_median": float(np.median(scores)), "r2_min": float(np.min(scores)),
                     "coef_median": np.median(coefs, axis=0).round(4).tolist()}
    out["zones"] = int(T.shape[1])
    out["steps"] = int(T.shape[0])
    return out


if __name__ == "__main__":
    res = {p: fit(p) for p in sys.argv[1:]}
    print(json.dumps(res, indent=1))
