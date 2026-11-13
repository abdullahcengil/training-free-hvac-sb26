"""Per-zone trace over a window of steps: what each zone was asked and given.

Runs the policy from the start of the scenario and, for steps in
[--start, --end), records per zone the temperature, occupancy, the heat the
policy planned, the airflow and discharge temperature the box really
delivered, and the zone model (g, lambda, c).

    python -m sb.zone_dump --policy policies/zonal.py:TransferPolicy \
        --scenario .../building_train_1/atlanta_2 --start 4600 --end 4800 --out zones.npz
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


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kwargs", default="{}")
    a = ap.parse_args(argv)
    spec = _absolute_spec(a.policy)
    scen = Path(a.scenario).resolve()
    out = Path(a.out).resolve()

    from smart_buildings import evaluate

    os.chdir(Path(evaluate.__file__).resolve().parents[1])
    env = evaluate.load_hybrid_environment(scen / "config.gin")
    env.metrics_path = None
    env._occupancy_normalization_constant = 125.0
    meta = evaluate.create_building_meta_data(env, scen)
    spec_a = env.action_spec()
    pol = load_policy_class(spec)(meta, spec_a, **json.loads(a.kwargs))
    hv = env.building.simulator._hvac
    obs, _ = env.reset()
    rec = {k: [] for k in ("T", "occ", "q_plan", "flow", "dis", "theta", "sat", "oat", "lo", "hi")}
    for k in range(a.end):
        act = evaluate.validate_action(pol.get_action(obs), spec_a)
        obs, r, term, trunc, _ = env.step(act)
        if k < a.start:
            continue
        info, _ = env.get_reward_info_and_response()
        zr = list(info.zone_reward_infos.values())
        rec["occ"].append([z.average_occupancy for z in zr])
        rec["lo"].append([z.heating_setpoint_temperature for z in zr])
        rec["hi"].append([z.cooling_setpoint_temperature for z in zr])
        # Policy-side, in the policy's zone order.
        rec["T"].append(pol.prev_t.copy())
        rec["q_plan"].append(pol.prev_q.copy())
        rec["theta"].append(pol.theta.copy())
        rec["flow"].append(pol.prev_flow_cmd.copy())
        rec["dis"].append(pol.prev_dis.copy())
        rec["sat"].append([float(x) for x in pol.prev_s])
        rec["oat"].append(float(hv.air_handler.ahus[0].outside_air_temperature_sensor))
        if term or trunc:
            break
    np.savez(out, **{k: np.array(v) for k, v in rec.items()},
             zone_names=np.array(list(info.zone_reward_infos.keys())),
             policy_zones=np.array([meta["observation_field_names"][i] for i in pol.z_t]))
    print("saved", out)


if __name__ == "__main__":
    main()
