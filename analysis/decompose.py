"""Score decomposition of one result folder by station and component (per step, weighted)."""
import json
import sys
from pathlib import Path

rows = []
for f in sorted(Path(sys.argv[1]).glob("*.json")):
    j = json.loads(f.read_text())
    n, c = j["steps"], j["components"]
    st = f.stem.split("__")[1].split("_")[0]
    rows.append((f.stem, st, abs(j["total_reward"]) / n, -0.6 * c["prod"] / n, 0.2 * c["energy"] / n, 0.2 * c["carbon"] / n))
tot = sum(r[2] for r in rows)
print(f"mean {tot / len(rows):.5f} over {len(rows)}")
by = {}
for r in rows:
    b = by.setdefault(r[1], [0, 0, 0, 0, 0])
    for i in range(4):
        b[i] += r[2 + i]
    b[4] += 1
for k, b in by.items():
    print(f"{k:10s} n={b[4]:2d} share {100 * b[0] / tot:5.1f}%  score/scen {b[0] / b[4]:.5f}  comfort {b[1] / b[4]:.5f}  energy {b[2] / b[4]:.5f}  carbon {b[3] / b[4]:.5f}")
for r in sorted(rows, key=lambda r: -r[2]):
    print(f"{r[0]:34s} {r[2]:.5f}  comfort {r[3]:.5f}  energy {r[4]:.5f}  carbon {r[5]:.5f}")
