"""Figure: Monday recovery of a large room in deep cold at full size (docs/BIG_BUILDINGS.md, deep-cold diagnosis).

Building 7407 at full size, Fairbanks from 21 Nov 2023: the trace starts on a Tuesday at 06:00, so steps 1440-1872 are
Sunday 06:00 to Monday 18:00. Top: room air temperature with the comfort band in comfort time; bottom: the box's
airflow against its 2 m3/s maximum. One line per trace given (sb/bigbld_dump.py records).

    python -m sb.fig_monday_cold --trace v14=D:/SmartBuildings_data/results/coldsize_diag/v14_7407_fairbanks_nov21_full.npz \
        --trace v15=D:/SmartBuildings_data/results/coldsize_diag/v15_7407_fairbanks_nov21_full.npz --out docs/fig/fig_monday_cold.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sb.fig_monday import BAND, GRID, SLOT1, SLOT2, SURFACE, TEXT, TEXT2


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", action="append", required=True, help="label=path, in drawing order")
    ap.add_argument("--zone", default="VAV_36")
    ap.add_argument("--start", type=int, default=1440)
    ap.add_argument("--end", type=int, default=1872)
    ap.add_argument("--out", default="docs/fig/fig_monday_cold.png")
    a = ap.parse_args(argv)
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": TEXT2,
                         "xtick.color": TEXT2, "ytick.color": TEXT2, "text.color": TEXT})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 3.9), sharex=True, facecolor=SURFACE,
                                   gridspec_kw={"height_ratios": [2.2, 1.0]})
    sl = slice(a.start, a.end)
    first = True
    for (label, path), color in zip((t.split("=", 1) for t in a.trace), (SLOT1, SLOT2)):
        d = dict(np.load(path))
        z = list(d["vids"]).index(a.zone)
        area = d["area"][z] * float(d["cv_m"]) ** 2
        h = np.arange(a.end - a.start) / 12.0
        if first:
            lo, hi = d["lo"][sl, z] - 273.15, d["hi"][sl, z] - 273.15
            comfort = np.isclose(lo, lo.max())
            ax1.fill_between(h, lo, hi, where=comfort, color=BAND, step="mid", lw=0, label="comfort band")
            for ax in (ax1, ax2):
                ax.set_facecolor(SURFACE)
                ax.grid(axis="y", color=GRID, lw=0.6)
                for s in ax.spines.values():
                    s.set_visible(False)
            vmax = float(d["vmax"][a.start, z])
            ax2.axhline(vmax, color=TEXT2, lw=0.8, ls=":")
            ax2.text(0.3, vmax - 0.2, "box maximum", fontsize=7.5, color=TEXT2)
            oat = float(np.mean(d["oat"][sl])) - 273.15
            first = False
        ax1.plot(h, d["T"][sl, z] - 273.15, color=color, lw=1.6, label=f"{label}: room air")
        ax2.plot(h, d["flow"][sl, z], color=color, lw=1.4, label=label)
    ax1.set_ylabel("temperature (°C)")
    ax2.set_ylabel("airflow (m³/s)")
    ax2.set_xlabel("hours from Sunday 06:00")
    ax2.set_xticks([0, 6, 12, 18, 24, 30, 36])
    ax2.set_xticklabels(["Sun 06", "12", "18", "Mon 00", "06", "12", "18"])
    ax1.legend(loc="upper left", fontsize=7.5, frameon=False, ncol=2)
    ax1.set_title(f"Building 7407 at full size, Fairbanks (outside {oat:.0f} °C on average): one room of "
                  f"{area:.0f} m² on a 2 m³/s box", fontsize=8.5, color=TEXT, loc="left")
    fig.tight_layout()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    print("wrote", out)


if __name__ == "__main__":
    main()
