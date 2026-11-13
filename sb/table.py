"""Per-scenario table of result folders: score, comfort, energy+carbon (all per step, weighted).

    python -m sb.table <root> <run> [<run> ...]
"""
import json
import sys
from pathlib import Path

import numpy as np

root = Path(sys.argv[1])
runs = sys.argv[2:]
data = {}
for r in runs:
    for f in sorted((root / r).glob("*.json")):
        j = json.loads(f.read_text())
        n = j["steps"]
        c = j["components"] or {}
        data.setdefault(f.stem, {})[r] = (abs(j["total_reward"]) / n, -0.6 * c.get("prod", np.nan) / n,
                                          0.2 * (c.get("energy", np.nan) + c.get("carbon", np.nan)) / n)
names = sorted(data)
print("scenario".ljust(34) + "".join(r[:16].rjust(17) for r in runs))
for s in names:
    print(s.ljust(34) + "".join((f"{data[s][r][0]:.5f}" if r in data[s] else "-").rjust(17) for r in runs))
for k, lab in [(0, "mean score"), (1, "comfort"), (2, "energy+carbon")]:
    vals = []
    for r in runs:
        v = [data[s][r][k] for s in names if r in data[s]]
        vals.append(f"{np.mean(v):.5f} ({len(v)})")
    print(lab.ljust(34) + "".join(v.rjust(17) for v in vals))
if len(runs) > 1:
    base = runs[0]
    for r in runs[1:]:
        both = [s for s in names if base in data[s] and r in data[s]]
        better = sum(data[s][r][0] < data[s][base][0] - 1e-9 for s in both)
        same = sum(abs(data[s][r][0] - data[s][base][0]) <= 1e-9 for s in both)
        print(f"{r} vs {base}: better in {better}, identical in {same}, worse in {len(both) - better - same} of {len(both)}")
