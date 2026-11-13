"""Figure: the Monday-morning recovery of a large room on a full-size building (docs/BIGDEV.md, diagnosis 2).

Building 7407 at full size in Chicago, Sunday 06:00 to Monday 18:00 of the second week (sb/bigbld_dump.py traces).
Top: the zone's air temperature and the controller's slab estimate, with the comfort band in occupied time. Bottom:
the box's airflow against its 2 m3/s maximum. One trace per controller (v14 always, v15 when its dump exists).

    python -m sb.fig_monday --zone VAV_36 --out docs/fig/fig_monday.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SURFACE, TEXT, TEXT2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SLOT1, SLOT2 = "#2a78d6", "#eb6834"   # categorical slots 1 and 2 (validated: CVD dE 24.7, normal 33.6)
BAND = "#e9e8e4"
D = Path("D:/SmartBuildings_data/results/bigbld_diag")
# v14, then v15 if a candidate passed its checks, else the rejected candidate A (slab-limited setback).
TRACES = [("v14", D / "v14_7407_chicago_full_d8.npz", SLOT1, "-")]
if (D / "v15_7407_chicago_full_d8.npz").exists():
    TRACES.append(("v15", D / "v15_7407_chicago_full_d8.npz", SLOT2, "-"))
else:
    TRACES.append(("candidate A (rejected)", D / "v15A_7407_chicago_full_d8.npz", SLOT2, "-"))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone", default="VAV_36")
    ap.add_argument("--out", default="docs/fig/fig_monday.png")
    a = ap.parse_args(argv)
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": TEXT2,
                         "xtick.color": TEXT2, "ytick.color": TEXT2, "text.color": TEXT})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 3.9), sharex=True, facecolor=SURFACE,
                                   gridspec_kw={"height_ratios": [2.2, 1.0]})
    first = True
    for name, f, color, ls in TRACES:
        if not f.exists():
            continue
        d = dict(np.load(f))
        z = list(d["vids"]).index(a.zone)
        area = d["area"][z] * float(d["cv_m"]) ** 2
        h = (np.arange(len(d["T"])) / 12.0)          # hours since Sunday 06:00
        T = d["T"][:, z] - 273.15
        if first:
            occ = d["occ_total"] > 0
            lo, hi = d["lo"][:, z] - 273.15, d["hi"][:, z] - 273.15
            comfort = np.isclose(lo, lo.max())
            ax1.fill_between(h, lo, hi, where=comfort, color=BAND, step="mid", lw=0, label="comfort band")
            for ax in (ax1, ax2):
                ax.set_facecolor(SURFACE)
                ax.grid(axis="y", color=GRID, lw=0.6)
                for s in ax.spines.values():
                    s.set_visible(False)
            ax2.axhline(float(d["vmax"][0, z]), color=TEXT2, lw=0.8, ls=":")
            ax2.text(0.3, float(d["vmax"][0, z]) - 0.18, "box maximum", fontsize=7.5, color=TEXT2)
            first = False
        ax1.plot(h, T, color=color, lw=1.6, ls=ls, label=f"{name}: room air")
        if "p_tm" in d:
            ax1.plot(h, d["p_tm"][:, z] - 273.15, color=color, lw=1.0, ls="--", label=f"{name}: slab (model)")
        ax2.plot(h, d["flow"][:, z], color=color, lw=1.4, ls=ls, label=name)
    ax1.set_ylabel("temperature (°C)")
    ax2.set_ylabel("airflow (m³/s)")
    ax2.set_xlabel("hours from Sunday 06:00")
    ticks = [0, 6, 12, 18, 24, 30, 36]
    ax2.set_xticks(ticks)
    ax2.set_xticklabels(["Sun 06", "12", "18", "Mon 00", "06", "12", "18"])
    ax1.legend(loc="upper left", fontsize=7.5, frameon=False, ncol=2)
    ax1.set_title(f"Building 7407 at full size, Chicago: one room of {area:.0f} m² on a 2 m³/s box",
                  fontsize=8.5, color=TEXT, loc="left")
    fig.tight_layout()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    print("wrote", out)


if __name__ == "__main__":
    main()
