"""Figure: training of the residual controller (docs/TRAINED_BASELINE.md). Validation loss (five scenarios of
building_train_4, 2880 steps, no exploration noise, corrected simulator) and the training loss (with exploration noise,
mean over 50 iterations) against simulator steps, with pid_water's validation loss, the chosen checkpoint and the
restart of deviation 2. Training and validation data only; nothing from the test scenarios.

    python -m sb.fig_trained docs/fig/fig_trained.pdf
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RUN = Path("D:/SmartBuildings_data/results/rl/main")
SURFACE, TEXT, TEXT2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#9aa3ad"
RESTART_IT = 1050    # deviation 2: actors of iteration 450, new settings, from here on


def main(out: str) -> None:
    val = pd.read_csv(RUN / "val.csv").drop_duplicates("it", keep="first").sort_values("it")
    tr = pd.read_csv(RUN / "train.csv").sort_values("it")
    base = float(np.mean([r["loss"] for r in json.loads((RUN / "val_baseline.json").read_text())]))
    best = json.loads((RUN / "best.json").read_text())
    restart_steps = float(tr.loc[tr["it"] <= RESTART_IT, "env_steps"].max()) / 1e6

    plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": TEXT2,
                         "xtick.color": TEXT2, "ytick.color": TEXT2, "text.color": TEXT})
    fig, ax = plt.subplots(1, 1, figsize=(6.0, 3.0), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    roll = tr["loss"].rolling(50, min_periods=10).mean()
    ax.plot(tr["env_steps"] / 1e6, roll, color=GREY, lw=1.0, label="training loss (with exploration, mean of 50 iterations)")
    ax.plot(val["env_steps"] / 1e6, val["val_loss"], color=BLUE, lw=1.6, marker="o", ms=3.5,
            label="validation loss (building_train_4, no exploration)")
    ax.axhline(base, color=ORANGE, lw=1.2, ls="--", label=f"pid_water on the validation scenarios ({base:.4f})")
    b = val.loc[val["it"] == best["it"]].iloc[0]
    ax.plot([b["env_steps"] / 1e6], [b["val_loss"]], marker="o", ms=8, mfc="none", mec=TEXT, mew=1.2)
    ax.annotate(f"chosen: iteration {int(best['it'])}, {best['val_loss']:.4f}", (b["env_steps"] / 1e6, b["val_loss"]),
                xytext=(6, -14), textcoords="offset points", fontsize=8, color=TEXT)
    ax.axvline(restart_steps, color=TEXT2, lw=0.8, ls=":")
    top = max(base, roll.max()) * 1.12
    ax.annotate("restart from iteration 450\n(new settings, averaged weights)", (restart_steps, top),
                xytext=(4, -2), textcoords="offset points", fontsize=7.5, color=TEXT2, va="top")
    ax.set_xlabel("simulator steps (millions)")
    ax.set_ylabel("mean loss per step")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    # Above the axes, so neither the data nor the restart line runs through it.
    ax.legend(fontsize=7.5, frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.0), borderaxespad=0.3)
    lo = min(val["val_loss"].min(), roll.min())
    ax.set_ylim(lo * 0.85, top)
    fig.tight_layout()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, facecolor=SURFACE)
    print("wrote", out, f"| validation points {len(val)}, last it {int(val['it'].max())}, steps {tr['env_steps'].max():,}, "
          f"hours {tr['hours'].max():.2f}, best it {best['it']} {best['val_loss']:.5f}, pid_water {base:.5f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/fig/fig_trained.pdf")
