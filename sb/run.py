"""Parallel rollout harness for the Smart Buildings Challenge.

Runs (policy, scenario) jobs in separate processes and writes one JSON per job.
The environment is stepped directly. The starter kit's SimulationTracker is not
used, because its occupancy logging queries the next interval and advances the
occupants' random chains, so its returns differ from the Kaggle gateway
(reported on the competition forum, 16 Oct 2026).

Usage:
    python -m sb.run --policy policies/pid_ref.py:PidWater \
        --scenarios D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios \
        --out D:/SmartBuildings_data/results/pid_water --steps 8640 --workers 16
"""

from __future__ import annotations

import os as _os

# One BLAS thread per process: otherwise every worker commits ~1 GB of thread
# buffers at import and the machine runs out of commit memory.
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import importlib.util
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np


def load_policy_class(spec: str):
    """Load 'path/to/file.py:ClassName' or 'baseline:<key>'."""
    if spec.startswith("baseline:"):
        from smart_buildings import evaluate

        return evaluate.POLICY_MAP[spec.split(":", 1)[1]]
    path, cls = spec.rsplit(":", 1)
    mod_name = "sbpolicy_" + Path(path).stem
    module_spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[mod_name] = module
    module_spec.loader.exec_module(module)
    return getattr(module, cls)


def _absolute_spec(spec: str) -> str:
    if spec.startswith("baseline:"):
        return spec
    path, cls = spec.rsplit(":", 1)
    return f"{Path(path).resolve()}:{cls}"


def find_scenarios(root: Path) -> list[Path]:
    return sorted(p.parent for p in root.glob("*/*/config.gin"))


def run_job(args: tuple) -> dict:
    policy_spec, scenario_dir, out_dir, steps, log_components, policy_kwargs = args
    scenario_dir = Path(scenario_dir).resolve()
    policy_spec = _absolute_spec(policy_spec)
    building, weather = scenario_dir.parent.name, scenario_dir.name
    out_file = Path(out_dir) / f"{building}__{weather}.json"
    if out_file.exists():
        return json.loads(out_file.read_text())

    from smart_buildings import evaluate

    # config.gin refers to weather files relative to the starter-kit root.
    os.chdir(Path(evaluate.__file__).resolve().parents[1])
    env = evaluate.load_hybrid_environment(scenario_dir / "config.gin")
    env.metrics_path = None
    env._occupancy_normalization_constant = 125.0
    meta = evaluate.create_building_meta_data(env, scenario_dir)
    action_spec = env.action_spec()
    policy_class = load_policy_class(policy_spec)
    try:
        policy = policy_class(meta, action_spec, **policy_kwargs)
    except TypeError:
        policy = evaluate.initialize_policy(policy_class, meta, action_spec)
    if policy_kwargs.get("occ_oracle") and hasattr(policy, "attach_oracle"):
        # Training-only diagnostic: the policy reads the true per-zone occupancy (never in a submission).
        policy.attach_oracle(env.building.occupancy)

    obs, _ = env.reset()
    t0 = time.time()
    total = 0.0
    comps = {"prod": 0.0, "energy": 0.0, "carbon": 0.0}
    per_step = []
    for _ in range(steps):
        action = evaluate.validate_action(policy.get_action(obs), action_spec)
        obs, reward, terminated, truncated, _ = env.step(action)
        total += float(reward)
        if log_components:
            _, rr = env.get_reward_info_and_response()
            comps["prod"] += rr.normalized_productivity_regret
            comps["energy"] += rr.normalized_energy_cost
            comps["carbon"] += rr.normalized_carbon_emission
            per_step.append(
                (
                    float(reward),
                    rr.normalized_productivity_regret,
                    rr.normalized_energy_cost,
                    rr.normalized_carbon_emission,
                    rr.total_occupancy,
                )
            )
        if terminated or truncated:
            break

    result = {
        "building": building,
        "weather": weather,
        "policy": policy_spec,
        "policy_kwargs": policy_kwargs,
        "steps": steps,
        "total_reward": total,
        "mean_reward": total / steps,
        "components": comps if log_components else None,
        "seconds": time.time() - t0,
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(result, indent=1))
    if log_components:
        np.save(out_file.with_suffix(".npy"), np.asarray(per_step, dtype=np.float32))
    return result


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--scenarios", required=True, help="root with <building>/<weather>/config.gin")
    ap.add_argument("--only", nargs="*", default=None, help="building__weather filters")
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=8640)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--components", action="store_true")
    ap.add_argument("--kwargs", default="{}", help="JSON dict passed to the policy")
    a = ap.parse_args(argv)

    scenarios = find_scenarios(Path(a.scenarios))
    if a.only:
        keep = set(a.only)
        scenarios = [s for s in scenarios if f"{s.parent.name}__{s.name}" in keep]
    kwargs = json.loads(a.kwargs)
    a.out = str(Path(a.out).resolve())
    jobs = [(_absolute_spec(a.policy), str(s), a.out, a.steps, a.components, kwargs) for s in scenarios]
    print(f"{len(jobs)} jobs, {a.workers} workers, {a.steps} steps", flush=True)
    t0 = time.time()
    with mp.get_context("spawn").Pool(a.workers) as pool:
        results = []
        for r in pool.imap_unordered(run_job, jobs):
            results.append(r)
            print(f"{r['building']}/{r['weather']}: {r['total_reward']:.2f} "
                  f"({r['seconds']:.0f}s)", flush=True)
    score = float(np.mean([abs(r["total_reward"]) / r["steps"] for r in results]))
    print(f"SCORE {score:.5f} over {len(results)} scenarios in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
