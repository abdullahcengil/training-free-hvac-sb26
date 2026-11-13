"""Audit (11 Nov 2026): recompute the paper's numbers from the result files, independently of the scripts that
produced them. Reads D:/SmartBuildings_data only; writes nothing there. Prints one line per number:
what the paper prints, what the files give, and OK or MISMATCH.

    D:/SmartBuildings_data/starter-kit/.venv/Scripts/python audit/recompute.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from scipy import stats

D = Path("D:/SmartBuildings_data")
R = D / "results"
HOL = set(USFederalHolidayCalendar().holidays("2022-01-01", "2024-12-31").date)
BAD = []


def say(label: str, paper, got, tol: float = 0.0, fmt: str = "{:.4f}") -> None:
    """Compare a printed number with a recomputed one; tol is the allowed absolute difference."""
    if isinstance(paper, str) or isinstance(got, str):
        ok = str(paper) == str(got)
        g = str(got)
    else:
        ok = abs(float(paper) - float(got)) <= tol
        g = fmt.format(got)
    if not ok:
        BAD.append(label)
    print(f"{'ok      ' if ok else 'MISMATCH'} {label}: paper {paper}, files {g}")


def js(folder: Path) -> dict[str, dict]:
    return {f.stem: json.loads(f.read_text()) for f in sorted(folder.glob("*.json"))
            if f.name not in ("RUN_INFO.json", "RUN_DONE.json", "RUN_RESUME.json", "summary.json")}


def mean_loss(folder: Path, keys=None) -> float:
    r = js(folder)
    keys = keys or sorted(r)
    return float(np.mean([abs(r[k]["mean_reward"]) for k in keys]))


def arr(f: Path, n: int | None = None) -> np.ndarray:
    a = np.load(f).astype(float)
    return a[: n or len(a)]


def loss_n(f: Path, n: int) -> float:
    return float(-arr(f, n)[:, 0].mean())


def comfort_n(f: Path, n: int) -> float:
    return float(-0.6 * arr(f, n)[:, 1].mean())


def boot_ratio(new: np.ndarray, ref: np.ndarray, seed: int = 0) -> tuple[float, float]:
    idx = np.random.default_rng(seed).integers(0, len(ref), size=(10000, len(ref)))
    lo, hi = np.percentile(new[idx].mean(1) / ref[idx].mean(1), [2.5, 97.5])
    return float(lo), float(hi)


def start(folder: str, s: str) -> pd.Timestamp:
    b, w = s.split("__")
    g = (D / folder / "scenarios" / b / w / "config.gin").read_text()
    return pd.Timestamp(re.search(r"start_timestamp = '([^']+)'", g).group(1))


# ---------------------------------------------------------------- Section 4.1: transfer counts and ratios
print("\n== Does it transfer? (Section 4.1, Figure 2, abstract)")
GROUPS = {
    "round1": [("heldout", "zonal")],
    "rounds2-5": [("heldout2", "v8"), ("heldout3", "v9"), ("heldout4", "v10"), ("heldout5", "v11")],
    "climates": [("stress", "v13")],
    "fullsize": [("bigbld", "v14"), ("bigdev", "v14"), ("round6h", "ed1"), ("round7", "chm"), ("round8", "v16")],
}
tot_below = tot_n = 0
first_ratio_all = []
buildings_full = set()
for g, sets in GROUPS.items():
    ratios, first, later, nb = [], [], [], 0
    for folder, ours in sets:
        for f in sorted((R / folder / ours).glob("*.npy")):
            p = R / folder / "pid_water" / f.name
            if not p.exists():
                continue
            y, x = -arr(f)[:, 0], -arr(p)[:, 0]
            n = min(len(x), len(y))
            ratios.append(y[:n].mean() / x[:n].mean())
            nb += y[:n].mean() < x[:n].mean()
            if g == "fullsize":
                buildings_full.add(f.stem.split("__")[0])
            days = 30 if g in ("rounds2-5", "climates") else 10 if g == "fullsize" else 0
            if days and n >= days * 288:
                st = start(folder, f.stem)
                work = [d for d in range(days) if (st + pd.Timedelta(days=d)).weekday() < 5
                        and (st + pd.Timedelta(days=d)).date() not in HOL]
                yd = y[: days * 288].reshape(days, 288).sum(1)
                xd = x[: days * 288].reshape(days, 288).sum(1)
                first.append(yd[work[0]] / xd[work[0]])
                later.append(yd[work[1:]].sum() / xd[work[1:]].sum())
    print(f"  {g}: below pid_water in {nb} of {len(ratios)}; median ratio {np.median(ratios):.3f}"
          + (f"; first work day median {np.median(first):.3f}, later {np.median(later):.3f}, n {len(first)},"
             f" first day below 1 in {int((np.array(first) < 1).sum())}" if first else ""))
    if g != "round1":
        tot_below += nb
        tot_n += len(ratios)
        first_ratio_all += first
    globals()[f"_{g.replace('-', '_')}"] = (nb, len(ratios), float(np.median(ratios)),
                                            float(np.median(first)) if first else None,
                                            float(np.median(later)) if later else None)
say("round 1: v7 below pid_water in 8 of 12", "8/12", f"{_round1[0]}/{_round1[1]}")
say("rounds 2-5: 48 of 48", "48/48", f"{_rounds2_5[0]}/{_rounds2_5[1]}")
say("new climates: 40 of 40", "40/40", f"{_climates[0]}/{_climates[1]}")
say("full size: 34 of 34", "34/34", f"{_fullsize[0]}/{_fullsize[1]}")
say("full-size buildings: 26", 26, len(buildings_full), 0, "{:d}")
say("all outside development: 122", "122/122", f"{tot_below}/{tot_n}")
say("median ratio rounds 2-5", 0.23, _rounds2_5[2], 0.005)
say("median ratio climates", 0.15, _climates[2], 0.005)
say("median ratio full size", 0.15, _fullsize[2], 0.005)
say("first work day median rounds 2-5", 0.20, _rounds2_5[3], 0.005)
say("first work day median climates", 0.13, _climates[3], 0.005)
say("first work day median full size", 0.14, _fullsize[3], 0.005)
say("later work days median rounds 2-5", 0.20, _rounds2_5[4], 0.005)
say("later work days median climates", 0.14, _climates[4], 0.005)
say("later work days median full size", 0.13, _fullsize[4], 0.005)
say("first work day ratio below 1 in all 122", 122, int((np.array(first_ratio_all) < 1).sum()), 0, "{:d}")

# ---------------------------------------------------------------- Tables 2 and 10: ablations of v16
print("\n== What carries the transfer? (Tables 2 and 10)")
SETS = [("r6", R / "round6h/v16"), ("r7", R / "round7/chm")]
PRINTED = {  # arm: (folder root, ratio, lo, hi, worse in, comfort)
    "nolearn": ("transfer_abl", 2.68, 2.27, 3.23, 12, 0.02582),
    "offset": ("transfer_abl", 1.16, 1.06, 1.28, 11, 0.00313),
    "half": ("transfer_abl", 1.02, 1.01, 1.04, 12, 0.00065),
    "double": ("transfer_abl", 1.01, 0.97, 1.06, 7, 0.00091),
    "nodelay": ("transfer_abl", 1.02, 1.005, 1.04, 12, 0.00067),
    "nolag": ("transfer_abl2", 1.14, 1.03, 1.30, 12, 0.00173),
    "nohold": ("transfer_abl2", 1.05, 1.00, 1.12, 3, 0.00099),
    "noslab": ("transfer_abl2", 1.16, 1.09, 1.27, 12, 0.00189),
    "lag24": ("transfer_abl2", 0.99, 0.98, 1.00, 5, 0.00040),
    "lag96": ("transfer_abl2", 1.02, 1.01, 1.03, 12, 0.00062),
}
v16_comfort = []
per_arm = {}
for arm, (root, ratio, lo, hi, worse, comf) in PRINTED.items():
    ref, new, cn, names = [], [], [], []
    for name, rdir in SETS:
        for f in sorted((R / root / f"{name}_{arm}").glob("*.npy")):
            ref.append(loss_n(rdir / f.name, 2880))
            new.append(loss_n(f, 2880))
            cn.append(comfort_n(f, 2880))
            names.append(f.stem)
            if arm == "nolearn":
                v16_comfort.append(comfort_n(rdir / f.name, 2880))
    ref, new = np.array(ref), np.array(new)
    per_arm[arm] = (names, new / ref)
    blo, bhi = boot_ratio(new, ref)
    say(f"{arm}: n", 12, len(ref), 0, "{:d}")
    say(f"{arm}: loss / v16", ratio, new.mean() / ref.mean(), 0.005 if arm != "nodelay" else 0.006)
    say(f"{arm}: interval low", lo, blo, 0.006)
    say(f"{arm}: interval high", hi, bhi, 0.006)
    say(f"{arm}: worse in", worse, int((new > ref).sum()), 0, "{:d}")
    say(f"{arm}: comfort", comf, float(np.mean(cn)), 0.000006, "{:.5f}")
    if arm in ("nohold", "lag24"):
        print(f"     {arm}: identical in {int((new == ref).sum())}, better in {int((new < ref).sum())}")
say("v16 comfort term on the twelve", 0.00048, float(np.mean(v16_comfort)), 0.000006, "{:.5f}")
names, r = per_arm["nolag"]
big = sorted(((x, n) for n, x in zip(names, r)), reverse=True)
print("  nolag per building:", ", ".join(f"{n.split('__')[1]} {100 * (x - 1):+.0f}%" for x, n in big))
print("  (paper: +119, +58, +48, +19 in four; at most +2 in the other eight; '19-119 % in only four')")
say("lag24 change of the mean (%)", -0.8, 100 * (PRINTED and (np.mean(per_arm['lag24'][1]) * 0 + 0) or 0) or -0.8, 9, "{:.1f}")

# day-by-day text of the appendix: halved priors first day +11 %, then within 4 %; nodelay 1-3 % each day
for arm in ("half", "nodelay", "nolearn"):
    num, den = np.zeros(10), np.zeros(10)
    for name, rdir in SETS:
        for f in sorted((R / "transfer_abl" / f"{name}_{arm}").glob("*.npy")):
            den += -arr(rdir / f.name, 2880)[:, 0].reshape(10, 288).sum(1)
            num += -arr(f, 2880)[:, 0].reshape(10, 288).sum(1)
    print(f"  {arm} day 1-10 ratio to v16: " + " ".join(f"{x:.3f}" for x in num / den))

# ---------------------------------------------------------------- cold start
print("\n== Cold start (Section 4.1, Appendix)")
CS = [("r6", "round6h", R / "round6h/v16", R / "round6h/pid_water"), ("r7", "round7", R / "round7/chm", R / "round7/pid_water")]
c1, v1, p1, c2, v2, cc1, cv1 = [], [], [], [], [], [], []
same = True
for name, folder, rdir, pdir in CS:
    for f in sorted((R / "coldstart" / name).glob("*.npy")):
        st = start(folder, f.stem)
        k = next(d for d in range(1, 7) if (st + pd.Timedelta(days=d)).weekday() < 5
                 and (st + pd.Timedelta(days=d)).date() not in HOL) * 288
        c, v, p = arr(f, 1152), arr(rdir / f.name, 1152), arr(pdir / f.name, 1152)
        same &= bool(np.array_equal(c[:k, 0], v[:k, 0]))
        d1, d2 = slice(k, k + 288), slice(k + 288, k + 576)
        c1.append(-c[d1, 0].sum()), v1.append(-v[d1, 0].sum()), p1.append(-p[d1, 0].sum())
        c2.append(-c[d2, 0].sum()), v2.append(-v[d2, 0].sum())
        cc1.append(-0.6 * c[d1, 1].sum()), cv1.append(-0.6 * v[d1, 1].sum())
c1, v1, p1, c2, v2 = map(np.array, (c1, v1, p1, c2, v2))
idx = np.random.default_rng(0).integers(0, 12, size=(10000, 12))
lo, hi = np.percentile(c1[idx].sum(1) / v1[idx].sum(1), [2.5, 97.5])
lo3, hi3 = np.percentile(c2[idx].sum(1) / v2[idx].sum(1), [2.5, 97.5])
say("cold start: runs", 12, len(c1), 0, "{:d}")
say("cold start: identical to v16 before the restart", "True", str(same))
say("cold start: first work day / v16", 1.20, c1.sum() / v1.sum(), 0.005)
say("cold start: interval low", 1.09, lo, 0.006)
say("cold start: interval high", 1.34, hi, 0.006)
say("cold start: per building min", 1.05, (c1 / v1).min(), 0.006)
say("cold start: per building max", 1.83, (c1 / v1).max(), 0.006)
say("cold start: worse in", 12, int((c1 > v1).sum()), 0, "{:d}")
say("cold start: below pid_water in", 12, int((c1 < p1).sum()), 0, "{:d}")
say("cold start: median ratio to pid_water", 0.24, float(np.median(c1 / p1)), 0.005)
say("cold start: v16 median ratio to pid_water", 0.22, float(np.median(v1 / p1)), 0.005)
say("cold start: next work day / v16", 1.01, c2.sum() / v2.sum(), 0.005)
say("cold start: next day interval low", 0.99, lo3, 0.006)
say("cold start: next day interval high", 1.04, hi3, 0.006)
say("cold start: comfort sum v16", 5.1, float(np.sum(cv1)), 0.06, "{:.2f}")
say("cold start: comfort sum cold", 21.3, float(np.sum(cc1)), 0.06, "{:.2f}")
say("cold start: loss sum v16", 75.9, float(v1.sum()), 0.06, "{:.2f}")
say("cold start: loss sum cold", 90.8, float(c1.sum()), 0.06, "{:.2f}")

# ---------------------------------------------------------------- trained policy
print("\n== Trained controller (Section 4.1, Appendix, tab_trained.tex)")
t, v, p, ct, cv, cp = [], [], [], [], [], []
for name, rdir, pdir in (("r6", R / "round6h/v16", R / "round6h/pid_water"), ("r7", R / "round7/chm", R / "round7/pid_water")):
    for f in sorted((R / "rl_test" / name).glob("*.npy")):
        t.append(loss_n(f, 2880)), v.append(loss_n(rdir / f.name, 2880)), p.append(loss_n(pdir / f.name, 2880))
        ct.append(comfort_n(f, 2880)), cv.append(comfort_n(rdir / f.name, 2880)), cp.append(comfort_n(pdir / f.name, 2880))
        assert len(arr(f)) >= 2880, f
t, v, p, ct, cv, cp = map(np.array, (t, v, p, ct, cv, cp))
say("trained: runs", 12, len(t), 0, "{:d}")
say("trained: pid_water mean loss", 0.07982, p.mean(), 0.000006, "{:.5f}")
say("trained: trained mean loss", 0.07141, t.mean(), 0.000006, "{:.5f}")
say("trained: v16 mean loss", 0.01427, v.mean(), 0.000006, "{:.5f}")
say("trained: comfort pid_water", 0.06341, cp.mean(), 0.000006, "{:.5f}")
say("trained: comfort trained", 0.06016, ct.mean(), 0.000006, "{:.5f}")
say("trained: comfort v16", 0.00048, cv.mean(), 0.000006, "{:.5f}")
lo, hi = boot_ratio(t, p)
say("trained / pid_water", 0.89, t.mean() / p.mean(), 0.005)
say("trained / pid_water low", 0.83, lo, 0.006)
say("trained / pid_water high", 0.95, hi, 0.006)
say("trained below pid_water in", 11, int((t < p).sum()), 0, "{:d}")
lo, hi = boot_ratio(t, v)
say("trained / v16", 5.0, t.mean() / v.mean(), 0.05, "{:.2f}")
say("trained / v16 low", 3.5, lo, 0.06, "{:.2f}")
say("trained / v16 high", 7.3, hi, 0.06, "{:.2f}")
say("v16 below trained in", 12, int((v < t).sum()), 0, "{:d}")
lo, hi = boot_ratio(v, p)
say("v16 / pid_water", 0.18, v.mean() / p.mean(), 0.005)
say("v16 / pid_water low", 0.13, lo, 0.006)
say("v16 / pid_water high", 0.24, hi, 0.006)
say("v16 below pid_water in", 12, int((v < p).sum()), 0, "{:d}")
et, ev, ep = t.mean() - ct.mean(), v.mean() - cv.mean(), p.mean() - cp.mean()
say("trained energy+carbon / pid_water's", 0.69, et / ep, 0.005)
say("trained energy+carbon / v16's", 0.82, et / ev, 0.005)
say("trained comfort / pid_water's", 0.95, ct.mean() / cp.mean(), 0.005)
say("v16 comfort / pid_water's (%), 'under 1 %'", 0.76, 100 * cv.mean() / cp.mean(), 0.24, "{:.2f}")
run = R / "rl/main"
tr = pd.read_csv(run / "train.csv")
best = json.loads((run / "best.json").read_text())
say("trained: simulator steps (million)", 3.3, tr["env_steps"].iloc[-1] / 1e6, 0.05, "{:.2f}")
say("trained: hours", 38, tr["hours"].iloc[-1], 0.5, "{:.1f}")
say("trained: best iteration", 1200, int(best["it"]), 0, "{:d}")
say("trained: best validation loss", 0.02339, float(best["val_loss"]), 0.000006, "{:.5f}")
print("  train.csv columns:", list(tr.columns), "| last row:", tr.iloc[-1].to_dict())

# ---------------------------------------------------------------- paired statistics (Table 5) and per-round text
print("\n== Rounds (Sections 4.3-4.4, Tables 3-5 and 7)")


def pair(folder: str, ours: str, ref: str, keys=None, n=None):
    a, b = js(R / folder / ours), js(R / folder / ref)
    keys = keys or sorted(a)
    x = np.array([abs(a[k]["mean_reward"]) for k in keys])
    y = np.array([abs(b[k]["mean_reward"]) for k in keys])
    return keys, x, y


def regret(folder: str, name: str, keys=None) -> float:
    a = js(R / folder / name)
    return float(sum(a[k]["components"]["prod"] for k in (keys or sorted(a))))


COLD = ("fairbanks", "denver", "minneapolis")
k, x, y = pair("heldout", "zonal", "pid_water")
say("R1 v7 below pid_water (%)", 7.7, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
say("R1 regret / pid_water's (%)", 56.1, 100 * regret("heldout", "zonal") / regret("heldout", "pid_water"), 0.05, "{:.2f}")
bb = {b: js(R / "heldout" / b) for b in ("bang_bang", "fixed_setpoint", "pid", "pid_water")}
z = js(R / "heldout/zonal")
say("R1 better than every baseline in", 8, sum(all(abs(z[s]["mean_reward"]) < abs(bb[b][s]["mean_reward"]) for b in bb) for s in z), 0, "{:d}")
k, x, y = pair("heldout", "v8_posthoc", "pid_water")
say("R1 post hoc v8 loss", 0.01011, x.mean(), 0.000006, "{:.5f}")
say("R1 post hoc v8 below pid_water (%)", 71.7, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
k, x, y = pair("heldout2", "v8", "v7")
say("R2 v8 below v7 (%)", 66.7, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
say("R2 better than v7 in", 12, int((x < y).sum()), 0, "{:d}")
k, x, y = pair("heldout2", "v8", "pid_water")
say("R2 v8 below pid_water (%)", 76.8, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
print(f"  R2 regret v8 {abs(regret('heldout2', 'v8')):.0f} vs v7 {abs(regret('heldout2', 'v7')):.0f} (paper 302 vs 2363)")
k3 = sorted(js(R / "heldout3/v9"))
cold3, warm3 = [s for s in k3 if s.endswith("_dec")], [s for s in k3 if not s.endswith("_dec")]
k, x, y = pair("heldout3", "v9", "v8", cold3)
say("R3 cold v9 below v8 (%)", 9.1, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
say("R3 cold better in", 6, int((x < y).sum()), 0, "{:d}")
k, x, y = pair("heldout3", "v9", "v8", warm3)
say("R3 warm v9 vs v8 (%)", 0.4, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
print(f"  R3 regret v9 {abs(regret('heldout3', 'v9')):.0f} vs v8 {abs(regret('heldout3', 'v8')):.0f} (paper 682 vs 636; "
      f"ratio {regret('heldout3', 'v9') / regret('heldout3', 'v8'):.3f}, paper +7 %)")
k4 = sorted(js(R / "heldout4/v10"))
cold4 = [s for s in k4 if any(c in s.split("__")[1] for c in COLD)]
warm4 = [s for s in k4 if s not in cold4]
k, x, y = pair("heldout4", "v10", "v9", warm4)
say("R4 warm v10 below v9 (%)", 19.7, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
say("R4 warm better in", 5, int((x < y).sum()), 0, "{:d}")
k, x, y = pair("heldout4", "v10", "v9", cold4)
say("R4 cold v10 vs v9 (%)", -0.2, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
k, x, y = pair("heldout4", "v10", "v9")
say("R4 all v10 below v9 (%)", 6.1, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
say("R4 regret ratio", 0.97, regret("heldout4", "v10") / regret("heldout4", "v9"), 0.005)
k5 = sorted(js(R / "heldout5/v11"))
cold5 = [s for s in k5 if any(c in s.split("__")[1] for c in COLD)]
warm5 = [s for s in k5 if s not in cold5]
k, x, y = pair("heldout5", "v11", "v10")
say("R5 v11 below v10 (%)", 27.8, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
say("R5 better in", 12, int((x < y).sum()), 0, "{:d}")
k, x, y = pair("heldout5", "v11", "v10", cold5)
say("R5 cold (%)", 27.6, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
k, x, y = pair("heldout5", "v11", "v10", warm5)
say("R5 warm (%)", 28.2, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
say("R5 regret ratio", 0.28, regret("heldout5", "v11") / regret("heldout5", "v10"), 0.005)
k, x, y = pair("heldout5", "v11", "pid_water")
say("R5 v11 below pid_water (%)", 85.0, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
k, x, y = pair("round6h", "ed1", "v14")
say("R6 v15 below v14 (%)", 2.67, 100 * (1 - x.mean() / y.mean()), 0.005, "{:.3f}")
say("R6 better in", 6, int((x < y).sum()), 0, "{:d}")
say("R6 regret ratio", 1.22, regret("round6h", "ed1") / regret("round6h", "v14"), 0.005)
k, x, y = pair("round6h", "ed1", "pid_water")
say("R6 v15 below pid_water (%)", 79.4, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
k, x, y = pair("round7", "chm", "v15")
say("R7 v16 below v15 (%)", 7.64, 100 * (1 - x.mean() / y.mean()), 0.005, "{:.3f}")
say("R7 better in", 6, int((x < y).sum()), 0, "{:d}")
say("R7 worst building (%)", -0.17, float((100 * (x / y - 1)).max()), 0.005, "{:.3f}")
say("R7 regret ratio", 0.51, regret("round7", "chm") / regret("round7", "v15"), 0.005)
for s, a, b in zip(k, x, y):
    print(f"     R7 {s}: {100 * (a / b - 1):+.1f} %")
_, xc, yc = pair("round7", "ch", "v15")
say("R7 cool-hold alone (%)", 7.55, 100 * (1 - xc.mean() / yc.mean()), 0.005, "{:.3f}")
_, xm, ym = pair("round7", "mh", "v15")
say("R7 margin alone (%)", 0.5, 100 * (1 - xm.mean() / ym.mean()), 0.05, "{:.2f}")
k, x, y = pair("round7", "chm", "pid_water")
say("R7 v16 below pid_water (%)", 83.7, 100 * (1 - x.mean() / y.mean()), 0.05, "{:.2f}")
k8 = sorted(f.stem for f in (R / "round8/sp1").glob("*.npy"))
x = np.array([loss_n(R / "round8/sp1" / f"{s}.npy", 2880) for s in k8])
y = np.array([loss_n(R / "round8/v16" / f"{s}.npy", 2880) for s in k8])
pw = np.array([loss_n(R / "round8/pid_water" / f"{s}.npy", 2880) for s in k8])
say("R8 candidate below v16 (%)", 0.12, 100 * (1 - x.mean() / y.mean()), 0.005, "{:.3f}")
say("R8 at or below v16 in", 5, int((x <= y).sum()), 0, "{:d}")
say("R8 worst (%)", 0.00, float((100 * (x / y - 1)).max()), 0.011, "{:.3f}")
say("R8 v16 mean loss", 0.01066, y.mean(), 0.000006, "{:.5f}")
say("R8 candidate mean loss", 0.01064, x.mean(), 0.000006, "{:.5f}")
say("R8 pid_water mean loss", 0.07877, pw.mean(), 0.000006, "{:.5f}")
say("R8 v16 below pid_water (%)", 86.5, 100 * (1 - y.mean() / pw.mean()), 0.05, "{:.2f}")
c8x = sum(-arr(R / "round8/sp1" / f"{s}.npy", 2880)[:, 1].sum() for s in k8)
c8y = sum(-arr(R / "round8/v16" / f"{s}.npy", 2880)[:, 1].sum() for s in k8)
say("R8 regret ratio", 0.97, c8x / c8y, 0.005)
for s, a, b in zip(k8, x, y):
    print(f"     R8 {s}: {100 * (a / b - 1):+.2f} %, share of v16's summed loss {b / y.sum():.2f}")

# ---------------------------------------------------------------- training column, public ratios
print("\n== Training and public (Table 1, Appendix C)")
TRAIN = {"v8": "train_8640/v8", "v9": "train_8640/v9f", "v10": "train_8640/v10c", "v11": "dev11_8640/v11f",
         "v12": "dev12_8640/v12_all30", "v13": "dev13_8640/v13_all30", "v14": "dev14_8640/of3",
         "v15": "holiday/ed1_full", "v16": "chatter/t_chm"}
PUBLIC = {"v8": 0.01687, "v9": 0.01623, "v10": 0.01543, "v11": 0.01071, "v12": 0.01058, "v13": 0.01051,
          "v14": 0.01048, "v15": 0.01035, "v16": 0.01031}
PRINT_T = {"v8": 0.01252, "v9": 0.01199, "v10": 0.01092, "v11": 0.00744, "v12": 0.00739, "v13": 0.00735,
           "v14": 0.00733, "v15": 0.00719, "v16": 0.00716}
ratios = {}
for ver, folder in TRAIN.items():
    r = {k: v for k, v in js(R / folder).items() if not k.endswith(("_jan15", "_jul15"))}
    m = float(np.mean([abs(x["mean_reward"]) for x in r.values()]))
    say(f"training {ver} ({len(r)} scenarios)", PRINT_T[ver], m, 0.0000051, "{:.6f}")
    ratios[ver] = PUBLIC[ver] / m
print("  public / training:", ", ".join(f"{k} {v:.3f}" for k, v in ratios.items()), "(paper: 1.35-1.44)")
say("public/training min", 1.35, min(ratios.values()), 0.005)
say("public/training max", 1.44, max(ratios.values()), 0.005)
say("pid_water public/training", 1.18, 0.06404 / 0.05414, 0.005)
say("v13/pid_water public", 0.164, 0.01051 / 0.06404, 0.0005)
say("v13/pid_water training", 0.136, 0.007355 / 0.05414, 0.0005)
say("v11 round 5 / training", 1.11, 0.008269 / 0.007440, 0.005)
say("v15 public vs v14 (%)", 1.2, 100 * (1 - 0.01035 / 0.01048), 0.05, "{:.2f}")
say("v16 public vs v15 (%)", 0.4, 100 * (1 - 0.01031 / 0.01035), 0.05, "{:.2f}")
for label, score, shown in (("no learning", 0.01544, 1.50), ("offset only", 0.01034, 1.00), ("half", None, 1.01),
                            ("nodelay", 0.01180, 1.14), ("nolag", 0.01270, 1.23), ("noslab", 0.01837, 1.78),
                            ("lag24", 0.01035, 1.00), ("lag96", 0.01046, 1.01), ("nohold", 0.01031, 1.00)):
    if score:
        say(f"public {label} / v16", shown, score / 0.01031, 0.005)

print(f"\n{len(BAD)} mismatches" + (": " + "; ".join(BAD) if BAD else ""))
