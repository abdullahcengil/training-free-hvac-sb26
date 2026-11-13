"""Round 6 figure (docs/RESULTS_ROUND6.md): (a) change of the ten-day loss per blind scenario, v15 against v14;
(b) daily loss in one of them (Chicago, Thanksgiving week), showing the holiday's saving and the next day's payback.

    python -m sb.fig_round6 docs/fig/fig_round6.png
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA = Path("D:/SmartBuildings_data")
RES = DATA / "results/round6h"
ROOT = DATA / "round6h/scenarios"
BLUE, GREY, TEXT, TEXT2, GRID, SURFACE = "#2a6fdb", "#9aa3ad", "#1f2328", "#59636e", "#e3e6ea", "#fcfcfb"
LABEL = {"houston_may28": "Houston, Memorial Day", "miami_jul02": "Miami, Independence Day",
         "dubai_sep03": "Dubai, Labor Day", "newyork_oct08": "New York, Columbus Day",
         "chicago_nov19": "Chicago, Thanksgiving", "duluth_dec17": "Duluth, Christmas"}


def start(b: str, w: str) -> pd.Timestamp:
    txt = (ROOT / b / w / "config.gin").read_text()
    return pd.Timestamp(re.search(r"start_timestamp\s*=\s*'([^']+)'", txt).group(1))


def main(out: str) -> None:
    scen = sorted(f.stem for f in (RES / "v14").glob("*.npy"))
    loss = {arm: {s: -np.load(RES / arm / f"{s}.npy").astype(float)[:, 0] for s in scen} for arm in ("v14", "ed1")}
    ch = {s: 100 * (loss["ed1"][s].mean() / loss["v14"][s].mean() - 1) for s in scen}
    order = [s for s in scen]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": TEXT2,
                         "axes.labelcolor": TEXT, "xtick.color": TEXT2, "ytick.color": TEXT2})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.7), gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.45})
    fig.patch.set_facecolor(SURFACE)
    for ax in (ax1, ax2):
        ax.set_facecolor(SURFACE)
        ax.spines[["top", "right"]].set_visible(False)

    # (a) change per scenario
    y = np.arange(len(order))[::-1]
    vals = [ch[s] for s in order]
    ax1.barh(y, vals, color=BLUE, height=0.6)
    ax1.set_yticks(y, [LABEL[s.split("__")[1]] for s in order])
    ax1.axvline(0, color=TEXT2, lw=0.8)
    ax1.set_xlabel("change of the ten-day loss, v15 vs v14 (%)")
    ax1.grid(axis="x", color=GRID, lw=0.6)
    ax1.set_axisbelow(True)
    for yi, v in zip(y, vals):
        ax1.text(v - 0.15, yi, f"{v:.1f}", va="center", ha="right", fontsize=7.5, color=TEXT)
    ax1.set_xlim(min(vals) * 1.35, 0.5)
    ax1.set_title("a   Change per building", loc="left", fontsize=9, weight="bold", color=TEXT)

    # (b) daily loss, Chicago (Thanksgiving on Thursday)
    s = next(x for x in scen if x.endswith("chicago_nov19"))
    b, w = s.split("__")
    t0 = start(b, w)
    n = len(loss["v14"][s])
    days = (t0 + pd.to_timedelta(np.arange(n) * 5, unit="min")).normalize()
    uniq = sorted(set(days))
    dv14 = np.array([loss["v14"][s][days == d].sum() for d in uniq])
    ded1 = np.array([loss["ed1"][s][days == d].sum() for d in uniq])
    x = np.arange(len(uniq))
    ax2.bar(x - 0.2, dv14, width=0.38, color=GREY, label="v14")
    ax2.bar(x + 0.2, ded1, width=0.38, color=BLUE, label="v15")
    ax2.set_xticks(x, [d.strftime("%a")[:2] for d in uniq], fontsize=7.5)
    top = max(dv14.max(), ded1.max())
    ax2.set_ylim(0, top * 1.18)
    hol = [i for i, d in enumerate(uniq) if d == pd.Timestamp("2023-11-23")]
    for i in hol:
        ax2.axvspan(i - 0.5, i + 0.5, color=GRID, zorder=0)
        ax2.text(i, top * 1.1, "holiday", ha="center", va="center", fontsize=7.5, color=TEXT2)
    ax2.set_ylabel("loss per day")
    ax2.set_xlabel("19-29 November 2023")
    ax2.grid(axis="y", color=GRID, lw=0.6)
    ax2.set_axisbelow(True)
    ax2.legend(frameon=False, loc="upper left", fontsize=7.5, ncol=1)
    ax2.set_title("b   Chicago, Thanksgiving week", loc="left", fontsize=9, weight="bold", color=TEXT)
    fig.subplots_adjust(left=0.25, right=0.98, top=0.88, bottom=0.2, wspace=0.45)
    fig.savefig(out, dpi=300, facecolor=SURFACE)
    print("wrote", out)
    for d, a1, a2 in zip(uniq, dv14, ded1):
        print(d.date(), round(a1, 3), round(a2, 3))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/fig/fig_round6.png")
