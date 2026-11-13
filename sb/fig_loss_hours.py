"""Figure: where v11's loss falls in the day (30 training scenarios, full length).

Share of each climate group's total loss per local hour, split into comfort and energy + carbon. Local hour is
aligned on the occupancy onset (first arrivals at 06:00), which falls on the same step in every episode.

    python -m sb.fig_loss_hours --runs D:/SmartBuildings_data/results/dev11_8640/v11f --out docs/fig/fig_loss_hours.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SURFACE, TEXT, TEXT2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
ENERGY, COMFORT = "#2a78d6", "#eb6834"   # categorical slots 1 and 2 (validated: CVD dE 24.7, normal 33.6)
COLD = ("denver", "fairbanks")


def hourly(runs: Path):
    acc = {g: np.zeros((2, 24)) for g in ("cold", "warm")}
    for f in sorted(runs.glob("*.npy")):
        a = np.load(f)                        # reward, prod regret, energy, carbon, total occupancy
        k = np.arange(len(a)) % 288
        occ = a[:, 4] > 0
        onsets = np.flatnonzero(occ[1:] & ~occ[:-1]) + 1
        vals, cnt = np.unique(onsets % 288, return_counts=True)
        hour = ((k - vals[np.argmax(cnt)] + 72) % 288) // 12   # step of the usual onset = 06:00
        g = "cold" if any(s in f.stem for s in COLD) else "warm"
        np.add.at(acc[g][0], hour, -0.6 * a[:, 1])
        np.add.at(acc[g][1], hour, 0.2 * (a[:, 2] + a[:, 3]))
    return {g: v / v.sum() * 100 for g, v in acc.items()}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="D:/SmartBuildings_data/results/dev11_8640/v11f")
    ap.add_argument("--out", default="docs/fig/fig_loss_hours.png")
    a = ap.parse_args(argv)
    shares = hourly(Path(a.runs))
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": TEXT2,
                         "xtick.color": TEXT2, "ytick.color": TEXT2, "text.color": TEXT})
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True, facecolor=SURFACE)
    x = np.arange(24)
    titles = {"cold": "Cold: Denver, Fairbanks (12 scenarios)",
              "warm": "Warm: Atlanta, Phoenix, Singapore (18 scenarios)"}
    for ax, g in zip(axes, ("cold", "warm")):
        comfort, energy = shares[g]
        ax.set_facecolor(SURFACE)
        ax.bar(x, energy, width=0.72, color=ENERGY, edgecolor=SURFACE, linewidth=0.8, label="energy + carbon")
        ax.bar(x, comfort, bottom=energy, width=0.72, color=COMFORT, edgecolor=SURFACE, linewidth=0.8,
               label="comfort")
        ax.set_title(titles[g], fontsize=8.5, color=TEXT, loc="left")
        ax.set_xticks([0, 3, 6, 8, 12, 19, 23])
        ax.set_xticklabels(["0", "3", "6", "8", "12", "19", "23"])
        ax.set_xlabel("local hour")
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0)
        t = comfort + energy
        label = (f"03-08 h: {t[3:8].sum():.0f} %\n08-19 h: {t[8:19].sum():.0f} %\n"
                 f"19-03 h: {t[19:].sum() + t[:3].sum():.0f} %")
        ax.text(23.4, 11.6, label, ha="right", va="top", fontsize=8, color=TEXT)
    axes[0].set_ylabel("share of loss (%)")
    axes[0].set_ylim(0, 12.5)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="upper center", ncol=2, fontsize=8, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=300, facecolor=SURFACE)
    for g in ("cold", "warm"):
        c, e = shares[g]
        t = c + e
        print(g, "03-08 h", round(t[3:8].sum(), 1), "08-19 h", round(t[8:19].sum(), 1),
              "19-03 h", round(t[19:].sum() + t[:3].sum(), 1), "comfort", round(c.sum(), 1))


if __name__ == "__main__":
    main()
