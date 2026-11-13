"""Building-level version of sb/stats.py (added 8 Nov 2026 after an AI review): scenarios that share a building are
averaged, so each building is one observation; sign test and a cluster bootstrap (10,000 resamples of buildings, seed 0)
over buildings. Only comparisons with more than one scenario per building appear. Writes docs/RESULTS_STATS_BUILDINGS.md.

    python -m sb.stats_buildings
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import stats

from sb.evaluate_prereg import load
from sb.stats import COLD_STATIONS, COMPARISONS, STRESS_WINDOWS, folder, losses


def keys_for(fold: str, ours: str, filt: str | None) -> list[str]:
    keys = sorted(load(folder(fold, ours)))
    if filt in ("cold_st", "warm_st"):
        cold = [any(c in k.split("__")[1] for c in COLD_STATIONS) for k in keys]
        keys = [k for k, c in zip(keys, cold) if c == (filt == "cold_st")]
    elif filt == "warm":
        keys = [k for k in keys if not k.endswith("_dec")]
    elif filt in ("train30", "stress40"):
        keys = [k for k in keys if k.endswith(STRESS_WINDOWS) == (filt == "stress40")]
    elif filt:
        keys = [k for k in keys if k.endswith(filt)]
    return keys


def main() -> None:
    rng = np.random.default_rng(0)
    lines = ["# Paired statistics by building (descriptive)", "",
             "As docs/RESULTS_STATS.md, but scenarios on the same building are averaged first, so that each building "
             "counts once. Reduction = 1 - mean(ours)/mean(reference). Bootstrap: 10,000 resamples of buildings, seed "
             "0. Sign test two-sided over buildings, ties dropped. Written by `sb/stats_buildings.py`.", "",
             "| comparison | scenarios | buildings | better / same / worse | reduction | bootstrap 95 % CI | sign test p |",
             "|---|---|---|---|---|---|---|"]
    for label, fold, ours, ref, filt in COMPARISONS:
        keys = keys_for(fold, ours, filt)
        names = [k.split("__")[0] for k in keys]
        blds = sorted(set(names))
        if len(blds) == len(keys):
            continue
        x, y = losses(folder(fold, ours), keys), losses(folder(fold, ref), keys)
        xb = np.array([x[[n == b for n in names]].mean() for b in blds])
        yb = np.array([y[[n == b for n in names]].mean() for b in blds])
        tie = np.isclose(xb, yb, rtol=1e-9, atol=0)
        better, worse, same = int(np.sum((xb < yb) & ~tie)), int(np.sum((xb > yb) & ~tie)), int(np.sum(tie))
        red = 1 - xb.mean() / yb.mean()
        idx = rng.integers(0, len(blds), size=(10000, len(blds)))
        boot = 1 - xb[idx].mean(1) / yb[idx].mean(1)
        lo, hi = np.percentile(boot, [2.5, 97.5])
        n_eff = better + worse
        p = stats.binomtest(better, n_eff, 0.5).pvalue if n_eff else float("nan")
        lines.append(f"| {label} | {len(keys)} | {len(blds)} | {better} / {same} / {worse} | {red:.1%} | "
                     f"{lo:.1%} to {hi:.1%} | {p:.2g} |")
    Path("docs/RESULTS_STATS_BUILDINGS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
