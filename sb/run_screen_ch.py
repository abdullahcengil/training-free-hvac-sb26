"""Cool-hold screen (docs/CHATTER.md; rule written before any run): chm = v15 + cool_hold 2 + margin_heat 0.30 on the
five cold scaled windows (with new v15 reference runs), the six cold and six hot full-size development windows (first
2880 steps) and the 30 shipped training scenarios at full length. Restartable (sb.memsched).

    python -m sb.run_screen_ch >> D:/SmartBuildings_data/screen_ch.log 2>&1
    python -m sb.run_screen_ch --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
V15 = json.loads((REPO / "submission/V15_PARAMS.json").read_text())
CHM = dict(V15, cool_hold=2, margin_heat=0.30)
POL15 = "D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy"
POLCH = "D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py:TransferPolicy"
DATA = Path("D:/SmartBuildings_data")
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
BIG = DATA / "bigdev/scenarios"
SCALED = DATA / "bigdev_scaled/scenarios"
OUT = DATA / "results/chatter"
REF_T = DATA / "results/holiday/ed1_full"
REF_F = DATA / "results/heatless/v15_bigdev"
REF_H = DATA / "results/bigdev/v14"
COLD = ["building_7001__chicago_jan15", "building_7002__helena_jan15", "building_7003__duluth_jan15",
        "building_7005__chicago_jan15", "building_7007__newyork_jan15", "building_7008__seattle_jan15"]
HOT = ["building_7001__dubai_jul15", "building_7002__lasvegas_jul15", "building_7003__houston_jul15",
       "building_7005__lasvegas_jul15", "building_7007__miami_jul15", "building_7008__chicago_jul15"]
SCOLD = ["building_7001__chicago_jan15", "building_7002__helena_jan15", "building_7003__duluth_jan15",
         "building_7007__newyork_jan15", "building_7008__seattle_jan15"]


def training() -> list[str]:
    return sorted(f"{d.parent.name}__{d.name}" for d in TRAIN.glob("building_train_*/*") if (d / "config.gin").exists())


def _job(pol: str, kw: dict, out: str, s: str, root: Path, steps: int) -> dict:
    return memsched.job({"policy": pol, "base": "none", "kwargs": kw, "out": str(OUT / out), "scenario": s,
                         "root": str(root)}, steps)


def jobs() -> list[dict]:
    s = [_job(pol, kw, out, x, SCALED, 2880) for x in SCOLD
         for pol, kw, out in ((POL15, V15, "s_v15"), (POLCH, CHM, "s_chm"))]
    f = [_job(POLCH, CHM, "f_chm", x, BIG, 2880) for x in COLD]
    h = [_job(POLCH, CHM, "h_chm", x, BIG, 2880) for x in HOT]
    t = [_job(POLCH, CHM, "t_chm", x, TRAIN, 8640) for x in training()]
    return s + f + h + t


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def terms(d: Path, s: str) -> tuple[float, float, float] | None:
    f = d / f"{s}.npy"
    if not f.exists():
        return None
    a = np.load(f).astype(float)
    # Stored terms: reward = 0.6 * regret (stored negative) - 0.2 * (energy cost + carbon) (stored positive).
    return -a[:, 0].mean(), -0.6 * a[:, 1].mean(), 0.2 * (a[:, 2].mean() + a[:, 3].mean())


def table(name: str, ref: Path, new: Path, scen: list[str], mark_mean: float | None, mark_worst: float) -> None:
    rows = [(s, terms(ref, s), terms(new, s)) for s in scen]
    rows = [r for r in rows if r[1] is not None and r[2] is not None]
    if not rows:
        print(f"{name}: no runs yet")
        return
    a = np.array([r[1][0] for r in rows])
    b = np.array([r[2][0] for r in rows])
    ch = 100 * (b / a - 1)
    mean = 100 * (b.mean() / a.mean() - 1)
    done = len(rows) == len(scen)
    ok = (mark_mean is None or mean <= mark_mean) and ch.max() <= mark_worst
    mm = "reported" if mark_mean is None else f"{mark_mean:+.1f} %"
    print(f"{name}: {len(rows)}/{len(scen)}, mean {b.mean():.6f} vs v15 {a.mean():.6f} ({mean:+.2f} %; mark {mm}), "
          f"better in {(ch < 0).sum()}, worst {ch.max():+.2f} % (mark +{mark_worst:.0f} %)"
          + (f"  {'PASS' if ok else 'FAIL'}" if done else ""))
    for (s, x, y), c in zip(rows, ch):
        print(f"    {s:38s} v15 {x[0]:.5f}  chm {y[0]:.5f}  ({c:+.2f} %)  comfort {x[1]:.5f}->{y[1]:.5f} "
              f"energy {x[2]:.5f}->{y[2]:.5f}")


def read() -> None:
    table("S (five cold scaled, 2880 steps)", OUT / "s_v15", OUT / "s_chm", SCOLD, None, 2.0)
    table("F (six cold full-size, 2880 steps)", REF_F, OUT / "f_chm", COLD, -1.0, 2.0)
    table("H (six hot full-size, 2880 steps)", REF_H, OUT / "h_chm", HOT, 0.1, 1.0)
    table("T (30 training, full length)", REF_T, OUT / "t_chm", training(), 0.1, 2.0)


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"screen CH starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("screen CH END")
    read()


if __name__ == "__main__":
    main()
