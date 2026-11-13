"""Frost-protection test (docs/FROST.md): v16 with a temperature record (arm v16T) and v16 + frost_min 278.15 K
(arm frost5) on the cold windows of the tuned check. Restartable (sb.memsched, at most 3 runs at a time).

    python -m sb.run_frost check                                                    # K1 (288 steps), exit 1 if different
    python -m sb.run_frost run >> D:/SmartBuildings_data/frost.log 2>&1             # shipped simulator, both arms
    PYTHONPATH=D:/SmartBuildings_data/kit_fixed python -m sb.run_frost run --fixed  # corrected copy, frost5 only
    python -m sb.run_frost read
    python -m sb.run_frost one <policy> <scenario dir> <out dir> <steps> <kwargs json>   (used by the scheduler)

Each logged run saves an .npy with 8 columns per step: reward, productivity regret, energy, carbon, occupancy (as
sb/run.py) and the lowest true zone temperature (K), the share of zones below 278.15 K and below 273.15 K (from the
reward's zone records).
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched
from sb.run_tuned import BIG, COLD, DATA, R, REPO, STEPS, V16, scen

POL = f"{REPO.as_posix()}/policies/zonal_v16frost.py:TransferPolicy"
OUT = R / "frost"
FROST = 278.15
ARMS = {"v16T": dict(V16), "frost5": dict(V16, frost_min=FROST)}


def cold_sets(fixed: bool) -> list[tuple[str, Path, list[str], Path]]:
    """(set, scenario root, cold scenarios, folder of the stored v16 runs)."""
    if fixed:
        return [("fixed", BIG, COLD, R / "fixsim/v16")]
    r6 = [s for s in scen(DATA / "round6h/scenarios") if s.split("__")[1].split("_")[0] in ("newyork", "chicago", "duluth")]
    return [("dev", BIG, COLD, R / "chatter/f_chm"),
            ("r6", DATA / "round6h/scenarios", r6, R / "round6h/v16"),
            ("r7", DATA / "round7/scenarios", scen(DATA / "round7/scenarios"), R / "round7/chm"),
            ("r8", DATA / "round8/scenarios", scen(DATA / "round8/scenarios"), R / "round8/v16")]


def jobs(fixed: bool) -> list[dict]:
    arms = ["frost5"] if fixed else ["v16T", "frost5"]
    out = []
    for name, root, ss, _ in cold_sets(fixed):
        for s in ss:
            b, w = s.split("__")
            for arm in arms:
                od = OUT / arm / name
                out.append(memsched.module_job(
                    "sb.run_frost", ["one", POL, str(root / b / w), str(od), str(STEPS), json.dumps(ARMS[arm])],
                    str(root / b / w), str(od / f"{s}.json"), f"frost_{arm}_{name}__{s}"))
    return out


def one(policy: str, scen_dir: str, out_dir: str, steps: int, kw: dict) -> None:
    from smart_buildings import evaluate

    from sb.run import _absolute_spec, load_policy_class

    scen_dir = Path(scen_dir).resolve()
    out = Path(out_dir).resolve() / f"{scen_dir.parent.name}__{scen_dir.name}.json"
    os.chdir(Path(evaluate.__file__).resolve().parents[1])
    env = evaluate.load_hybrid_environment(scen_dir / "config.gin")
    env.metrics_path = None
    env._occupancy_normalization_constant = 125.0
    meta = evaluate.create_building_meta_data(env, scen_dir)
    spec = env.action_spec()
    pol = load_policy_class(_absolute_spec(policy))(meta, spec, **kw)
    obs, _ = env.reset()
    t0, rows = time.time(), []
    for _ in range(steps):
        obs, reward, term, trunc, _ = env.step(evaluate.validate_action(pol.get_action(obs), spec))
        info, rr = env.get_reward_info_and_response()
        t = np.array([z.zone_air_temperature for z in info.zone_reward_infos.values()], dtype=float)
        rows.append((float(reward), rr.normalized_productivity_regret, rr.normalized_energy_cost,
                     rr.normalized_carbon_emission, rr.total_occupancy, t.min(), (t < 278.15).mean(), (t < 273.15).mean()))
        if term or trunc:
            break
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(out.with_suffix(".npy"), np.asarray(rows, dtype=np.float32))
    out.write_text(json.dumps({"policy": policy, "kwargs": kw, "steps": len(rows), "seconds": time.time() - t0,
                               "mean_reward": float(np.mean([r[0] for r in rows]))}, indent=1))
    print(f"{out.parent.parent.name}/{out.parent.name} {out.stem}: {-np.mean([r[0] for r in rows]):.5f}, "
          f"lowest zone {min(r[5] for r in rows) - 273.15:.2f} C ({time.time() - t0:.0f}s)", flush=True)


def check() -> None:
    """K1: frost_min 0 gives v16's actions (rewards) exactly, 288 steps of the first round-7 building."""
    r7 = DATA / "round7/scenarios"
    s = scen(r7)[0]
    j = memsched.job({"policy": POL, "base": "none", "kwargs": dict(V16, frost_min=0.0), "out": str(OUT / "check/k1"),
                      "scenario": s, "root": str(r7)}, 288)
    memsched.run(lambda: ([j] if not Path(j["result"]).exists() else [], []), max_jobs=1, reserve=0.5, say=print)
    x = np.load(OUT / "check/k1" / f"{s}.npy").astype(float)
    y = np.load(R / "round7/chm" / f"{s}.npy").astype(float)[:288]
    same = np.array_equal(x, y)
    print(f"{time.strftime('%d %b %H:%M:%S')} frost check k1: {'IDENTICAL' if same else 'DIFFERENT'} "
          f"(max diff {np.abs(x - y).max():.3g})", flush=True)
    sys.exit(0 if same else 1)


def read() -> None:
    loss = lambda x: -x[:STEPS, 0].mean()
    print("set   window                               v16 lowest C  <5C %   <0C %   frost5 lowest C  frost5/v16  K2")
    agg = {"ship": ([], []), "fixed": ([], [])}
    lows_v, lows_f, b5, b0 = [], [], [], []
    for fixed in (False, True):
        for name, _, ss, ref in cold_sets(fixed):
            for s in ss:
                fv, ff = OUT / "v16T" / name / f"{s}.npy", OUT / "frost5" / name / f"{s}.npy"
                g = np.load(ref / f"{s}.npy").astype(float)[:STEPS]
                cols = []
                if fv.exists():
                    v = np.load(fv).astype(float)
                    k2 = "same" if np.array_equal(v[:, :5], g[:, :5]) else "DIFF"
                    lows_v.append(v[:, 5].min()), b5.append(v[:, 6].mean()), b0.append(v[:, 7].mean())
                    cols += [f"{v[:, 5].min() - 273.15:7.2f}", f"{100 * v[:, 6].mean():6.2f}", f"{100 * v[:, 7].mean():6.3f}"]
                else:
                    k2, cols = "-", ["      -", "     -", "     -"]
                if ff.exists():
                    f = np.load(ff).astype(float)
                    lows_f.append(f[:, 5].min())
                    agg["fixed" if fixed else "ship"][0].append(loss(f)), agg["fixed" if fixed else "ship"][1].append(loss(g))
                    cols += [f"{f[:, 5].min() - 273.15:10.2f}", f"{loss(f) / loss(g):10.4f}"]
                else:
                    cols += ["         -", "         -"]
                print(f"{name:5s} {s:38s} {'  '.join(cols)}  {k2}")
    for k, (a, b) in agg.items():
        if a:
            r = np.array(a) / np.array(b)
            print(f"frost5/v16 {k}: n {len(a)}  mean loss ratio {np.mean(a) / np.mean(b):.4f}  worst {r.max():.4f}")
    if lows_v:
        print(f"v16 lowest zone over {len(lows_v)} windows {min(lows_v) - 273.15:.2f} C; zone-steps below 5 C "
              f"{100 * np.mean(b5):.2f} %, below 0 C {100 * np.mean(b0):.3f} %")
    if lows_f:
        print(f"frost5 lowest zone over {len(lows_f)} windows {min(lows_f) - 273.15:.2f} C (F2 mark 4.0 C)")


def main() -> None:
    cmd = sys.argv[1]
    if cmd == "one":
        one(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), json.loads(sys.argv[6]))
    elif cmd == "check":
        check()
    elif cmd == "read":
        read()
    elif cmd == "run":
        fixed = "--fixed" in sys.argv
        assert fixed == ("kit_fixed" in os.environ.get("PYTHONPATH", "")), "--fixed needs the patched copy and only it"
        say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
        plan = lambda: ([j for j in jobs(fixed) if not Path(j["result"]).exists()], [])
        say(f"frost{' fixed' if fixed else ''} starts: {len(plan()[0])} of {len(jobs(fixed))} runs to do")
        memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
        say(f"frost{' fixed' if fixed else ''} END")
        read()


if __name__ == "__main__":
    main()
