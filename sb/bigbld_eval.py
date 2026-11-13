"""Read docs/BIG_BUILDINGS.md by its rule: full-size vs scaled round-5 buildings, first 2880 steps.

    python -m sb.bigbld_eval [--steps 2880]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

R = Path("D:/SmartBuildings_data/results")
PAIRS = [f"{b}__{w}" for b in ("building_7402", "building_7407", "building_7408")
         for w in ("chicago_jan15", "dubai_jul15")]


def loss(d: Path, s: str, n: int) -> float | None:
    f = d / f"{s}.npy"
    if not f.exists():
        return None
    a = np.load(f).astype(float)
    return float(-a[:n, 0].mean()) if len(a) >= n else None


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=2880)
    n = ap.parse_args(argv).steps
    rows = []
    for s in PAIRS:
        v = [loss(R / "bigbld" / "v14", s, n), loss(R / "bigbld" / "pid_water", s, n),
             loss(R / "hidlike" / "v14", s, n), loss(R / "hidlike" / "pid_water", s, n)]
        if None in v:
            continue
        rows.append((s, *v))
        print(f"{s:30s} full v14 {v[0]:.5f} pid {v[1]:.5f} ratio {v[0] / v[1]:.3f} | scaled v14 {v[2]:.5f} "
              f"pid {v[3]:.5f} ratio {v[2] / v[3]:.3f}")
    if not rows:
        return
    rf = sum(r[1] for r in rows) / sum(r[2] for r in rows)
    rs = sum(r[3] for r in rows) / sum(r[4] for r in rows)
    k = rf / rs
    verdict = ("SIZE IS THE MISSING PIECE" if rf >= 0.160 and k >= 1.15 else
               "not it" if k <= 1.05 else "unclear: run full length")
    print(f"ratio of means: full {rf:.3f}, scaled {rs:.3f}, x{k:.2f} over {len(rows)} pairs -> {verdict}")
    print(f"level: v14 full/scaled x{sum(r[1] for r in rows) / sum(r[3] for r in rows):.2f}, "
          f"pid_water x{sum(r[2] for r in rows) / sum(r[4] for r in rows):.2f}")


if __name__ == "__main__":
    main()
