"""Compare per-step rewards of two result folders (bit-for-bit checks).

    python -m sb.stepcmp <dir_a> <dir_b>
"""
import sys
from pathlib import Path

import numpy as np

a_dir, b_dir = Path(sys.argv[1]), Path(sys.argv[2])
for fa in sorted(a_dir.glob("*.npy")):
    fb = b_dir / fa.name
    if not fb.exists():
        print(fa.stem, "missing in", b_dir)
        continue
    a, b = np.load(fa), np.load(fb)
    n = min(len(a), len(b))
    same = np.array_equal(a[:n], b[:n])
    bad = np.flatnonzero(np.any(a[:n] != b[:n], axis=1))
    print(f"{fa.stem}: {n} steps, identical={same}, first differing step={bad[0] if len(bad) else '-'}, "
          f"total {a[:n, 0].sum():.6f} vs {b[:n, 0].sum():.6f}")
