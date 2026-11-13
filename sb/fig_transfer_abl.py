"""Transfer ablation figure (docs/TRANSFER_ABLATION.md): (a) loss of each arm relative to v16 on the twelve full-size
unseen buildings of rounds 6 and 7, per scenario and as the ratio of means with its bootstrap interval; (b) the same
ratio day by day (summed over the scenarios), to show how fast learning makes up for wrong priors.

    python -m sb.fig_transfer_abl docs/fig/fig_transfer_abl.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

from sb.run_transfer_abl import ARMS, OUT, SETS, STEPS, scenarios

SURFACE, TEXT, TEXT2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
# Categorical slots 1-5 of the dataviz reference palette (validated, light surface), in fixed order.
COLOR = {"nolearn": "#2a78d6", "offset": "#eb6834", "half": "#1baf7a", "double": "#eda100", "nodelay": "#e87ba4"}
LABEL = {"nolearn": "no online learning", "offset": "offset learned only", "half": "priors halved",
         "double": "priors doubled", "nodelay": "no delay compensation"}


def pairs(arm: str) -> list[tuple[np.ndarray, np.ndarray]]:
    out = []
    for name, root, rdir in SETS:
        for s in scenarios(root):
            f = OUT / f"{name}_{arm}" / f"{s}.npy"
            if f.exists():
                out.append((-np.load(rdir / f"{s}.npy").astype(float)[:STEPS, 0],
                            -np.load(f).astype(float)[:STEPS, 0]))
    return out


def main(out: str) -> None:
    arms = [a for a in ARMS if pairs(a)]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.6), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.75})
    fig.patch.set_facecolor(SURFACE)
    for ax in (ax1, ax2):
        ax.set_facecolor(SURFACE)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=7, colors=TEXT2)
        ax.grid(color=GRID, lw=0.6)
        ax.set_axisbelow(True)

    ticks = [0.9, 1, 1.25, 1.5, 2, 3, 5, 8]

    def log_axis(axis, lo: float, hi: float, ticks: list[float] = ticks) -> None:
        axis.set_major_locator(FixedLocator([t for t in ticks if lo <= t <= hi]))
        axis.set_major_formatter(FixedFormatter([f"{t:g}" for t in ticks if lo <= t <= hi]))
        axis.set_minor_locator(NullLocator())

    # (a) per scenario (small dots) and ratio of means with its 95 % bootstrap interval (bar)
    y = np.arange(len(arms))[::-1]
    rng = np.random.default_rng(0)
    rmax = 1.0
    for yi, arm in zip(y, arms):
        p = pairs(arm)
        ref, new = np.array([a.mean() for a, _ in p]), np.array([b.mean() for _, b in p])
        r = new / ref
        rmax = max(rmax, r.max())
        ax1.scatter(r, yi + rng.uniform(-0.15, 0.15, len(r)), s=9, color=COLOR[arm], alpha=0.6, lw=0, zorder=2)
        idx = rng.integers(0, len(ref), size=(10000, len(ref)))
        lo, hi = np.percentile(new[idx].mean(axis=1) / ref[idx].mean(axis=1), [2.5, 97.5])
        m = new.mean() / ref.mean()
        ax1.plot([lo, hi], [yi, yi], color=TEXT, lw=1.6, zorder=3)
        ax1.plot([m], [yi], marker="o", ms=5, color=TEXT, mec=SURFACE, mew=1.2, zorder=4)
        ax1.text(m, yi + 0.36, f"{m:.2f}", fontsize=7, color=TEXT, va="center", ha="center",
                 bbox=dict(boxstyle="round,pad=0.12", fc=SURFACE, ec="none"), zorder=5)
    ax1.axvline(1, color=TEXT2, lw=0.8)
    ax1.set_xscale("log")
    ax1.set_xlim(0.8, rmax * 1.15)
    log_axis(ax1.xaxis, 0.8, rmax * 1.15, [1, 1.5, 2, 3, 5, 8])
    ax1.set_ylim(-0.6, len(arms) - 0.4)
    ax1.set_yticks(y, [LABEL[a] for a in arms], fontsize=7.5)
    ax1.grid(axis="y", visible=False)
    ax1.set_xlabel("loss relative to v16 (log scale; dots: buildings)", fontsize=7.5, color=TEXT)
    ax1.set_title("a   One part changed", loc="left", fontsize=8.5, weight="bold", color=TEXT)

    # (b) day-by-day ratio of summed losses; every window starts on a Sunday at 06:00
    days = np.arange(1, STEPS // 288 + 1)
    names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for d in days:
        if names[(d - 1) % 7] in ("Sat", "Sun"):
            ax2.axvspan(d - 0.5, d + 0.5, color=GRID, alpha=0.6, lw=0, zorder=0)
    vmax = 1.0
    for arm in arms:
        p = pairs(arm)
        a = sum(x.reshape(-1, 288).sum(axis=1) for x, _ in p)
        b = sum(x.reshape(-1, 288).sum(axis=1) for _, x in p)
        vmax = max(vmax, (b / a).max())
        ax2.plot(days, b / a, color=COLOR[arm], lw=2, marker="o", ms=3, label=LABEL[arm], zorder=3)
    ax2.axhline(1, color=TEXT2, lw=0.8)
    ax2.set_yscale("log")
    ax2.set_ylim(0.85, vmax * 1.12)
    log_axis(ax2.yaxis, 0.85, vmax * 1.12)
    ax2.set_xlim(0.5, days[-1] + 0.5)
    ax2.set_xticks(days, [names[(d - 1) % 7] for d in days], fontsize=6.5)
    ax2.grid(axis="x", visible=False)
    ax2.set_xlabel("day of the window (from 06:00; shaded: weekend)", fontsize=7.5, color=TEXT)
    ax2.set_ylabel("loss relative to v16 that day", fontsize=7.5, color=TEXT)
    ax2.legend(frameon=False, fontsize=6.5, loc="center left", bbox_to_anchor=(1.01, 0.5))
    ax2.set_title("b   Day by day, summed over the buildings", loc="left", fontsize=8.5, weight="bold", color=TEXT)
    fig.savefig(out, dpi=250, bbox_inches="tight", facecolor=SURFACE)
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/fig/fig_transfer_abl.png")
