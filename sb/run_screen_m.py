"""Margin screen (docs/HEATLESS.md; rule written before any run): v15 + margin_heat 0.30 (mh30) on the 30 shipped
training scenarios at full length (against v15's recorded runs) and, with v15 itself, on the six cold full-size
development windows (first 2880 steps). Waits for the upside check of docs/SIZEGATE.md to end (three simulations at
most). Restartable (sb.memsched).

    python -m sb.run_screen_m >> D:/SmartBuildings_data/screen_m.log 2>&1
    python -m sb.run_screen_m --read
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
MH30 = dict(V15, margin_heat=0.30)
POL = "D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy"
DATA = Path("D:/SmartBuildings_data")
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
BIG = DATA / "bigdev/scenarios"
REF_T = DATA / "results/holiday/ed1_full"       # v15 on the 30 training scenarios, full length
OUT = DATA / "results/heatless"
UPSIDE_LOG = DATA / "sizegate_upside.log"
COLD = ["building_7001__chicago_jan15", "building_7002__helena_jan15", "building_7003__duluth_jan15",
        "building_7005__chicago_jan15", "building_7007__newyork_jan15", "building_7008__seattle_jan15"]


def training() -> list[str]:
    return sorted(f"{d.parent.name}__{d.name}" for d in TRAIN.glob("building_train_*/*") if (d / "config.gin").exists())


def jobs() -> list[dict]:
    full = [memsched.job({"policy": POL, "base": "none", "kwargs": kw, "out": str(OUT / f"{arm}_bigdev"),
                          "scenario": s, "root": str(BIG)}, 2880)
            for s in COLD for arm, kw in (("v15", V15), ("mh30", MH30))]
    train = [memsched.job({"policy": POL, "base": "none", "kwargs": MH30, "out": str(OUT / "mh30_train"),
                           "scenario": s, "root": str(TRAIN)}, 8640) for s in training()]
    return full + train        # full-size first (larger, so they start while memory is free)


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def loss(d: Path, s: str) -> float | None:
    f = d / f"{s}.json"
    return -json.loads(f.read_text())["mean_reward"] if f.exists() else None


def comfort_energy(d: Path, s: str) -> tuple[float, float] | None:
    f = d / f"{s}.npy"
    if not f.exists():
        return None
    a = np.load(f).astype(float)
    # Stored terms: reward = 0.6 * regret (stored negative) - 0.2 * (energy cost + carbon) (stored positive).
    return -0.6 * a[:, 1].mean(), 0.2 * (a[:, 2].mean() + a[:, 3].mean())


def table(name: str, ref: Path, new: Path, scen: list[str], mark_mean: float, mark_worst: float) -> None:
    rows = [(s, loss(ref, s), loss(new, s)) for s in scen]
    rows = [r for r in rows if r[1] is not None and r[2] is not None]
    if not rows:
        print(f"{name}: no runs yet")
        return
    a = np.array([r[1] for r in rows])
    b = np.array([r[2] for r in rows])
    ch = 100 * (b / a - 1)
    mean = 100 * (b.mean() / a.mean() - 1)
    done = len(rows) == len(scen)
    ok = mean <= mark_mean and ch.max() <= mark_worst
    print(f"{name}: {len(rows)}/{len(scen)}, mean {b.mean():.6f} vs v15 {a.mean():.6f} ({mean:+.2f} %; mark "
          f"{mark_mean:+.1f} %), better in {(ch < 0).sum()}, worst {ch.max():+.2f} % (mark +{mark_worst:.0f} %)"
          + (f"  {'PASS' if ok else 'FAIL'}" if done else ""))
    for s, x, y in rows:
        ce_a, ce_b = comfort_energy(ref, s), comfort_energy(new, s)
        split = (f"  comfort {ce_a[0]:.5f}->{ce_b[0]:.5f} energy {ce_a[1]:.5f}->{ce_b[1]:.5f}"
                 if ce_a and ce_b else "")
        print(f"    {s:38s} v15 {x:.5f}  mh30 {y:.5f}  ({100 * (y / x - 1):+.2f} %){split}")
    if name.startswith("T"):
        for city in ("atlanta", "denver", "fairbanks", "phoenix", "singapore"):
            sel = [i for i, r in enumerate(rows) if f"__{city}" in r[0]]
            if sel:
                print(f"    {city:10s} {100 * (b[sel].sum() / a[sel].sum() - 1):+.2f} % over {len(sel)}")


def read() -> None:
    table("T (30 training, full length)", REF_T, OUT / "mh30_train", training(), 0.1, 2.0)
    table("F (six cold full-size, 2880 steps)", OUT / "v15_bigdev", OUT / "mh30_bigdev", COLD, -1.0, 2.0)


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    while "upside END" not in (UPSIDE_LOG.read_text(encoding="utf-8", errors="replace") if UPSIDE_LOG.exists()
                               else ""):
        time.sleep(60)
    say(f"screen M starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("screen M END")
    read()


if __name__ == "__main__":
    main()
