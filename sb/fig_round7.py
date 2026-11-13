"""Round 7 figure (docs/RESULTS_ROUND7.md): (a) change of the ten-day loss per blind building, v16 against v15, split
into comfort and energy; (b) the zone of the Chicago building whose planned heat flips most often under v15, on its
worst day, under both versions (trace dumps of sb/run_r7_traces.py).

    python -m sb.fig_round7 docs/fig/fig_round7.png
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
RES = DATA / "results/round7"
DIAG = DATA / "results/round7_diag"
BLUE, GREY, ORANGE, TEXT, TEXT2, GRID, SURFACE = "#2a78d6", "#9aa3ad", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
LABEL = {"duluth_feb19": "Duluth, February", "helena_feb19": "Helena, February", "newyork_jan29": "New York, January",
         "chicago_dec03": "Chicago, December", "seattle_nov26": "Seattle, November",
         "sanfrancisco_mar05": "San Francisco, March"}


def terms(f: Path) -> tuple[float, float, float]:
    a = np.load(f).astype(float)
    return -a[:, 0].mean(), -0.6 * a[:, 1].mean(), 0.2 * (a[:, 2].mean() + a[:, 3].mean())


def start_of(name: str) -> str:
    b, w = name.split("__")
    txt = (DATA / "round7/scenarios" / b / w / "config.gin").read_text()
    return re.search(r"start_timestamp\s*=\s*'([^']+)'", txt).group(1)


def flips(q: np.ndarray) -> np.ndarray:
    s = np.sign(np.where(np.abs(q) > 0.5, q, 0.0))
    return sum(((s[k:] * s[:-k]) < 0).sum(0) for k in (1, 2, 3))


def main(out: str) -> None:
    scen = sorted(f.stem for f in (RES / "v15").glob("*.npy"))
    order = sorted(scen, key=lambda s: terms(RES / "chm" / f"{s}.npy")[0] / terms(RES / "v15" / f"{s}.npy")[0])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.7), gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.5})
    fig.patch.set_facecolor(SURFACE)
    for ax in (ax1, ax2):
        ax.set_facecolor(SURFACE)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=7, colors=TEXT2)

    # (a) change per building, as a share of v15's loss: comfort part and energy part
    y = np.arange(len(order))[::-1]
    dc, de = [], []
    for s in order:
        l0, c0, e0 = terms(RES / "v15" / f"{s}.npy")
        l1, c1, e1 = terms(RES / "chm" / f"{s}.npy")
        dc.append(100 * (c1 - c0) / l0)
        de.append(100 * (e1 - e0) / l0)
    dc, de = np.array(dc), np.array(de)
    ax1.barh(y, de, color=BLUE, height=0.6, label="energy")
    ax1.barh(y, dc, left=np.where(dc < 0, de, 0), color=ORANGE, height=0.6, label="comfort")
    ax1.set_yticks(y, [LABEL[s.split("__")[1]] for s in order], fontsize=7.5)
    ax1.axvline(0, color=TEXT2, lw=0.8)
    for yi, v in zip(y, dc + de):
        ax1.text(min(v, 0) - 0.4, yi, f"{v:.1f}", va="center", ha="right", fontsize=7, color=TEXT)
    ax1.set_xlim(min(dc + de) * 1.3, 1.5)
    ax1.set_xlabel("change of the ten-day loss, v16 vs v15 (% of v15)", fontsize=7.5, color=TEXT)
    ax1.grid(axis="x", color=GRID, lw=0.6)
    ax1.set_axisbelow(True)
    ax1.legend(frameon=False, fontsize=7, loc="lower left")
    ax1.set_title("a   Change per building", loc="left", fontsize=8.5, weight="bold", color=TEXT)

    # (b) the most-flipping zone of the Chicago building under v15, on its worst day
    name = "building_7804__chicago_dec03"
    v15, v16 = np.load(DIAG / f"v15__{name}.npz"), np.load(DIAG / f"chm__{name}.npz")
    z = int(np.argmax(flips(v15["p_q"])))
    s = np.sign(np.where(np.abs(v15["p_q"][:, z]) > 0.5, v15["p_q"][:, z], 0.0))
    per_day = np.add.reduceat(((s[1:] * s[:-1]) < 0).astype(int), np.arange(0, len(s) - 1, 288))
    d = int(np.argmax(per_day))
    k = np.arange(d * 288, min((d + 1) * 288, len(s)))
    hours = (k - d * 288) * 5 / 60
    ax2.fill_between(hours, v15["lo"][k, z] - 273.15, v15["hi"][k, z] - 273.15, color="#d6ecdf", lw=0, zorder=0,
                     label="band")
    ax2.plot(hours, v15["T"][k, z] - 273.15, color=GREY, lw=0.8, label="v15", zorder=2)
    ax2.plot(hours, v16["T"][k, z] - 273.15, color=BLUE, lw=1.2, label="v16", zorder=3)
    ax2.set_xlim(0, 24)
    ax2.set_ylim(None, 35)
    ax2.set_xticks([0, 6, 12, 18, 24], ["06:00", "12:00", "18:00", "00:00", "06:00"])
    day = pd.Timestamp(start_of(name)) + pd.Timedelta(days=d)
    ax2.set_xlabel(f"{day:%A %d %B} (day {d + 1} of the window)", fontsize=7.5, color=TEXT)
    ax2.set_ylabel("zone temperature (°C)", fontsize=7.5, color=TEXT)
    ax2.grid(color=GRID, lw=0.5)
    ax2.legend(frameon=False, fontsize=7, loc="upper left", ncol=3)
    ax2.set_title("b   Chicago: the zone that cycled most", loc="left", fontsize=8.5, weight="bold", color=TEXT)
    fig.subplots_adjust(left=0.18, right=0.98, top=0.88, bottom=0.2)
    fig.savefig(out, dpi=300, facecolor=SURFACE)
    print("wrote", out, "| zone", z, "day", d + 1, "flips that day", int(per_day[d]),
          "| flips v15", int(flips(v15["p_q"])[z]), "v16", int(flips(v16["p_q"])[z]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/fig/fig_round7.png")
