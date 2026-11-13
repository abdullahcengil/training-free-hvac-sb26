"""The test of the trained neural residual controller (docs/TRAINED_BASELINE.md): the checkpoint chosen on the validation
building, once, on the twelve full-size scenarios of rounds 6 and 7, first 2880 steps, shipped simulator. Restartable
(sb.memsched), three simulations at most.

    python -m sb.run_trained >> D:/SmartBuildings_data/rl_test.log 2>&1
    python -m sb.run_trained --read
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

REPO = Path(__file__).resolve().parents[1]
POLICY = f"{REPO / 'policies/trained_residual.py'}:TrainedResidualPolicy"
DATA = Path("D:/SmartBuildings_data")
R = DATA / "results"
WEIGHTS = R / "rl/main/best.pkl"
SETS = [("r6", DATA / "round6h/scenarios", R / "round6h/v16", R / "round6h/pid_water"),
        ("r7", DATA / "round7/scenarios", R / "round7/chm", R / "round7/pid_water")]
OUT = R / "rl_test"
STEPS = 2880


def scenarios(root: Path) -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in root.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    out = []
    for name, root, _, _ in SETS:
        out += [memsched.job({"policy": POLICY, "base": "none", "kwargs": {"weights_file": str(WEIGHTS)},
                              "out": str(OUT / name), "scenario": s, "root": str(root)}, STEPS) for s in scenarios(root)]
    return out


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def terms(f: Path) -> tuple[float, float]:
    a = np.load(f).astype(float)[:STEPS]
    return -a[:, 0].mean(), -0.6 * a[:, 1].mean()


def read() -> None:
    v, p, t, cv, cp, ct, names = [], [], [], [], [], [], []
    for name, root, rv, rp in SETS:
        for s in scenarios(root):
            f = OUT / name / f"{s}.npy"
            if not f.exists():
                continue
            (a, ca), (b, cb), (c, cc) = terms(rv / f"{s}.npy"), terms(rp / f"{s}.npy"), terms(f)
            v.append(a), p.append(b), t.append(c), cv.append(ca), cp.append(cb), ct.append(cc), names.append(s)
            print(f"{name} {s:36s} v16 {a:.5f}  pid_water {b:.5f}  trained {c:.5f}  trained/pid {c / b:.3f}  trained/v16 {c / a:.2f}  "
                  f"comfort {ca:.5f} {cb:.5f} {cc:.5f}")
    if not t:
        print("no results yet")
        return
    v, p, t = np.array(v), np.array(p), np.array(t)
    idx = np.random.default_rng(0).integers(0, len(t), size=(10000, len(t)))
    rng = lambda x, y: np.percentile(x[idx].mean(axis=1) / y[idx].mean(axis=1), [2.5, 97.5])
    lo1, hi1 = rng(t, p)
    lo2, hi2 = rng(t, v)
    print(f"== {len(t)} of 12 scenarios. Mean loss: v16 {v.mean():.6f}, pid_water {p.mean():.6f}, trained {t.mean():.6f}.")
    print(f"trained / pid_water: ratio of means {t.mean() / p.mean():.3f} (95 % CI {lo1:.3f}-{hi1:.3f}), below pid_water in "
          f"{int((t < p).sum())} of {len(t)}.")
    print(f"trained / v16: ratio of means {t.mean() / v.mean():.3f} (95 % CI {lo2:.3f}-{hi2:.3f}), v16 below trained in "
          f"{int((v < t).sum())} of {len(t)}.")
    print(f"comfort term: v16 {np.mean(cv):.5f}, pid_water {np.mean(cp):.5f}, trained {np.mean(ct):.5f}")
    if len(t) == 12:
        write_outputs(names, v, p, t, np.array(cv), np.array(cp), np.array(ct), rng)


def budget() -> dict:
    """Training budget from the run's own logs (training and validation data only)."""
    import csv
    run = R / "rl/main"
    rows = list(csv.DictReader(open(run / "train.csv", newline="")))
    val = list(csv.DictReader(open(run / "val.csv", newline="")))
    best = json.loads((run / "best.json").read_text())
    return {"iterations": int(rows[-1]["it"]), "train_steps": int(rows[-1]["env_steps"]),
            "hours": float(rows[-1]["hours"]), "validations": len({r["it"] for r in val}),
            "best_it": int(best["it"]), "best_val": float(best["val_loss"])}


def write_outputs(names, v, p, t, cv, cp, ct, rng) -> None:
    """results/rl_test/summary.json and paper/tab_trained.tex, straight from the result files."""
    lo1, hi1 = rng(t, p)
    lo2, hi2 = rng(t, v)
    lo3, hi3 = rng(v, p)
    s = {"scenarios": names, "v16": v.tolist(), "pid_water": p.tolist(), "trained": t.tolist(),
         "mean": {"v16": v.mean(), "pid_water": p.mean(), "trained": t.mean()},
         "comfort": {"v16": cv.mean(), "pid_water": cp.mean(), "trained": ct.mean()},
         "trained_over_pid": [t.mean() / p.mean(), lo1, hi1], "trained_below_pid": int((t < p).sum()),
         "trained_over_v16": [t.mean() / v.mean(), lo2, hi2], "v16_below_trained": int((v < t).sum()),
         "v16_over_pid": [v.mean() / p.mean(), lo3, hi3], "v16_below_pid": int((v < p).sum()),
         "budget": budget()}
    s = json.loads(json.dumps(s, default=float))
    (OUT / "summary.json").write_text(json.dumps(s, indent=1))
    b = s["budget"]
    f = lambda x: f"{x:.5f}"
    tex = (
        "% Written by sb/run_trained.py --read from results/rl_test (do not edit by hand).\n"
        "\\begin{tabular}{llcccc}\\toprule\n"
        "Policy & Training & Loss & Comfort & Loss / pid\\_water & Below pid\\_water\\\\\\midrule\n"
        f"pid\\_water & none (official baseline) & {f(p.mean())} & {f(cp.mean())} & 1 & --\\\\\n"
        f"trained residual & {b['hours']:.0f}\\,h, {b['train_steps'] / 1e6:.1f}\\,M steps & {f(t.mean())} & {f(ct.mean())} & "
        f"{t.mean() / p.mean():.2f} ({lo1:.2f}--{hi1:.2f}) & {int((t < p).sum())} of 12\\\\\n"
        f"v16 & none (learns online) & {f(v.mean())} & {f(cv.mean())} & {v.mean() / p.mean():.2f} ({lo3:.2f}--{hi3:.2f}) & "
        f"{int((v < p).sum())} of 12\\\\\\bottomrule\n"
        "\\end{tabular}\n"
    )
    (REPO / "paper/tab_trained.tex").write_text(tex, encoding="utf-8")
    print("wrote", OUT / "summary.json", "and paper/tab_trained.tex")


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    if not WEIGHTS.exists():
        raise SystemExit(f"{WEIGHTS} is missing")
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"trained controller test starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("trained controller test END")
    read()


if __name__ == "__main__":
    main()
