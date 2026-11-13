"""What the five numbers learn (docs/PARAMS.md), read from the size-gate traces (docs/SIZEGATE.md; v15, first three
days of a cold window, 17 buildings: six shipped training buildings, six full-size development buildings and five of
them scaled to the shipped size). Per zone: the gain g of Eq. 1 averaged over day 3, and the true floor area from the
simulator's grid (the controller never sees it). If g is the inverse of the zone's heat capacity, log g falls with log
area with slope -1 within a building.

    python -m sb.params_read [--fig docs/fig/fig_params.png]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

DIR = Path("D:/SmartBuildings_data/results/sizegate")
G_LO, G_HI = 0.05, 0.8   # m2_lo, m2_hi of the gain in frozen/zonal_v14f.py
GROUPS = {"train": "shipped", "full": "full size", "scaled": "scaled twins"}


def load() -> list[dict]:
    out = []
    for f in sorted(DIR.glob("*.npz")):
        d = np.load(f)
        th = d["p_theta2"][-288:].mean(axis=0)            # zones x 5, mean over day 3
        area = d["area"] * float(d["cv_m"]) ** 2
        g = th[:, 1]
        free = (g > G_LO + 1e-6) & (g < G_HI - 1e-6)
        tag, b, w = f.stem.split("__")
        out.append(dict(group=tag, building=b.replace("building_", ""), weather=w, g=g, area=area, free=free,
                        lam=-th[:, 0], b=th[:, 3]))
    return out


def slope(rows: list[dict]) -> float:
    xs, ys = [], []
    for r in rows:
        m = r["free"]
        if m.sum() < 3:
            continue
        x, y = np.log(r["area"][m]), np.log(r["g"][m])
        xs.append(x - x.mean())
        ys.append(y - y.mean())
    x, y = np.concatenate(xs), np.concatenate(ys)
    return float((x * y).sum() / (x * x).sum())


def boot(rows: list[dict], n: int = 2000, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    s = [slope([rows[i] for i in rng.integers(0, len(rows), len(rows))]) for _ in range(n)]
    return float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))


def r2_within(rows: list[dict]) -> float:
    xs, ys = [], []
    for r in rows:
        m = r["free"]
        if m.sum() < 3:
            continue
        x, y = np.log(r["area"][m]), np.log(r["g"][m])
        xs.append(x - x.mean())
        ys.append(y - y.mean())
    x, y = np.concatenate(xs), np.concatenate(ys)
    return float(np.corrcoef(x, y)[0, 1] ** 2)


def main(argv: list[str]) -> None:
    rows = load()
    print("building                         zones  free  area m2 (min-max)   g median  slope (within)")
    for r in rows:
        m = r["free"]
        s = slope([r]) if m.sum() >= 3 else float("nan")
        print(f"{r['group']:6s} {r['building']:8s} {r['weather']:14s} {len(r['g']):5d} {int(m.sum()):5d}  "
              f"{r['area'].min():7.1f}-{r['area'].max():7.1f}  {np.median(r['g']):8.3f}  {s:+.2f}")
    for key in ("train", "full", "scaled", None):
        sel = [r for r in rows if key is None or r["group"] == key]
        n = sum(len(r["g"]) for r in sel)
        nf = sum(int(r["free"].sum()) for r in sel)
        lo, hi = boot(sel)
        name = "all" if key is None else GROUPS[key]
        print(f"{name:13s}: {len(sel)} buildings, {n} zones, {n - nf} at a bound of g ({100 * (n - nf) / n:.0f} %); "
              f"within-building slope of log g on log area {slope(sel):+.2f} (95 % over buildings {lo:+.2f} to "
              f"{hi:+.2f}), R2 {r2_within(sel):.2f}")
    if "--fig" in argv:
        fig(rows, argv[argv.index("--fig") + 1])


def fig(rows: list[dict], out: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    SURFACE, TEXT, TEXT2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    COL = {"train": ("#2a78d6", "o"), "full": ("#1f9e74", "s"), "scaled": ("#eb6834", "^")}
    f, ax = plt.subplots(figsize=(3.3, 2.6), facecolor=SURFACE)
    for key in ("train", "scaled", "full"):
        xs, ys = [], []
        for r in rows:
            if r["group"] != key:
                continue
            m = r["free"]
            xs.append(r["area"][m] / np.median(r["area"][m]))
            ys.append(r["g"][m] / np.median(r["g"][m]))
        x, y = np.concatenate(xs), np.concatenate(ys)
        c, mk = COL[key]
        ax.scatter(x, y, s=9, marker=mk, facecolors="none", edgecolors=c, lw=0.7, label=GROUPS[key], zorder=3)
    xx = np.array([0.1, 10.0])
    ax.plot(xx, 1 / xx, color=TEXT2, lw=0.8, ls="--", zorder=1)
    ax.text(3.2, 0.42, "slope $-1$", fontsize=6.5, color=TEXT2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("room floor area / building median", fontsize=7.5, color=TEXT)
    ax.set_ylabel("learned gain g / building median", fontsize=7.5, color=TEXT)
    ax.legend(fontsize=6.2, frameon=False, loc="lower left", handletextpad=0.3)
    ax.set_facecolor(SURFACE)
    ax.tick_params(labelsize=6.5, colors=TEXT2)
    ax.spines[["top", "right"]].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(TEXT2)
    ax.grid(True, which="major", color=GRID, lw=0.5)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    f.savefig(out, dpi=300, facecolor=SURFACE, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1:])
