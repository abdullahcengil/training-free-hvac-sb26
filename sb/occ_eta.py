"""Event-triggered averages of the zone error, temperature change and heat around departures and arrivals (sb/occ_dump.py traces)."""
import sys
import numpy as np
d = np.load(sys.argv[1])
T, q, occ, hour, err = d["T"], d["q"], d["occ"], d["hour"], d["err"]
n, nz = T.shape
dT = np.full_like(T, np.nan); dT[:-1] = T[1:] - T[:-1]
ev = [(k, z) for k in range(30, n - 30) for z in range(nz) if occ[k, z] < occ[k - 1, z] - 0.5 and 13 <= hour[k] < 19.5]
arr = [(k, z) for k in range(30, n - 30) for z in range(nz) if occ[k, z] > occ[k - 1, z] + 0.5]
W = range(-6, 13)
def eta(events, x):
    out = []
    for L in W:
        v = [x[k + L, z] - np.nanmean(x[k + L, :]) for k, z in events]   # minus the same step's mean over all zones
        out.append(np.nanmean(v))
    return np.array(out)
print(sys.argv[1].split("/")[-1], len(ev), "departures,", len(arr), "arrivals")
for name, x in (("err", err), ("dT", dT), ("q", q)):
    a, b = eta(ev, x), eta(arr, x)
    print(f"  {name:3s} around departures (mK or W, relative to the zone mean at the same step), offsets {W.start}..{W.stop-1}:")
    print("     dep:", " ".join(f"{v*1000:+.0f}" for v in a))
    print("     arr:", " ".join(f"{v*1000:+.0f}" for v in b))
