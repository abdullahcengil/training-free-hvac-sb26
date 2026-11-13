"""Read sb/bigbld_dump.py traces side by side (docs/BIG_BUILDINGS.md diagnosis).

Per trace: the week's mean fan, cooling and gas power and the normalised energy, occupied vs unoccupied; per hour of
day the same; the air handlers' state (on, flow / maximum, static pressure, supply-air setpoint); the boxes' state in
occupied steps (damper open fully, flow capped by the air handler, zones above the cooling setpoint).

    python -m sb.bigbld_dump_read D:/SmartBuildings_data/results/bigbld_diag/v14_7402_dubai_full.npz ...
"""

from __future__ import annotations

import sys

import numpy as np


def summary(path: str, hours: bool = True) -> None:
    d = dict(np.load(path))
    n = len(d["reward"])
    occ_b = d["occ_total"] > 0
    kw = {k: d[k] / 1000.0 for k in ("elec_blower", "elec_ac", "gas", "pump")}
    print(f"\n== {path.split('/')[-1]}: {n} steps, {d['T'].shape[1]} zones, {d['a_flow'].shape[1]} AHUs, "
          f"floor {np.nansum(d['area']) * float(d['cv_m']) ** 2:.0f} m2")
    print(f"   loss {-d['reward'].mean():.5f} = energy {0.2 * d['energy'].mean():.5f} + carbon "
          f"{0.2 * d['carbon'].mean():.5f} + comfort {-0.6 * d['prod'].mean():.5f}")
    for lab, m in (("all", np.ones(n, bool)), ("occupied", occ_b), ("unoccupied", ~occ_b)):
        print(f"   {lab:10s} fan {kw['elec_blower'][m].mean():7.1f} kW  cooling {np.abs(kw['elec_ac'][m]).mean():7.1f} kW"
              f"  gas {kw['gas'][m].mean():7.1f} kW  pump {kw['pump'][m].mean():5.2f} kW  energy {d['energy'][m].mean():.4f}"
              f"  carbon {d['carbon'][m].mean():.4f}")
    on = d["a_on"] > 0.5
    fr = d["a_flow"] / d["a_max"]
    print(f"   AHU on {100 * on.mean():.0f} % of steps; when on: flow/max {np.mean(fr[on]):.2f} (p90 "
          f"{np.percentile(fr[on], 90):.2f}), pressure {np.mean(d['a_p'][on]):.0f} Pa, SAT setpoint "
          f"{np.mean(d['a_sat_sp'][on]) - 273.15:.1f} C, SAT {np.mean(d['a_sat'][on]) - 273.15:.1f} C, recirc "
          f"{np.mean(d['a_recirc'][on]):.2f}")
    zo = d["occ"] > 0
    full = d["damper"] >= 0.95
    capped = d["ratio"] < 0.999
    warm = d["T"] > d["hi"] + 0.05
    print(f"   occupied zone-steps: damper >= 0.95 {100 * (full & zo).sum() / zo.sum():.1f} %, flow capped by AHU "
          f"{100 * (capped & zo).sum() / zo.sum():.1f} %, above cooling setpoint {100 * (warm & zo).sum() / zo.sum():.1f} %"
          f"; zone area mean {np.nanmean(d['area']) * float(d['cv_m']) ** 2:.0f} m2, flow per box when occupied "
          f"{np.mean(d['flow'][zo]):.2f} m3/s (max {np.mean(d['vmax'][zo]):.2f})")
    if hours:
        h = np.floor(d["hour"]).astype(int)
        wk = d["day"] < 5
        print("   weekday hour: fan / cooling / gas kW, energy, AHU flow/max, SAT C, zones above hi %")
        for hh in range(0, 24, 2):
            m = wk & ((h == hh) | (h == hh + 1))
            if not m.any():
                continue
            zm = zo[m]
            print(f"     {hh:02d}-{hh + 2:02d}  {kw['elec_blower'][m].mean():6.1f} {np.abs(kw['elec_ac'][m]).mean():6.1f} "
                  f"{kw['gas'][m].mean():6.1f}  {d['energy'][m].mean():.4f}  {np.mean(fr[m]):.2f}  "
                  f"{np.mean(d['a_sat'][m]) - 273.15:5.1f}  {100 * (warm[m] & zm).sum() / max(zm.sum(), 1):5.1f}"
                  f"  oat {np.mean(d['oat'][m]) - 273.15:5.1f}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        summary(p)
