"""Bootstrap intervals for the size tests (docs/BIG_BUILDINGS.md; descriptive, no rule): the factor k = (v14/pid_water
ratio of means at full size) / (the same ratio scaled), resampling the scenario pairs with replacement (10,000
draws, seed 0), for the first test (6 pairs), the replication (10 pairs) and both together.

    python -m sb.size_stats
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from sb.bigbld_eval import PAIRS as PAIRS1
from sb.bigbld_eval import loss
from sb.make_bigdev import PAIRS as BIGDEV_PAIRS
from sb.make_bigdev_scaled import BUILDINGS

R = Path("D:/SmartBuildings_data/results")


def table(pairs: list[str], dirs: tuple[Path, Path, Path, Path]) -> np.ndarray:
    rows = []
    for s in pairs:
        v = [loss(d, s, 2880) for d in dirs]
        if None not in v:
            rows.append(v)
    return np.array(rows)


def k(t: np.ndarray) -> float:
    m = t.mean(axis=0)
    return (m[0] / m[1]) / (m[2] / m[3])


def ci(t: np.ndarray, draws: int = 10_000) -> tuple[float, float]:
    rng = np.random.default_rng(0)
    ks = [k(t[rng.integers(0, len(t), len(t))]) for _ in range(draws)]
    return float(np.percentile(ks, 2.5)), float(np.percentile(ks, 97.5))


def main() -> None:
    t1 = table(PAIRS1, (R / "bigbld/v14", R / "bigbld/pid_water", R / "hidlike/v14", R / "hidlike/pid_water"))
    rep = [f"{b}__{w}" for b in BUILDINGS for w in BIGDEV_PAIRS[b]]
    t2 = table(rep, (R / "bigdev/v14", R / "bigdev/pid_water", R / "bigdev_scaled/v14", R / "bigdev_scaled/pid_water"))
    for name, t in (("first test", t1), ("replication", t2),
                    ("both", np.vstack([x for x in (t1, t2) if len(x)]) if len(t1) or len(t2) else t1)):
        if len(t) < 2:
            print(f"{name}: {len(t)} pairs")
            continue
        lo, hi = ci(t)
        print(f"{name}: {len(t)} pairs, k = {k(t):.2f} (95 % interval {lo:.2f}-{hi:.2f}); full ratio "
              f"{t[:, 0].mean() / t[:, 1].mean():.3f}, scaled {t[:, 2].mean() / t[:, 3].mean():.3f}")


if __name__ == "__main__":
    main()
