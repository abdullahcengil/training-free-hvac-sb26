"""Deep-cold size test (docs/BIG_BUILDINGS.md, rule of 29 Oct): frozen v14 on the eight size-test buildings at full
size and scaled, in fairbanks_nov21 and duluth_jan25 (sb/make_coldsize.py), first 2880 steps; 16 pairs. Restartable:
finished runs are skipped (sb.memsched).

    python -m sb.run_coldsize >> D:/SmartBuildings_data/coldsize.log 2>&1
    python -m sb.run_coldsize --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched
from sb.make_coldsize import BUILDINGS, WINDOWS

REPO = Path(__file__).resolve().parents[1]
V14 = json.loads((REPO / "submission/V14_PARAMS.json").read_text())
POL = "D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy"
DATA = Path("D:/SmartBuildings_data")
OUT = DATA / "results/coldsize"
STEPS = 2880


def jobs() -> list[dict]:
    out = []
    for w in WINDOWS:
        for b in BUILDINGS:
            for size in ("full", "scaled"):      # pairs finish together, so a stopped run still reads
                out.append(memsched.job({"policy": POL, "base": "none", "kwargs": V14, "out": str(OUT / size),
                                         "scenario": f"{b}__{w}", "root": str(DATA / "coldsize" / size / "scenarios")},
                                        STEPS))
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def parts(f: Path) -> np.ndarray:
    """Mean per step over the first 2880 steps: [comfort occupied, comfort empty, energy+carbon occupied,
    energy+carbon empty] (record columns as in sb/size_parts.py)."""
    a = np.load(f).astype(float)[:STEPS]
    occ = a[:, 4] > 0
    comfort = -0.6 * a[:, 1]
    ec = 0.2 * (a[:, 2] + a[:, 3])
    return np.array([comfort[occ].sum(), comfort[~occ].sum(), ec[occ].sum(), ec[~occ].sum()]) / len(a)


def read() -> None:
    rows, names, prt = [], [], []
    for w in WINDOWS:
        for b in BUILDINGS:
            f = {s: OUT / s / f"{b}__{w}.json" for s in ("full", "scaled")}
            if not all(p.exists() for p in f.values()):
                continue
            lf, ls = (-json.loads(f[s].read_text())["mean_reward"] for s in ("full", "scaled"))
            rows.append((lf, ls))
            names.append(f"{b}__{w}")
            prt.append(parts(f["full"].with_suffix(".npy")) - parts(f["scaled"].with_suffix(".npy")))
            print(f"{b} {w:16s} full {lf:.5f}  scaled {ls:.5f}  x{lf / ls:.2f}")
    if len(rows) < 2:
        print(f"{len(rows)} of {len(BUILDINGS) * len(WINDOWS)} pairs done")
        return
    t = np.array(rows)
    k = t[:, 0].mean() / t[:, 1].mean()
    rng = np.random.default_rng(0)
    ks = [(lambda s: s[:, 0].mean() / s[:, 1].mean())(t[rng.integers(0, len(t), len(t))]) for _ in range(10_000)]
    lo, hi = np.percentile(ks, [2.5, 97.5])
    for w in WINDOWS:
        m = np.array([n.endswith(w) for n in names])
        if m.any():
            print(f"{w}: {m.sum()} pairs, ratio of means {t[m, 0].mean() / t[m, 1].mean():.2f}")
    d = np.array(prt).mean(axis=0)
    extra = t[:, 0].mean() - t[:, 1].mean()
    ec_share = (d[2] + d[3]) / extra if extra > 0 else float("nan")
    print(f"{len(t)} of {len(BUILDINGS) * len(WINDOWS)} pairs: full {t[:, 0].mean():.5f}, scaled {t[:, 1].mean():.5f}, "
          f"ratio of means {k:.2f} (95 % interval {lo:.2f}-{hi:.2f})")
    print(f"extra loss per step {extra:+.5f}: comfort occupied {d[0]:+.5f}, comfort empty {d[1]:+.5f}, "
          f"energy+carbon occupied {d[2]:+.5f}, empty {d[3]:+.5f} (energy+carbon share {ec_share:.2f})")
    if len(t) == len(BUILDINGS) * len(WINDOWS):
        if k >= 1.30 and ec_share >= 0.5:
            verdict = "SIZE EXPLAINS THE HEATING PART"
        elif k <= 1.10:
            verdict = "SIZE DOES NOT EXPLAIN IT"
        else:
            verdict = "PARTIAL"
        print("reading (rule of 29 Oct):", verdict)


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"coldsize starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("coldsize END")
    read()


if __name__ == "__main__":
    main()
