"""Figure: the heat the controller adds to a zone around the moment a person leaves or arrives (sb/occ_dump.py traces).

Each person gives off 70 W in their zone, so after a departure the zone needs about 70 W more from the HVAC and after
an arrival about 70 W less. Plotted: the zone's planned heat relative to the mean of all zones at the same step, minus
its own value over the six steps before the event, averaged over events, with one standard error.

    python -m sb.fig_occ docs/fig/fig_occ.png D:/SmartBuildings_data/results/occdump/b8_fairbanks_8.npz \
        D:/SmartBuildings_data/results/occdump/b8_phoenix_4.npz
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#1f2328", "#6e7781"
W = np.arange(-6, 19)


def _events(occ, hour, sign):
    n, nz = occ.shape
    out = []
    for k in range(30, n - 30):
        for z in range(nz):
            if sign < 0 and occ[k, z] < occ[k - 1, z] - 0.5 and 13 <= hour[k] < 19.5:
                out.append((k, z))
            if sign > 0 and occ[k, z] > occ[k - 1, z] + 0.5:
                out.append((k, z))
    return out


def _eta(x, events):
    v = np.array([[x[k + L, z] - x[k + L].mean() for L in W] for k, z in events])
    v -= v[:, W < 0].mean(1, keepdims=True)          # each event relative to its own six steps before
    return v.mean(0), v.std(0) / np.sqrt(len(v)), len(v)


def main(out: str, *paths: str) -> None:
    fig, axes = plt.subplots(1, len(paths), figsize=(7.0, 2.5), sharey=True)
    for ax, path in zip(np.atleast_1d(axes), paths):
        d = np.load(path)
        q = d["q"] * 1000.0          # W
        for sign, color, label in ((-1, BLUE, "departures"), (1, ORANGE, "arrivals")):
            m, se, n = _eta(q, _events(d["occ"], d["hour"], sign))
            ax.fill_between(W, m - se, m + se, color=color, alpha=0.18, lw=0)
            ax.plot(W, m, color=color, lw=1.6, label=f"{label} (n = {n})")
        for y in (70, -70):
            ax.axhline(y, color=MUTED, lw=0.8, ls=(0, (4, 3)))
        ax.axhline(0, color=MUTED, lw=0.6)
        ax.axvline(0, color=MUTED, lw=0.6)
        name = Path(path).stem.replace("b8_", "building 8, ").replace("_", " ")
        ax.set_title(name, fontsize=8, color=INK)
        ax.set_xlabel("steps (5 min) from the change in occupancy", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.spines[["top", "right"]].set_visible(False)
    np.atleast_1d(axes)[0].set_ylabel("change in zone heat (W)", fontsize=8)
    np.atleast_1d(axes)[-1].text(W[0], 74, "one person: 70 W", fontsize=7, color=MUTED, va="bottom")
    h, lab = np.atleast_1d(axes)[0].get_legend_handles_labels()
    fig.legend(h, lab, fontsize=7, frameon=False, ncol=2, loc="upper center")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1], *sys.argv[2:])
