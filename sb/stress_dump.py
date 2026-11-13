"""Per-zone trace for the stress test's weak spot (docs/STRESS_TEST.md): why do zones miss the band?

Like sb/zone_dump.py, plus the mass model's state (theta2, the slab node tm, the disturbance estimate dhat) and the
box maximum airflow the policy reads. For every step in [--start, --end): per zone in the policy's order the
temperature, planned heat, airflow command, discharge temperature and maximum airflow; per zone in the reward's
order the occupancy and the band.

    python -m sb.stress_dump --scenario D:/SmartBuildings_data/stress/scenarios/building_train_7/duluth_jan15 \
        --start 2016 --end 3744 --out D:/SmartBuildings_data/results/stressdiag/b7_duluth.npz
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import json
import os
from pathlib import Path

import numpy as np

from sb.run import _absolute_spec, load_policy_class

V13 = Path(__file__).resolve().parents[1] / "submission" / "V13_PARAMS.json"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="D:/SmartBuildings_data/frozen/zonal_v11f.py:TransferPolicy")
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    spec = _absolute_spec(a.policy)
    scen = Path(a.scenario).resolve()
    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    from smart_buildings import evaluate

    os.chdir(Path(evaluate.__file__).resolve().parents[1])
    env = evaluate.load_hybrid_environment(scen / "config.gin")
    env.metrics_path = None
    env._occupancy_normalization_constant = 125.0
    meta = evaluate.create_building_meta_data(env, scen)
    spec_a = env.action_spec()
    pol = load_policy_class(spec)(meta, spec_a, **json.loads(V13.read_text()))
    obs, _ = env.reset()
    keys = ("T", "q_plan", "flow", "dis", "maxflow", "theta2", "tm", "dhat", "oat", "occ", "lo", "hi", "reward")
    rec = {k: [] for k in keys}
    for k in range(a.end):
        o = np.asarray(obs, dtype=np.float64)
        act = evaluate.validate_action(pol.get_action(obs), spec_a)
        obs, r, term, trunc, _ = env.step(act)
        if k >= a.start:
            info, _ = env.get_reward_info_and_response()
            zr = list(info.zone_reward_infos.values())
            rec["occ"].append([z.average_occupancy for z in zr])
            rec["lo"].append([z.heating_setpoint_temperature for z in zr])
            rec["hi"].append([z.cooling_setpoint_temperature for z in zr])
            rec["T"].append(pol.prev_t.copy())
            rec["q_plan"].append(pol.prev_q.copy())
            rec["flow"].append(pol.prev_flow_cmd.copy())
            rec["dis"].append(pol.prev_dis.copy())
            rec["maxflow"].append(np.where(pol.z_maxflow_idx >= 0, o[np.maximum(pol.z_maxflow_idx, 0)], np.nan))
            rec["theta2"].append(pol.theta2.copy())
            rec["tm"].append(pol.tm.copy())
            rec["dhat"].append(pol.dhat.copy())
            rec["oat"].append(float(o[pol.oat_idx]) if pol.oat_idx is not None else np.nan)
            rec["reward"].append(float(r))
        if term or trunc:
            break
    np.savez(out, **{k: np.array(v) for k, v in rec.items()},
             zone_names=np.array(list(info.zone_reward_infos.keys())),
             policy_zones=np.array([meta["observation_field_names"][i] for i in pol.z_t]))
    print("saved", out)


if __name__ == "__main__":
    main()
