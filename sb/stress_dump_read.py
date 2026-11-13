"""Read sb/stress_dump.py traces: which zones miss the band while occupied, and why.

For each occupied step a zone is below its band (by more than 0.05 K), the box is classed as
  at its maximum airflow (>= 95 % of the box maximum: the plant cannot give more air),
  at the policy's heating cap (heating, flow below 95 % of the maximum),
  not heating (no planned heat): the controller did not ask for heat.
Also prints, per zone that misses, its model parameters and disturbance estimate against the building's median.

    python -m sb.stress_dump_read D:/SmartBuildings_data/results/stressdiag/b7_duluth.npz
"""

from __future__ import annotations

import sys

import numpy as np


def load(path: str) -> dict:
    d = dict(np.load(path))
    names = [s.replace("_zone_air_temperature_sensor", "").replace("VAV_", "room_") for s in d["policy_zones"]]
    zn = list(d["zone_names"])
    idx = [zn.index(n) for n in names]
    for k in ("occ", "lo", "hi"):
        d[k] = d[k][:, idx]
    d["names"] = names
    return d


def main(path: str) -> None:
    d = load(path)
    T, occ, lo = d["T"], d["occ"], d["lo"]
    n, nz = T.shape
    miss = (occ > 0) & (T < lo - 0.05)
    short = np.where(miss, lo - T, 0.0)
    print(f"{path}: {n} steps, {nz} zones; occupied zone-steps {int((occ > 0).sum())}, below band {int(miss.sum())} "
          f"({100 * miss.sum() / max((occ > 0).sum(), 1):.1f} %); shortfall-steps by zone (top 8):")
    at_max = d["flow"] >= 0.95 * d["maxflow"]
    heating = d["q_plan"] > 0
    med = np.median(d["theta2"][-1], axis=0)
    print(f"   building median theta2 (end): {np.round(med, 4)}")
    order = np.argsort(-short.sum(0))
    for z in order[:8]:
        m = miss[:, z]
        if not m.any():
            break
        print(f"   {d['names'][z]:28s} K-steps {short[:, z].sum():7.1f}  steps {m.sum():4d}  "
              f"at box max {100 * (m & at_max[:, z]).sum() / m.sum():5.1f} %  "
              f"heating below max {100 * (m & heating[:, z] & ~at_max[:, z]).sum() / m.sum():5.1f} %  "
              f"not heating {100 * (m & ~heating[:, z]).sum() / m.sum():5.1f} %  "
              f"dis {np.mean(d['dis'][m, z]):6.1f} K  flow/max {np.mean(d['flow'][m, z] / d['maxflow'][m, z]):.2f}  "
              f"theta2 {np.round(d['theta2'][-1, z], 4)}  dhat {np.mean(d['dhat'][m, z]):+.3f}")
    tot = miss.sum()
    if tot:
        print(f"   all misses: at box max {100 * (miss & at_max).sum() / tot:.1f} %, heating below max "
              f"{100 * (miss & heating & ~at_max).sum() / tot:.1f} %, not heating {100 * (miss & ~heating).sum() / tot:.1f} %")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
