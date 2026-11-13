"""Figure 2: transfer to unseen buildings. (a) Every unseen scenario we ran, our frozen version's mean loss per step
against pid_water's on the same scenario: blind rounds 1-5 (each with the version frozen for it), the 40 new-climate
scenarios (v13) and the 16 full-size buildings (v14). (b) Adaptation: in each unseen scenario of rounds 2-5 and the
new climates, the loss ratio to pid_water on the first work day against the ratio over the later work days.

    python -m sb.fig_transfer docs/fig/fig_transfer.png
"""

from __future__ import annotations

import glob
import os
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

D = Path("D:/SmartBuildings_data")
R = D / "results"
SURFACE, TEXT, TEXT2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1f9e74", "#9aa3ad"   # validated (dataviz validator, light)
# (label, ours, baseline, scenario root, colour, marker)
SETS = [
    ("Round 1 (v7)", ["heldout/zonal"], ["heldout/pid_water"], "heldout", GREY, "x"),
    ("Rounds 2-5 (v8-v11)", ["heldout2/v8", "heldout3/v9", "heldout4/v10", "heldout5/v11"],
     ["heldout2/pid_water", "heldout3/pid_water", "heldout4/pid_water", "heldout5/pid_water"], None, BLUE, "o"),
    ("New climates (v13)", ["stress/v13"], ["stress/pid_water"], "stress", ORANGE, "^"),
    ("Full size (v14)", ["bigbld/v14", "bigdev/v14"], ["bigbld/pid_water", "bigdev/pid_water"], None, GREEN, "s"),
]
# Rounds 6 and 7 (full size), once pid_water has run there (docs/BASELINE_R67.md): round 6 with v15 (arm ed1), round 7
# with the version that is final after round 7 (R7_FINAL, set from its result).
R7_FINAL = "chm"   # round 7 passed (docs/RESULTS_ROUND7.md): chm is v16
if R7_FINAL and (R / "round7/pid_water").exists() and (R / "round6h/pid_water").exists():
    SETS[-1] = ("Full size (v14-v16)" if R7_FINAL == "chm" else "Full size (v14, v15)",
                ["bigbld/v14", "bigdev/v14", "round6h/ed1", f"round7/{R7_FINAL}"],
                ["bigbld/pid_water", "bigdev/pid_water", "round6h/pid_water", "round7/pid_water"], None, GREEN, "s")
# Round 8 (docs/RESULTS_ROUND8.md): its candidate failed, so v16 is the version shown, once pid_water has run there.
if len(list((R / "round8/pid_water").glob("*.npy"))) == 6:
    _name, _ours, _base, *_rest = SETS[-1]
    SETS[-1] = (_name, _ours + ["round8/v16"], _base + ["round8/pid_water"], *_rest)
HOL = set(USFederalHolidayCalendar().holidays("2022-01-01", "2024-12-31").date)


def pairs(ours: list[str], base: list[str]) -> list[tuple[str, Path, Path]]:
    out = []
    for a, b in zip(ours, base):
        for f in sorted((R / a).glob("*.npy")):
            g = R / b / f.name
            if g.exists():
                out.append((a.split("/")[0], f, g))
    return out


def loss(f: Path, n: int | None = None) -> np.ndarray:
    a = np.load(f).astype(float)
    return -a[: n or len(a), 0]


def start(folder: str, s: str) -> pd.Timestamp:
    b, w = s.split("__")
    g = (D / folder / "scenarios" / b / w / "config.gin").read_text()
    return pd.Timestamp(re.search(r"start_timestamp = '([^']+)'", g).group(1))


def ticks(a, xt: list[float], yt: list[float]) -> None:
    a.set_xticks(xt, [f"{v:g}" for v in xt])
    a.set_yticks(yt, [f"{v:g}" for v in yt])
    a.minorticks_off()


def main(out: str) -> None:
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.5, 2.45), facecolor=SURFACE,
                                 gridspec_kw={"width_ratios": [1.0, 1.0], "wspace": 0.42})
    below = {}
    adapt = []
    allv = []
    for label, ours, base, _, color, marker in SETS:
        xs, ys = [], []
        for folder, f, g in pairs(ours, base):
            x, y = loss(g), loss(f)
            n = min(len(x), len(y))
            xs.append(x[:n].mean())
            ys.append(y[:n].mean())
            if folder in ("heldout2", "heldout3", "heldout4", "heldout5", "stress") and n >= 8640:
                st = start(folder, f.stem)
                days = [st + pd.Timedelta(days=d) for d in range(30)]
                work = [d for d, t in enumerate(days) if t.weekday() < 5 and t.date() not in HOL]
                yd, xd = y[:8640].reshape(30, 288).sum(1), x[:8640].reshape(30, 288).sum(1)
                adapt.append((folder == "stress", xd[work[0]] and yd[work[0]] / xd[work[0]],
                              yd[work[1:]].sum() / xd[work[1:]].sum()))
            if folder in ("bigbld", "bigdev", "round6h", "round7", "round8") and n >= 2880:   # full size, ten days
                st = start(folder, f.stem)
                days = [st + pd.Timedelta(days=d) for d in range(10)]
                work = [d for d, t in enumerate(days) if t.weekday() < 5 and t.date() not in HOL]
                yd, xd = y[:2880].reshape(10, 288).sum(1), x[:2880].reshape(10, 288).sum(1)
                adapt.append((2.0, yd[work[0]] / xd[work[0]], yd[work[1:]].sum() / xd[work[1:]].sum()))
        xs, ys = np.array(xs), np.array(ys)
        allv += list(xs) + list(ys)
        below[label] = (int((ys < xs).sum()), len(xs))
        r = ys / xs
        print(f"  {label}: ratio ours / pid_water median {np.median(r):.3f}, quartiles {np.percentile(r, 25):.3f}-"
              f"{np.percentile(r, 75):.3f}, range {r.min():.3f}-{r.max():.3f}")
        kw = dict(color=color) if marker == "x" else dict(facecolors="none", edgecolors=color)
        short = label if label.startswith("Round 1") else label.split(" (")[0]
        ax.scatter(xs, ys, s=14, marker=marker, lw=0.9, label=f"{short}: {below[label][0]}/{below[label][1]}",
                   zorder=3, **kw)
    lim = (min(0.0012, min(allv) / 1.15), max(0.2, max(allv) * 1.15))  # every point inside (audit 8 Nov)
    print(f"  panel a limits {lim[0]:.5f}-{lim[1]:.4f}; data {min(allv):.5f}-{max(allv):.4f}")
    ax.plot(lim, lim, color=TEXT2, lw=0.8, ls="--", zorder=1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_aspect("equal")
    ax.text(0.0042, 0.0056, "equal loss", fontsize=7.2, color=TEXT2, rotation=45, ha="center", va="center")
    ticks(ax, [0.002, 0.01, 0.05], [0.002, 0.01, 0.05])
    ax.set_xlabel("pid_water, mean loss per step", fontsize=8.2, color=TEXT)
    ax.set_ylabel("ours, mean loss per step", fontsize=8.2, color=TEXT)
    ax.set_title("a   Scenarios outside development", fontsize=8.5, loc="left", color=TEXT, weight="bold")
    ax.legend(fontsize=6.9, frameon=False, loc="upper left", handletextpad=0.3, borderaxespad=0.2,
              title="ours below pid_water in", title_fontsize=6.9, alignment="left")

    adapt = np.array(adapt, dtype=float)
    for is_stress, color, marker, label in ((0.0, BLUE, "o", "Rounds 2-5"), (1.0, ORANGE, "^", "New climates"),
                                            (2.0, GREEN, "s", "Full size")):
        sel = adapt[:, 0] == is_stress
        bx.scatter(adapt[sel, 2], adapt[sel, 1], s=14, marker=marker, facecolors="none", edgecolors=color, lw=0.9,
                   label=f"{label} ({int(sel.sum())})", zorder=3)
    blim = (0.03, 1.0)
    bx.plot(blim, blim, color=TEXT2, lw=0.8, ls="--", zorder=1)
    bx.text(0.72, 0.5, "no extra loss", fontsize=7.2, color=TEXT2, rotation=45, ha="center", va="center")
    bx.set_xscale("log")
    bx.set_yscale("log")
    bx.set_xlim(*blim)
    bx.set_ylim(*blim)
    bx.set_aspect("equal")
    ticks(bx, [0.05, 0.1, 0.2, 0.5, 1.0], [0.05, 0.1, 0.2, 0.5, 1.0])
    bx.set_xlabel("ratio to pid_water, later work days", fontsize=8.2, color=TEXT)
    bx.set_ylabel("ratio, first work day", fontsize=8.2, color=TEXT)
    bx.set_title("b   First work day in a new building", fontsize=8.5, loc="left", color=TEXT, weight="bold")
    bx.legend(fontsize=6.9, frameon=False, loc="upper left", handletextpad=0.3, borderaxespad=0.2)
    for a in (ax, bx):
        a.set_facecolor(SURFACE)
        a.tick_params(labelsize=7.2, colors=TEXT2)
        a.spines[["top", "right"]].set_visible(False)
        for s in ("left", "bottom"):
            a.spines[s].set_color(TEXT2)
        a.grid(True, which="major", color=GRID, lw=0.5)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, facecolor=SURFACE, bbox_inches="tight")
    print("wrote", out)
    for k, (b, n) in below.items():
        print(f"  {k}: ours below pid_water in {b} of {n}")
    for is_stress, name in ((0.0, "rounds 2-5"), (1.0, "new climates"), (2.0, "full size")):
        sel = adapt[:, 0] == is_stress
        print(f"  adaptation {name}: n {int(sel.sum())}, first work day median ratio {np.median(adapt[sel, 1]):.3f}, "
              f"later {np.median(adapt[sel, 2]):.3f}, first < 1 in {int((adapt[sel, 1] < 1).sum())}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/fig/fig_transfer.png")
