"""Paired statistics for the pre-registered rounds (descriptive; no new hypotheses).

For each comparison: per-scenario wins, a two-sided sign test, a Wilcoxon
signed-rank test on the per-scenario losses, and a bootstrap 95 % interval
(10,000 resamples of scenarios, fixed seed) for the relative reduction of the
mean score. Writes docs/RESULTS_STATS.md.

    python -m sb.stats
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy import stats

from sb.evaluate_prereg import load

R = Path("D:/SmartBuildings_data/results")
COMPARISONS = [  # (round label, folder, ours, reference, scenario filter)
    ("Round 1 (pre-registered): v7 vs pid_water", "heldout", "zonal", "pid_water", None),
    ("Round 1, post hoc: v8 vs pid_water", "heldout", "v8_posthoc", "pid_water", None),
    ("Round 2 (pre-registered): v8 vs v7", "heldout2", "v8", "v7", None),
    ("Round 2 (pre-registered): v8 vs pid_water", "heldout2", "v8", "pid_water", None),
    ("Round 3 (pre-registered): v9 vs v8, cold", "heldout3", "v9", "v8", "_dec"),
    ("Round 3 (pre-registered): v9 vs v8, warm", "heldout3", "v9", "v8", "warm"),
    ("Round 3 (pre-registered): v9 vs pid_water", "heldout3", "v9", "pid_water", None),
    ("Training, 30 scenarios: v9 vs v8", "train_8640", "v9f", "v8", None),
    ("Round 4 (pre-registered): v10 vs v9, warm", "heldout4", "v10", "v9", "warm_st"),
    ("Round 4 (pre-registered): v10 vs v9, cold", "heldout4", "v10", "v9", "cold_st"),
    ("Round 4 (pre-registered): v10 vs v9", "heldout4", "v10", "v9", None),
    ("Round 4 (pre-registered): v10 vs pid_water", "heldout4", "v10", "pid_water", None),
    ("Training, 30 scenarios: v10 vs v9", "train_8640", "v10c", "v9f", None),
    ("Round 5 (pre-registered): v11 vs v10", "heldout5", "v11", "v10", None),
    ("Round 5 (pre-registered): v11 vs v10, cold", "heldout5", "v11", "v10", "cold_st"),
    ("Round 5 (pre-registered): v11 vs v10, warm", "heldout5", "v11", "v10", "warm_st"),
    ("Round 5 (pre-registered): v11 vs pid_water", "heldout5", "v11", "pid_water", None),
    ("Training, 30 scenarios: v11 vs v10", "train_8640", "/dev11_8640/v11f", "v10c", None),
    ("Round 6 (pre-registered, ten days): v15 vs v14", "round6h", "ed1", "v14", None),
    ("Round 6, pid_water run after the round: v15 vs pid_water", "round6h", "ed1", "pid_water", None),
    ("Training, 30 scenarios: v15 vs v14", "holiday", "ed1_full", "/dev14_8640/of3", "train30"),
    ("Stress, 40 windows: v15 vs v14", "holiday", "ed1_full", "/dev14_8640/of3", "stress40"),
    ("Round 7 (pre-registered, ten days): v16 vs v15", "round7", "chm", "v15", None),
    ("Round 7, pid_water run after the round: v16 vs pid_water", "round7", "chm", "pid_water", None),
    ("Training, 30 scenarios: v16 vs v15", "chatter", "t_chm", "/holiday/ed1_full", "train30"),
    # Appended 8 Nov 2026 (at the end, so that the seeded intervals above do not change).
    ("Round 8 (pre-registered, ten days): candidate vs v16", "round8", "sp1", "v16", None),
    ("Round 8, pid_water run after the round: v16 vs pid_water", "round8", "v16", "pid_water", None),
]
STRESS_WINDOWS = ("_jan15", "_jul15")   # the stress windows of docs/STRESS_TEST.md; training windows end in a digit
COLD_STATIONS = ("fairbanks", "denver", "minneapolis")


def folder(fold: str, name: str) -> Path:
    """A run folder: name inside the round's folder, or a path under R when it starts with '/'."""
    return R / name.lstrip("/") if name.startswith("/") else R / fold / name


def losses(folder: Path, keys: list[str]) -> np.ndarray:
    runs = load(folder)
    return np.array([abs(runs[k]["mean_reward"]) for k in keys])


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/RESULTS_STATS.md")
    a = ap.parse_args(argv)
    rng = np.random.default_rng(0)
    lines = ["# Paired statistics (descriptive)", "",
             "Loss = mean |reward| per step (lower is better). Reduction = 1 - mean(ours)/mean(reference). "
             "Sign test and Wilcoxon signed-rank test are two-sided, over scenarios; ties (identical runs) are "
             "dropped from both tests. Bootstrap: 10,000 resamples of scenarios, seed 0. Written by `sb/stats.py`.",
             "",
             "| comparison | n | better / same / worse | reduction | bootstrap 95 % CI | sign test p | Wilcoxon p |",
             "|---|---|---|---|---|---|---|"]
    for label, fold, ours, ref, filt in COMPARISONS:
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
        x, y = losses(folder(fold, ours), keys), losses(folder(fold, ref), keys)
        d = x - y
        tie = np.isclose(x, y, rtol=1e-9, atol=0)
        better, worse, same = int(np.sum((d < 0) & ~tie)), int(np.sum((d > 0) & ~tie)), int(np.sum(tie))
        red = 1 - x.mean() / y.mean()
        idx = rng.integers(0, len(x), size=(10000, len(x)))
        boot = 1 - x[idx].mean(1) / y[idx].mean(1)
        lo, hi = np.percentile(boot, [2.5, 97.5])
        n_eff = better + worse
        p_sign = stats.binomtest(better, n_eff, 0.5).pvalue if n_eff else float("nan")
        p_wil = stats.wilcoxon(x[~tie], y[~tie]).pvalue if n_eff >= 1 else float("nan")
        lines.append(f"| {label} | {len(x)} | {better} / {same} / {worse} | {red:.1%} | {lo:.1%} to {hi:.1%} | "
                     f"{p_sign:.2g} | {p_wil:.2g} |")
    lines += ["", "With 6 to 12 scenarios per round these tests are coarse; they are reported to show how "
              "much of each difference could be chance, not as new hypotheses."]
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
