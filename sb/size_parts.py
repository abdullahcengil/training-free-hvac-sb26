"""Where the extra loss of full-size buildings comes from (docs/BIG_BUILDINGS.md, replication pairs; description only,
no rule): per controller and season, the mean loss per step at full size and scaled, split into comfort and energy plus
carbon, and into occupied and empty steps (from the per-step records of sb/run.py).

    python -m sb.size_parts
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from sb.make_bigdev import PAIRS
from sb.make_bigdev_scaled import BUILDINGS

R = Path("D:/SmartBuildings_data/results")
DIRS = {"v14": (R / "bigdev/v14", R / "bigdev_scaled/v14"),
        "pid_water": (R / "bigdev/pid_water", R / "bigdev_scaled/pid_water")}


def parts(f: Path) -> np.ndarray:
    """[comfort occupied, comfort empty, energy+carbon occupied, energy+carbon empty] as shares of the run's mean
    over its first 2880 steps (the scaled records of the first test are full length)."""
    a = np.load(f).astype(float)[:2880]
    occ = a[:, 4] > 0
    comfort = -0.6 * a[:, 1]
    ec = 0.2 * (a[:, 2] + a[:, 3])
    n = len(a)
    return np.array([comfort[occ].sum(), comfort[~occ].sum(), ec[occ].sum(), ec[~occ].sum()]) / n


def main() -> None:
    from sb.bigbld_eval import PAIRS as PAIRS1

    print("first test (round-5 buildings 7402, 7407, 7408):")
    report(PAIRS1, {"v14": (R / "bigbld/v14", R / "hidlike/v14"),
                    "pid_water": (R / "bigbld/pid_water", R / "hidlike/pid_water")})
    print("replication (round-1 buildings 7001, 7002, 7003, 7007, 7008):")
    report([f"{b}__{w}" for b in BUILDINGS for w in PAIRS[b]], DIRS)


def report(names: list[str], dirs: dict[str, tuple[Path, Path]]) -> None:
    for pol, (full, scaled) in dirs.items():
        for season, key in (("cold", "jan"), ("hot", "jul")):
            sel = [n for n in names if key in n and (full / f"{n}.npy").exists() and (scaled / f"{n}.npy").exists()]
            if not sel:
                continue
            pf = np.mean([parts(full / f"{n}.npy") for n in sel], axis=0)
            ps = np.mean([parts(scaled / f"{n}.npy") for n in sel], axis=0)
            print(f"{pol:9s} {season} ({len(sel)} pairs): full {pf.sum():.5f} vs scaled {ps.sum():.5f} "
                  f"(x{pf.sum() / ps.sum():.2f}); extra = comfort occupied {pf[0] - ps[0]:+.5f}, comfort empty "
                  f"{pf[1] - ps[1]:+.5f}, energy occupied {pf[2] - ps[2]:+.5f}, energy empty {pf[3] - ps[3]:+.5f}")


if __name__ == "__main__":
    main()
