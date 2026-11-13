"""Cold start on a work day (docs/COLD_START.md; plan written and timestamped before any run). v16 restarted from scratch
at 06:00 on the first work day of each of the twelve full-size windows of rounds 6 and 7, against v16's and pid_water's
existing runs on the same steps. Post hoc and descriptive.

    python -m sb.run_coldstart --check   known-answer check: cold_step -1 must reproduce v16 for 288 steps
    python -m sb.run_coldstart >> D:/SmartBuildings_data/coldstart.log 2>&1
    python -m sb.run_coldstart --read
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
V16 = json.loads((REPO / "submission/V16_PARAMS.json").read_text())
POLICY = f"{REPO / 'policies/zonal_v16_coldstart.py'}:ColdStartPolicy"
DATA = Path("D:/SmartBuildings_data")
R = DATA / "results"
SETS = [("r6", DATA / "round6h/scenarios", R / "round6h/v16", R / "round6h/pid_water"),
        ("r7", DATA / "round7/scenarios", R / "round7/chm", R / "round7/pid_water")]
OUT = R / "coldstart"
STEPS = 1152   # Sunday 06:00 + 4 days: the first work day and the next one fit even when Monday is a holiday
DAY = 288
HOL = set(USFederalHolidayCalendar().holidays("2022-01-01", "2024-12-31").date)


def scenarios(rdir: Path) -> list[str]:
    """The scenarios of the round: those with an existing v16 run (rejected seeds have no run)."""
    return sorted(f.stem for f in rdir.glob("*.npy"))


def cold_step(root: Path, s: str) -> int:
    b, w = s.split("__")
    g = (root / b / w / "config.gin").read_text()
    st = pd.Timestamp(re.search(r"start_timestamp = '([^']+)'", g).group(1))
    assert st.hour == 6 and st.minute == 0, (s, st)
    for d in range(1, 7):
        t = st + pd.Timedelta(days=d)
        if t.weekday() < 5 and t.date() not in HOL:
            return d * DAY
    raise AssertionError(s)


def jobs() -> list[dict]:
    out = []
    for name, root, rdir, _ in SETS:
        for s in scenarios(rdir):
            kw = dict(V16, cold_step=cold_step(root, s))
            out.append(memsched.job({"policy": POLICY, "base": "none", "kwargs": kw, "out": str(OUT / name),
                                     "scenario": s, "root": str(root)}, STEPS))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def check() -> None:
    """Known-answer check: never restarting must give v16's rewards exactly (first 288 steps of one building)."""
    name, root, rdir, _ = SETS[1]
    s = "building_7802__helena_feb19"
    j = memsched.job({"policy": POLICY, "base": "none", "kwargs": dict(V16, cold_step=-1),
                      "out": str(OUT / "check"), "scenario": s, "root": str(root)}, DAY)
    from sb.run import run_job

    r = run_job((j["policy"], j["scen"], j["out"], j["steps"], True, j["kwargs"]))
    print("run_job returned", r)
    a = np.load(rdir / f"{s}.npy").astype(float)[:DAY]
    b = np.load(OUT / "check" / f"{s}.npy").astype(float)[:DAY]
    print("identical to v16 for", DAY, "steps:", np.array_equal(a[:, 0], b[:, 0]))
    assert np.array_equal(a[:, 0], b[:, 0])


def read() -> None:
    rows = []
    for name, root, rdir, pdir in SETS:
        for s in scenarios(rdir):
            f = OUT / name / f"{s}.npy"
            if not f.exists():
                continue
            k = cold_step(root, s)
            c = np.load(f).astype(float)[:STEPS]
            v = np.load(rdir / f"{s}.npy").astype(float)[:STEPS]
            p = np.load(pdir / f"{s}.npy").astype(float)[:STEPS]
            before = np.array_equal(c[:k, 0], v[:k, 0])
            d1 = slice(k, k + DAY)
            d2 = slice(k + DAY, k + 2 * DAY)
            L = lambda a, d: float(-a[d, 0].sum())
            C = lambda a, d: float(-0.6 * a[d, 1].sum())
            rows.append(dict(s=s, k=k, before=before, c1=L(c, d1), v1=L(v, d1), p1=L(p, d1), c2=L(c, d2), v2=L(v, d2),
                             p2=L(p, d2), cc1=C(c, d1), cv1=C(v, d1)))
            r = rows[-1]
            print(f"{s:36s} restart step {k:4d} same before: {before}  first work day loss: cold {r['c1']:.3f} "
                  f"v16 {r['v1']:.3f} pid_water {r['p1']:.3f} (cold/v16 {r['c1'] / r['v1']:.3f}, cold/pid "
                  f"{r['c1'] / r['p1']:.3f}); next work day cold/v16 {r['c2'] / r['v2']:.3f}; comfort term "
                  f"{r['cv1']:.3f} -> {r['cc1']:.3f}")
    if not rows:
        return
    g = lambda k: np.array([r[k] for r in rows])
    n = len(rows)
    idx = np.random.default_rng(0).integers(0, n, size=(10000, n))
    m1 = g("c1").sum() / g("v1").sum()
    lo, hi = np.percentile(g("c1")[idx].sum(1) / g("v1")[idx].sum(1), [2.5, 97.5])
    m3 = g("c2").sum() / g("v2").sum()
    lo3, hi3 = np.percentile(g("c2")[idx].sum(1) / g("v2")[idx].sum(1), [2.5, 97.5])
    print(f"== {n} of 12 buildings; all identical to v16 before the restart: {all(r['before'] for r in rows)}")
    print(f"== M1 first work day, cold / v16 (ratio of sums): {m1:.3f} (95 % CI {lo:.3f}-{hi:.3f}); worse than v16 in "
          f"{int((g('c1') > g('v1')).sum())}; per-building ratio median {np.median(g('c1') / g('v1')):.3f}, "
          f"range {(g('c1') / g('v1')).min():.3f}-{(g('c1') / g('v1')).max():.3f}")
    print(f"== M2 below pid_water on that day: {int((g('c1') < g('p1')).sum())} of {n}; ratio cold/pid_water "
          f"(ratio of sums) {g('c1').sum() / g('p1').sum():.3f}, median {np.median(g('c1') / g('p1')):.3f}; v16/pid_water "
          f"median {np.median(g('v1') / g('p1')):.3f}")
    print(f"== M3 next work day, cold / v16 (ratio of sums): {m3:.3f} (95 % CI {lo3:.3f}-{hi3:.3f})")
    print(f"== comfort term on the first work day: v16 {g('cv1').sum():.3f}, cold {g('cc1').sum():.3f}")


def main() -> None:
    if "--check" in sys.argv:
        check()
        return
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"cold start starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("cold start END")
    read()


if __name__ == "__main__":
    main()
