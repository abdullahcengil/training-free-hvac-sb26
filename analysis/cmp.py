"""Compare result folders scenario by scenario against a base folder (training runs).

    python analysis/cmp.py <base_dir> <dir> [<dir> ...]
"""
import json
import sys
from pathlib import Path

base = Path(sys.argv[1])
for d in map(Path, sys.argv[2:]):
    print(f"== {d.name} vs {base.name}")
    sa = sb = 0.0
    for f in sorted(d.glob("*.json")):
        fb = base / f.name
        if not fb.exists():
            continue
        a, b = json.loads(fb.read_text()), json.loads(f.read_text())
        n = a["steps"]
        ca, cb = a["components"], b["components"]
        ra, rb = abs(a["mean_reward"]), abs(b["mean_reward"])
        sa += ra
        sb += rb
        print(f"  {f.stem:32s} {ra:.5f} -> {rb:.5f} ({100 * (rb / ra - 1):+6.1f} %)  comfort {-0.6 * ca['prod'] / n:.5f}->{-0.6 * cb['prod'] / n:.5f}"
              f"  e+c {0.2 * (ca['energy'] + ca['carbon']) / n:.5f}->{0.2 * (cb['energy'] + cb['carbon']) / n:.5f}")
    if sa:
        print(f"  sum {sa:.5f} -> {sb:.5f} ({100 * (sb / sa - 1):+.1f} %)")
