"""Read sb/bigbld_dump.py traces in cold weather (docs/BIG_BUILDINGS.md, deep-cold diagnosis; description only).

Per trace: the loss split; gas while occupied and empty; the occupied zone-steps below the band and what the box was
doing then (airflow as a share of its maximum: v14 caps heating flow at f_heat_max 0.245, f_heat_rec 0.35 at night and
f_heat_safety 0.45 when boosting; damper fully open; air handler pressure); the zones that carry the comfort loss; the
comfort loss and gas by weekday hour and by day.

    python -m sb.cold_diag_read D:/SmartBuildings_data/results/coldsize_diag/v14_7407_fairbanks_full.npz ...
"""

from __future__ import annotations

import sys

import numpy as np


def shortfall_cost(dev: np.ndarray) -> np.ndarray:
    """The reward's comfort cost per occupant for a deviation in K: linear in dev / 5 K, quadratic beyond 5 K."""
    x = np.maximum(dev, 0.0) / 5.0
    return np.where(x <= 1.0, x, x ** 2)


def summary(path: str) -> None:
    d = dict(np.load(path))
    n = len(d["reward"])
    occ_b = d["occ_total"] > 0
    T, lo, hi, occ = d["T"], d["lo"], d["hi"], d["occ"]
    dev = np.maximum(lo - T, 0.0) + np.maximum(T - hi, 0.0)
    zc = occ * shortfall_cost(dev) / np.maximum(d["occ_total"][:, None], 1e-9)    # per zone, per step
    area = d["area"] * float(d["cv_m"]) ** 2
    gas = d["gas"] / 1000.0
    print(f"\n== {path.replace(chr(92), '/').split('/')[-1]}: {n} steps, {T.shape[1]} zones, floor {np.nansum(area):.0f} m2, "
          f"oat mean {np.mean(d['oat']) - 273.15:.1f} C")
    print(f"   loss {-d['reward'].mean():.5f} = energy {0.2 * d['energy'].mean():.5f} + carbon "
          f"{0.2 * d['carbon'].mean():.5f} + comfort {-0.6 * d['prod'].mean():.5f} (from zones {0.6 * zc.sum(1).mean():.5f})")
    print(f"   gas kW: occupied {gas[occ_b].mean():.1f}, empty {gas[~occ_b].mean():.1f}; per m2 {1000 * gas.mean() / np.nansum(area):.1f} W")
    zo = occ > 0
    cold = (T < lo - 0.05) & zo
    fr = d["flow"] / np.maximum(d["vmax"], 1e-9)
    print(f"   occupied zone-steps below the band: {100 * cold.sum() / max(zo.sum(), 1):.1f} %, mean shortfall "
          f"{np.mean((lo - T)[cold]) if cold.any() else 0:.2f} K")
    if cold.any():
        f = fr[cold]
        bins = [(0, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.95), (0.95, 2)]
        print("   ...their airflow / box maximum: " + ", ".join(f"{a:.2f}-{b:.2f} {100 * np.mean((f >= a) & (f < b)):.0f} %"
                                                          for a, b in bins))
        on = d["a_on"][:, d["ahu_of"]] > 0.5
        print(f"   ...damper >= 0.95 {100 * np.mean(d['damper'][cold] >= 0.95):.0f} %, AHU on {100 * np.mean(on[cold]):.0f} %, "
              f"AHU pressure {np.mean(d['a_p'][:, d['ahu_of']][cold]):.0f} Pa, supply-air setpoint {np.mean(d['a_sat'][:, d['ahu_of']][cold]) - 273.15:.1f} C (the supply is the mixed air when colder)")
    zl = 0.6 * zc.sum(0) / n
    order = np.argsort(-zl)[:6]
    print("   zones carrying the comfort loss (share, area m2, box max m3/s, area per box flow, mean T-lo occupied):")
    for z in order:
        if zl[z] <= 0:
            break
        m = zo[:, z]
        print(f"     {d['vids'][z]}: {100 * zl[z] / max(zl.sum(), 1e-12):4.0f} %  {area[z]:6.0f}  {np.mean(d['vmax'][:, z]):.2f}"
              f"  {area[z] / max(np.mean(d['vmax'][:, z]), 1e-9):5.0f}  {np.mean((T - lo)[m, z]) if m.any() else 0:+.2f}")
    h = np.floor(d["hour"]).astype(int)
    wk = d["day"] < 5
    print("   weekday hour: comfort loss, zones below band (occupied %), gas kW")
    for hh in range(0, 24, 2):
        m = wk & ((h == hh) | (h == hh + 1))
        if m.any():
            print(f"     {hh:02d}-{hh + 2:02d}  {0.6 * zc[m].sum(1).mean():.5f}  {100 * cold[m].sum() / max(zo[m].sum(), 1):5.1f}"
                  f"  {gas[m].mean():6.1f}  oat {np.mean(d['oat'][m]) - 273.15:5.1f}")
    days = np.floor(np.arange(n) / 288).astype(int)
    print("   by day (day index from the trace's clock): comfort loss, gas kW, oat C")
    for k in np.unique(days):
        m = days == k
        print(f"     day {k} (clock {int(d['day'][m][0])}): {0.6 * zc[m].sum(1).mean():.5f}  {gas[m].mean():6.1f}  "
              f"{np.mean(d['oat'][m]) - 273.15:6.1f}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        summary(p)
