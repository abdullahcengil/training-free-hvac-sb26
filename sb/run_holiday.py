"""Empty-holiday screen (docs/HOLIDAY.md; option and rule written before any run): frozen v14 with empty_day on ten
development windows that hold a weekday US federal holiday, each from its start until two days after its first
holiday; v14's own per-step rewards in results/dev14_8640/of3 are the reference. Restartable (sb.memsched).

    python -m sb.run_holiday --read
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
V14 = json.loads((REPO / "submission/V14_PARAMS.json").read_text())
POL = "D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy"
DATA = Path("D:/SmartBuildings_data")
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
STRESS = DATA / "stress/scenarios"
REF = DATA / "results/dev14_8640/of3"
OUT = DATA / "results/holiday"
OPT = {"empty_day": 1, "empty_h": 1.0}
SCEN = ["building_train_7__duluth_jan15", "building_train_1__chicago_jan15", "building_train_2__sanfrancisco_jan15",
        "building_train_8__dubai_jan15", "building_train_1__fairbanks_1", "building_train_7__singapore_6",
        "building_train_5__fairbanks_5", "building_train_7__denver_5", "building_train_2__denver_8",
        "building_train_2__phoenix_6"]
HOL = set(USFederalHolidayCalendar().holidays("2023-01-01", "2023-12-31").date)


def root(s: str) -> Path:
    b, w = s.split("__")
    return TRAIN if (TRAIN / b / w).exists() else STRESS


def start(s: str) -> pd.Timestamp:
    b, w = s.split("__")
    txt = (root(s) / b / w / "config.gin").read_text()
    return pd.Timestamp(re.search(r"start_timestamp\s*=\s*'([^']+)'", txt).group(1))


def first_holiday_step(s: str) -> int:
    """Step at which the first weekday holiday starts (local midnight)."""
    t0 = start(s)
    ts = t0 + pd.to_timedelta(np.arange(8640) * 5, unit="min")
    hd = np.array([t.date() in HOL and t.weekday() < 5 for t in ts])
    return int(np.argmax(hd))


def steps(s: str) -> int:
    """From the start until the end of the second work day after the first holiday (whole days from 06:00)."""
    t0 = start(s)
    d = (t0 + pd.Timedelta(minutes=5 * first_holiday_step(s))).normalize()
    work = 0
    while work < 2:
        d += pd.Timedelta(days=1)
        if d.weekday() < 5 and d.date() not in HOL:
            work += 1
    end = d + pd.Timedelta(days=1, hours=6)   # 06:00 after that work day
    return int((end - t0) / pd.Timedelta(minutes=5))


def jobs() -> list[dict]:
    out = []
    for s in SCEN:
        j = {"policy": POL, "base": "none", "kwargs": dict(V14, **OPT), "out": str(OUT / "ed1"), "scenario": s}
        if root(s) == STRESS:
            j["root"] = str(STRESS)
        out.append(memsched.job(j, steps(s)))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


POL16 = "D:/SmartBuildings_data/frozen/zonal_v16dev.py:TransferPolicy"


def v16_jobs() -> list[dict]:
    """v16 screen (docs/HOLIDAY.md, 'v16 development'): v15 plus empty_cmv 1, same windows and lengths as the screen."""
    out = []
    for s in SCEN:
        j = {"policy": POL16, "base": "none", "kwargs": dict(V14, **OPT, empty_cmv=1), "out": str(OUT / "v16cmv"),
             "scenario": s}
        if root(s) == STRESS:
            j["root"] = str(STRESS)
        out.append(memsched.job(j, steps(s)))
    return out


def v16_plan() -> tuple[list[dict], list[dict]]:
    return [j for j in v16_jobs() if not Path(j["result"]).exists()], []


def read_v16() -> None:
    rows = []
    for s in SCEN:
        f = OUT / "v16cmv" / f"{s}.npy"
        if not f.exists():
            continue
        new = -np.load(f).astype(float)[:, 0]
        v15 = -np.load(OUT / "ed1" / f"{s}.npy").astype(float)[:, 0]
        ref_all = -np.load(REF / f"{s}.npy").astype(float)[:, 0]
        d = (new.sum() - v15.sum()) / ref_all.sum()
        k = first_holiday_step(s) + 7 * 12   # 07:00 on the holiday, when the rule fires
        same = float(np.max(np.abs(new[:k] - v15[:k])))
        rows.append(d)
        print(f"{s:38s} change of the 30-day loss against v15 {100 * d:+.3f} %  (identity to 07:00: {same:.1e})")
    if rows:
        r = np.array(rows)
        verdict = ""
        if len(rows) == len(SCEN):
            verdict = "WORTH A FULL CHECK" if r.mean() <= -0.001 and r.max() <= 0.003 else "no"
        print(f"v16 screen {len(rows)}/{len(SCEN)}: mean {100 * r.mean():+.3f} %, worst {100 * r.max():+.3f} % {verdict}")


def full_jobs() -> list[dict]:
    """Second step of docs/HOLIDAY.md: all 70 development windows at full length (8640 steps), the windows with a
    weekday holiday first."""
    dev = json.loads((REPO / "sb/jobs_v14_full.json").read_text())
    hol = {s for s in (j["scenario"] for j in dev) if has_holiday(s)}
    out = []
    for j in sorted(dev, key=lambda j: j["scenario"] not in hol):
        k = {"policy": POL, "base": "none", "kwargs": dict(V14, **OPT), "out": str(OUT / "ed1_full"),
             "scenario": j["scenario"]}
        if "root" in j:
            k["root"] = j["root"]
        out.append(memsched.job(k, 8640))
    return out


def full_plan() -> tuple[list[dict], list[dict]]:
    return [j for j in full_jobs() if not Path(j["result"]).exists()], []


def has_holiday(s: str) -> bool:
    t0 = start(s)
    days = {(t0 + pd.Timedelta(days=d)).date() for d in range(30)}
    return any(d in HOL and pd.Timestamp(d).weekday() < 5 for d in days)


def read_full() -> None:
    rows = []
    for j in full_jobs():
        s = Path(j["result"]).stem
        f = Path(j["result"])
        if not f.exists():
            continue
        new = -json.loads(f.read_text())["mean_reward"]
        ref = -json.loads((REF / f"{s}.json").read_text())["mean_reward"]
        rows.append((s, ref, new, has_holiday(s)))
    if not rows:
        print("full: no runs yet")
        return
    a = np.array([r[1] for r in rows])
    b = np.array([r[2] for r in rows])
    ch = 100 * (b / a - 1)
    verdict = ""
    if len(rows) == len(full_jobs()):
        verdict = "PASS" if b.mean() <= 0.997 * a.mean() and ch.max() <= 1.0 else "FAIL"
    print(f"full: {len(rows)}/{len(full_jobs())}, mean {b.mean():.6f} vs v14 {a.mean():.6f} "
          f"({100 * (b.mean() / a.mean() - 1):+.2f} %), better in {(ch < -1e-9).sum()}, identical in "
          f"{(np.abs(ch) <= 1e-9).sum()}, worst {ch.max():+.2f} % {verdict}")
    for (s, x, y, h), c in zip(rows, ch):
        if abs(c) > 1e-9 or h:
            print(f"    {s:40s} {'holiday' if h else '       '} v14 {x:.5f}  ed1 {y:.5f}  ({c:+.2f} %)")
    # The change split by reward term over the windows with a holiday (per-step columns: reward, productivity,
    # energy cost, carbon; reward = 0.6 p - 0.2 E - 0.2 C).
    split, comfort, base = np.zeros(3), np.zeros(2), 0.0
    for s, _, _, h in rows:
        if not h:
            continue
        new, ref = (np.load(d / f"{s}.npy").astype(float) for d in (OUT / "ed1_full", REF))
        terms = [np.c_[-0.6 * x[:, 1], 0.2 * x[:, 2], 0.2 * x[:, 3]].sum(0) for x in (new, ref)]
        split += terms[0] - terms[1]
        comfort += [terms[1][0], terms[0][0]]
        base += -ref[:, 0].sum()
    if base:
        print(f"holiday windows: summed loss {100 * split.sum() / base:+.2f} % (comfort {split[0]:+.3f}, cost "
              f"{split[1]:+.3f}, carbon {split[2]:+.3f}; v14 total {base:.1f}); comfort term v14 {comfort[0]:.3f} -> "
              f"ed1 {comfort[1]:.3f} ({comfort[1] / comfort[0]:.2f} times)")


def read() -> None:
    rows = []
    for s in SCEN:
        f = OUT / "ed1" / f"{s}.npy"
        if not f.exists():
            print(f"{s}: not run yet")
            continue
        new = -np.load(f).astype(float)[:, 0]
        ref_all = -np.load(REF / f"{s}.npy").astype(float)[:, 0]
        n = len(new)
        ref = ref_all[:n]
        k = first_holiday_step(s) + 6 * 12   # 06:00 on the holiday
        same = float(np.max(np.abs(new[:k] - ref[:k]))) if k else 0.0
        d = (new.sum() - ref.sum()) / ref_all.sum()
        day = slice(k, k + 288)
        nxt = slice(k + 288, min(k + 576, n))
        rows.append(d)
        print(f"{s:38s} {n:5d} steps  identity before holiday {same:.1e}  change of the 30-day loss {100 * d:+.2f} %  "
              f"(holiday {ref[day].sum():.3f} -> {new[day].sum():.3f}, next day {ref[nxt].sum():.3f} -> "
              f"{new[nxt].sum():.3f}, rest {ref[min(k + 576, n):].sum():.3f} -> {new[min(k + 576, n):].sum():.3f})")
    if rows:
        r = np.array(rows)
        verdict = ""
        if len(rows) == len(SCEN):
            verdict = "PROMISING" if r.mean() <= -0.005 and r.max() <= 0.01 else "no"
        print(f"{len(rows)}/{len(SCEN)}: mean change {100 * r.mean():+.2f} %, worst {100 * r.max():+.2f} % {verdict}")


if __name__ == "__main__":
    if "--read" in sys.argv:
        read()
        read_full()
    elif "--full-count" in sys.argv:
        print(len(full_jobs()), sum(has_holiday(Path(j["result"]).stem) for j in full_jobs()), "with holidays")
    else:
        for j in jobs():
            print(j["key"], j["steps"])
