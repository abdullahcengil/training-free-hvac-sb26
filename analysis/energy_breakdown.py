"""Where the energy goes, from energy_dump.py traces: device shares in reward units, by period.

    python analysis/energy_breakdown.py <trace.npz> [<trace.npz> ...]

Reward weights per kW per step (from the policy's constants, which follow the reward code): electricity
0.0023 / n_ahu, gas 0.00105 / n_ahu. The split is approximate (price and carbon vary by hour) but the sum is
checked against the trace's own energy + carbon terms.
"""
import sys

import numpy as np
import pandas as pd

W_E, W_G = 0.0023, 0.00105

for fn in sys.argv[1:]:
    d = np.load(fn)
    n = len(d["reward"])
    nah = int(d["n_ahu"])
    ts = pd.date_range(str(d["start"]), periods=n, freq="5min")
    wk = ts.dayofweek >= 5
    h = ts.hour
    occ_day = (~wk) & (h >= 6) & (h < 19)
    kw = {k: np.abs(d[k]) / 1000.0 for k in ("blower", "ac", "pump", "gas", "hp")}  # the reward takes abs of the AC rate
    rew = {"fan": W_E * kw["blower"] / nah, "cool": W_E * kw["ac"] / nah, "pump": W_E * kw["pump"] / nah,
           "hp": W_E * kw["hp"] / nah, "gas": W_G * kw["gas"] / nah}
    ec = 0.2 * (d["energy"] + d["carbon"])
    comfort = -0.6 * d["prod"]
    tot_est = sum(rew.values())
    print(f"== {fn.split('/')[-1].split(chr(92))[-1]}  steps {n}  n_ahu {nah}  score {np.mean(np.abs(d['reward'])):.5f}  "
          f"comfort {comfort.mean():.5f}  e+c {ec.mean():.5f}  (device estimate {tot_est.mean():.5f})")
    on = d["flow_ahu"] > 0
    print(f"   AHU on {100 * on.mean():.0f} % of steps; mean static pressure when on "
          f"{d['dp'][on].mean() if on.any() else 0:.0f} Pa; recirc when on {d['recirc'][on].mean() if on.any() else 0:.2f}; "
          f"mean OAT {d['oat'].mean() - 273.15:.1f} C")
    periods = {"weekday 06-19": occ_day, "weekday 19-06": (~wk) & ~((h >= 6) & (h < 19)), "weekend": wk}
    for name, m in periods.items():
        share = m.mean()
        parts = "  ".join(f"{k} {v[m].mean():.5f}" for k, v in rew.items() if v.mean() > 1e-7)
        kws = "  ".join(f"{k} {v[m].mean():.1f}kW" for k, v in kw.items() if v.mean() > 1e-4)
        print(f"   {name:14s} {100 * share:4.0f} % of time, e+c/step {ec[m].mean():.5f} ({100 * ec[m].sum() / ec.sum():4.1f} % of e+c): {parts}")
        print(f"   {'':14s} {kws}")
    for k, v in rew.items():
        if v.mean() > 1e-7:
            print(f"   share of e+c (estimate) {k:5s} {100 * v.sum() / tot_est.sum():5.1f} %")
