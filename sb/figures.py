"""Paper figures.

    python -m sb.figures probe D:/SmartBuildings_data/results/probe_b1_atl.npz docs/fig/fig_probe.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

from sb.fit_probe import C_AIR, fit

INK = "#1f2933"
BLUE = "#2563eb"
GREY = "#9aa5b1"


def fig_probe(npz: str, out: str) -> None:
    res = fit(npz)
    d = np.load(npz)
    T, Q = d["T"], d["Q"]
    F, D = Q[..., 0], Q[..., 1]
    q = np.zeros_like(T)
    q[1:] = F[1:] * (D[1:] - T[:-1]) * C_AIR / 1e3
    y = T[1:] - T[:-1]
    # Distributed-lag fit, pooled over zones: dT[k] on q[k], q[k-1], q[k-2].
    lags = 4
    rows_y, rows_x = [], []
    for z in range(T.shape[1]):
        yy = y[lags:, z]
        X = np.stack([q[lags + 1 - l: len(q) - l if l > 0 else None, z][: len(yy)] for l in range(lags)], 1)
        X = np.c_[X, T[lags:-1, z] - 295.0, np.ones(len(yy))]
        rows_y.append(yy)
        rows_x.append(X)
    c, *_ = np.linalg.lstsq(np.vstack(rows_x), np.concatenate(rows_y), rcond=None)

    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.6))
    names = ["no_delay", "delay", "delay_relax", "both_relax"]
    labels = ["heat now", "heat one\nstep earlier", "+ relaxation", "both + relax."]
    vals = [res[n]["r2_median"] for n in names]
    ax[0].bar(range(4), vals, color=[GREY, GREY, BLUE, GREY])
    for i, v in enumerate(vals):
        ax[0].text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=8, color=INK)
    ax[0].set_xticks(range(4), labels, fontsize=7)
    ax[0].set_ylim(0, 1)
    ax[0].set_ylabel("median $R^2$ over zones", fontsize=8)
    ax[0].set_title("Which zone model explains the probe?", fontsize=9)
    ax[1].bar(range(lags), c[:lags], color=BLUE)
    ax[1].set_xticks(range(lags), [f"k-{l}" if l else "k" for l in range(lags)], fontsize=8)
    ax[1].set_ylabel("K per kW", fontsize=8)
    ax[1].set_title("Temperature change at step k\nper kW delivered at step ...", fontsize=9)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
        a.tick_params(labelsize=7)
    fig.tight_layout()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    print("wrote", out, "lag coefficients", np.round(c[:lags], 4), "relax", round(c[lags], 3))


def fig_scenarios(out: str, *folders: str) -> None:
    """Per-scenario mean per-step loss for several policies (log scale)."""
    import json

    runs = {}
    for f in folders:
        name = Path(f).name
        runs[name] = {j.stem: abs(json.loads(j.read_text())["mean_reward"]) for j in Path(f).glob("*.json")
                     if not j.name.startswith("RUN_")}
    keys = sorted(set.intersection(*[set(r) for r in runs.values()]))
    fig, ax = plt.subplots(figsize=(7.0, 2.8))
    w = 0.8 / len(runs)
    greys = ["#9aa5b1", "#cbd2d9", "#616e7c", "#e4e7eb"]
    for i, (name, r) in enumerate(runs.items()):
        color = BLUE if i == len(runs) - 1 else greys[i % len(greys)]
        ax.bar(np.arange(len(keys)) + i * w, [r[k] for k in keys], w, label=name, color=color)
    ax.set_yscale("log")
    ax.set_xticks(np.arange(len(keys)) + w * (len(runs) - 1) / 2,
                  [k.replace("building_train_", "b").replace("building_", "b").replace("__", " ") for k in keys],
                  fontsize=7, rotation=30 if len(keys) > 6 else 0, ha="right" if len(keys) > 6 else "center")
    ax.set_ylabel("mean loss per step (log)", fontsize=8)
    ax.legend(fontsize=7, frameon=False, ncol=len(runs))
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    print("wrote", out)


def fig_trace(out: str, ours_csv: str, base_csv: str, day: int = 3) -> None:
    """One day of zone temperatures (min/mean/max), ours vs a baseline."""
    import pandas as pd

    fig, ax = plt.subplots(2, 1, figsize=(7.0, 3.6), sharex=True)
    for a, (csv, label) in zip(ax, ((base_csv, "pid_water"), (ours_csv, "zonal (ours)"))):
        d = pd.read_csv(csv)
        ts = pd.to_datetime(d.ts)
        start = ts.dt.normalize().iloc[0] + pd.Timedelta(days=day)
        m = (ts >= start) & (ts < start + pd.Timedelta(days=1))
        d, ts = d[m], ts[m]
        h = ((ts - start).dt.total_seconds() / 3600.0).values
        a.fill_between(h, d.tmin, d.tmax, color="#dbeafe" if "ours" in label else "#e4e7eb", label="zone min-max")
        a.plot(h, d.tmean, color=BLUE if "ours" in label else INK, lw=1.2, label="zone mean")
        occ = d.occ.values > 0
        a.fill_between(h, 21, 24, where=occ, color="#fde68a", alpha=0.35, lw=0, label="comfort band, occupied")
        a.set_ylabel("deg C", fontsize=8)
        a.set_title(label, fontsize=8, loc="left")
        a.spines[["top", "right"]].set_visible(False)
        a.tick_params(labelsize=7)
    ax[1].set_xlabel("hour of day", fontsize=8)
    ax[0].legend(fontsize=6, frameon=False, ncol=3, loc="lower right")
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    print("wrote", out)


def fig_cycle(out: str, room: str, *pairs: str) -> None:
    """One zone over the same window under several policies (zone_dump files).

    pairs: label=path.npz ... ; an optional pair size=WxH (inches) sets the figure size (default 7.0x2.4).
    """
    size = (7.0, 2.4)
    if pairs and pairs[0].startswith("size="):
        size = tuple(float(x) for x in pairs[0][5:].split("x"))
        pairs = pairs[1:]
    fig, ax = plt.subplots(1, 1, figsize=size)
    colors = [GREY, BLUE, INK]
    for i, pair in enumerate(pairs):
        label, path = pair.split("=", 1)
        d = np.load(path)
        names = [s.replace("_zone_air_temperature_sensor", "").replace("VAV_", "room_") for s in d["policy_zones"]]
        z = names.index(room)
        zn = list(d["zone_names"])
        lo = d["lo"][:, zn.index(room)] - 273.15
        hi = d["hi"][:, zn.index(room)] - 273.15
        t = np.arange(len(d["T"])) * 5 / 60.0
        if i == 0:
            ax.fill_between(t, lo, hi, color="#fde68a", alpha=0.35, lw=0, label="comfort band")
        ax.plot(t, d["T"][:, z] - 273.15, color=colors[i % 3], lw=1.0 if i == 0 else 1.4, label=label)
    ax.set_xlabel("hours", fontsize=10)
    ax.set_ylabel("zone temp. (°C)", fontsize=10)
    ax.legend(fontsize=9.5, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(2))
    fig.tight_layout()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    print("wrote", out)


def fig_glide(out: str, v8_csv: str, v9_csv: str) -> None:
    """Building mean/min zone temperature and boiler gas, v8 vs v9 (sb.debug traces)."""
    import pandas as pd

    a8, a9 = pd.read_csv(v8_csv), pd.read_csv(v9_csv)
    ts = pd.to_datetime(a8.ts)
    h = ((ts - ts.iloc[0]).dt.total_seconds() / 3600.0).values
    occ = a8.occ.values > 0
    fig, ax = plt.subplots(2, 1, figsize=(7.0, 3.6), sharex=True)
    for a in ax:
        lo, hi = (12, 23) if a is ax[0] else (0, max(a8.gas_kw.max(), a9.gas_kw.max()) * 1.05)
        a.fill_between(h, lo, hi, where=occ, color="#fde68a", alpha=0.35, lw=0)
        a.spines[["top", "right"]].set_visible(False)
        a.tick_params(labelsize=7)
    ax[0].plot(h, a8.tmean, color=GREY, lw=1.0, label="v8, zone mean")
    ax[0].plot(h, a9.tmean, color=BLUE, lw=1.2, label="v9, zone mean")
    ax[0].plot(h, a8.tmin, color=GREY, lw=0.6, ls=":", label="v8, coldest zone")
    ax[0].plot(h, a9.tmin, color=BLUE, lw=0.6, ls=":", label="v9, coldest zone")
    ax[0].axhline(21.0, color=INK, lw=0.5, ls="--")
    ax[0].set_ylabel("zone temp. (deg C)", fontsize=8)
    ax[0].set_ylim(12, 23)
    ax[0].legend(fontsize=7, frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    g8, g9 = a8.gas_kw.mean(), a9.gas_kw.mean()
    ax[1].plot(h, a8.gas_kw, color=GREY, lw=0.8, label=f"v8 (mean {g8:.0f} kW)")
    ax[1].plot(h, a9.gas_kw, color=BLUE, lw=0.9, label=f"v9 (mean {g9:.0f} kW)")
    ax[1].set_ylabel("boiler gas (kW)", fontsize=8)
    ax[1].set_xlabel("hours from the start of the episode (Sunday 06:00); shaded = occupied", fontsize=8)
    ax[1].legend(fontsize=7, frameon=False, ncol=2, loc="upper right")
    fig.tight_layout()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    print("wrote", out, f"gas v8 {g8:.1f} kW, v9 {g9:.1f} kW")


if __name__ == "__main__":
    kind = sys.argv[1]
    if kind == "glide":
        fig_glide(sys.argv[2], sys.argv[3], sys.argv[4])
    if kind == "probe":
        fig_probe(sys.argv[2], sys.argv[3])
    elif kind == "scenarios":
        fig_scenarios(sys.argv[2], *sys.argv[3:])
    elif kind == "trace":
        fig_trace(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]) if len(sys.argv) > 5 else 3)
    elif kind == "cycle":
        fig_cycle(sys.argv[2], sys.argv[3], *sys.argv[4:])
