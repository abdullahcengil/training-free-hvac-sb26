"""Wall-clock cost of the controller per step, separate from the simulator's (for the paper's compute statement).

    python -m sb.timing --scenario <folder> --steps 576 [--policy frozen/zonal_v14f.py:TransferPolicy]
                        [--params submission/V15_PARAMS.json]
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import json
import os
import platform
import time
from pathlib import Path

import numpy as np

from sb.run import _absolute_spec, load_policy_class

REPO = Path(__file__).resolve().parents[1]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default=str(REPO / "frozen/zonal_v14f.py") + ":TransferPolicy")
    ap.add_argument("--params", default=str(REPO / "submission/V15_PARAMS.json"))
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--steps", type=int, default=576)
    a = ap.parse_args(argv)
    spec = _absolute_spec(a.policy)
    scen = Path(a.scenario).resolve()
    kw = json.loads(Path(a.params).read_text())

    from smart_buildings import evaluate

    os.chdir(Path(evaluate.__file__).resolve().parents[1])
    env = evaluate.load_hybrid_environment(scen / "config.gin")
    env.metrics_path = None
    env._occupancy_normalization_constant = 125.0
    meta = evaluate.create_building_meta_data(env, scen)
    spec_a = env.action_spec()
    cls = load_policy_class(spec)
    t0 = time.perf_counter()
    pol = cls(meta, spec_a, **kw)
    t_init = time.perf_counter() - t0
    obs, _ = env.reset()
    t_pol, t_sim = [], []
    for _ in range(a.steps):
        t0 = time.perf_counter()
        act = pol.get_action(obs)
        t1 = time.perf_counter()
        obs, r, term, trunc, _ = env.step(evaluate.validate_action(act, spec_a))
        t2 = time.perf_counter()
        t_pol.append(t1 - t0)
        t_sim.append(t2 - t1)
        if term or trunc:
            break
    p, s = 1e3 * np.array(t_pol), 1e3 * np.array(t_sim)
    print(f"{scen.parent.name}/{scen.name}: zones {getattr(pol, 'nz', '?')}, steps {len(p)}, "
          f"{platform.processor()} | init {1e3 * t_init:.0f} ms | controller per step: median {np.median(p):.1f} ms, "
          f"95th pct {np.percentile(p, 95):.1f} ms, max {p.max():.0f} ms, mean {p.mean():.1f} ms | simulator per step: "
          f"median {np.median(s):.0f} ms, mean {s.mean():.0f} ms | controller share {p.sum() / (p.sum() + s.sum()):.1%}",
          flush=True)


if __name__ == "__main__":
    main()
