"""What carries the transfer? (docs/TRANSFER_ABLATION.md; plan written and timestamped before any run.) v16 with one
part removed or disturbed at a time, on the twelve full-size unseen buildings of rounds 6 and 7 (first 2880 steps),
against v16's existing runs there (`results/round6h/v16`, `results/round7/chm`). Post hoc on buildings that are no
longer blind; descriptive, and every arm is reported.

Arms (each V16_PARAMS plus one change):
  nolearn  rls 0: the five numbers of each zone's model stay at their priors and no disturbance is estimated
  offset   the five numbers stay at their priors, the disturbance estimate is learned (policies/zonal_v16_offsetonly.py)
  half     all five priors halved, learning on
  double   all five priors doubled, learning on
  nodelay  delay_comp 0: plans and safety nets ignore the heat already in the pipe
Known-answer check first: `offset` with dist_beta 0 must give the same rewards as `nolearn` over 288 steps.

    python -m sb.run_transfer_abl >> D:/SmartBuildings_data/transfer_abl.log 2>&1
    python -m sb.run_transfer_abl --read
    python -m sb.run_transfer_abl --days    (loss ratio to v16 day by day)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
V16 = json.loads((REPO / "submission/V16_PARAMS.json").read_text())
POLICY = "D:/SmartBuildings_data/frozen/zonal_v16f.py:TransferPolicy"
OFFSET = f"{REPO / 'policies/zonal_v16_offsetonly.py'}:OffsetOnlyPolicy"
PRIOR = (-0.33, 0.27, 0.09, 0.016, 0.25)   # m2_prior of frozen/zonal_v16f.py
ARMS = {
    "nolearn": (POLICY, dict(V16, rls=0)),
    "offset": (OFFSET, dict(V16)),
    "half": (POLICY, dict(V16, m2_prior=[0.5 * x for x in PRIOR])),
    "double": (POLICY, dict(V16, m2_prior=[2.0 * x for x in PRIOR])),
    "nodelay": (POLICY, dict(V16, delay_comp=0)),
}
DATA = Path("D:/SmartBuildings_data")
R = DATA / "results"
SETS = [("r6", DATA / "round6h/scenarios", R / "round6h/v16"), ("r7", DATA / "round7/scenarios", R / "round7/chm")]
OUT = R / "transfer_abl"
STEPS = 2880
CHECK = ("r7", "building_7802__helena_feb19", 288)


def scenarios(root: Path) -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in root.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    name, scen, steps = CHECK
    root = dict((n, r) for n, r, _ in SETS)[name]
    out = [memsched.job({"policy": OFFSET, "base": "none", "kwargs": dict(V16, dist_beta=0.0),
                         "out": str(OUT / "check_b0"), "scenario": scen, "root": str(root)}, steps)]
    for arm, (pol, kw) in ARMS.items():
        for name, root, _ in SETS:
            out += [memsched.job({"policy": pol, "base": "none", "kwargs": kw, "out": str(OUT / f"{name}_{arm}"),
                                  "scenario": s, "root": str(root)}, STEPS) for s in scenarios(root)]
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def terms(f: Path) -> tuple[float, float]:
    a = np.load(f).astype(float)[:STEPS]
    return -a[:, 0].mean(), -0.6 * a[:, 1].mean()


def read() -> None:
    name, scen, steps = CHECK
    fb, fa = OUT / "check_b0" / f"{scen}.npy", OUT / f"{name}_nolearn" / f"{scen}.npy"
    if fb.exists() and fa.exists():
        b, a = np.load(fb).astype(float)[:steps], np.load(fa).astype(float)[:steps]
        print(f"known-answer check (offset, dist_beta 0 = nolearn, {steps} steps): "
              f"{'PASS' if np.array_equal(a, b) else 'FAIL'} (max |diff| {np.abs(a - b).max():.3g})")
    for arm in ARMS:
        ref, new, cref, cnew, n_better = [], [], [], [], 0
        for name, root, rdir in SETS:
            for s in scenarios(root):
                f = OUT / f"{name}_{arm}" / f"{s}.npy"
                if not f.exists():
                    continue
                (l0, c0), (l1, c1) = terms(rdir / f"{s}.npy"), terms(f)
                ref.append(l0), new.append(l1), cref.append(c0), cnew.append(c1)
                n_better += l1 < l0
                print(f"{arm:8s} {name} {s:36s} v16 {l0:.5f} {arm} {l1:.5f} ({100 * (l1 / l0 - 1):+6.2f} %)  "
                      f"comfort {c0:.5f} -> {c1:.5f}")
        if ref:
            ref, new = np.array(ref), np.array(new)
            r = new / ref
            idx = np.random.default_rng(0).integers(0, len(ref), size=(10000, len(ref)))
            lo, hi = np.percentile(new[idx].mean(axis=1) / ref[idx].mean(axis=1), [2.5, 97.5])
            print(f"== {arm}: {len(ref)} of 12 scenarios, mean loss v16 {ref.mean():.6f} {arm} {new.mean():.6f}, "
                  f"ratio of means {new.mean() / ref.mean():.3f} (95 % CI {lo:.3f}-{hi:.3f}), per-scenario ratio "
                  f"median {np.median(r):.3f} range {r.min():.3f}-{r.max():.3f}, worse than v16 in "
                  f"{int((np.array(new) > np.array(ref)).sum())} (identical in {int((np.array(new) == np.array(ref)).sum())}); "
                  f"comfort {np.mean(cref):.5f} -> {np.mean(cnew):.5f}")


def days() -> None:
    """Loss ratio arm / v16 day by day (288 steps), summed over the scenarios that have finished: how fast learning
    makes up for wrong priors, and whether the gap of an arm grows or shrinks with time."""
    for arm in ARMS:
        num, den, n = np.zeros(10), np.zeros(10), 0
        for name, root, rdir in SETS:
            for s in scenarios(root):
                f = OUT / f"{name}_{arm}" / f"{s}.npy"
                if not f.exists():
                    continue
                a = -np.load(rdir / f"{s}.npy").astype(float)[:STEPS, 0].reshape(10, 288).sum(axis=1)
                b = -np.load(f).astype(float)[:STEPS, 0].reshape(10, 288).sum(axis=1)
                num, den, n = num + b, den + a, n + 1
        if n:
            print(f"{arm:8s} ({n:2d} scenarios) day 1-10: " + " ".join(f"{x:.3f}" for x in num / den))


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    if "--days" in sys.argv:
        days()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"transfer ablation starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("transfer ablation END")
    read()


if __name__ == "__main__":
    main()
