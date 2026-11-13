"""Simulator-side airflow trace (docs/STRESS_TEST.md diagnosis): what each box really received.

A box's real airflow is damper x its maximum x sqrt(duct pressure / design pressure) x the share of the demand its air
handler can move (vav.py, flow_rate_demand). For every step in [--start, --end) this records, per box (sorted by id),
the damper, the box maximum, the real airflow and the air handler's share, and per air handler its airflow and
maximum. Run with v13 (frozen v11 file + submission/V13_PARAMS.json).

    python -m sb.stress_dump2 --scenario D:/SmartBuildings_data/stress/scenarios/building_train_7/duluth_jan15 \
        --start 2016 --end 2880 --out D:/SmartBuildings_data/results/stressdiag/b7_duluth_sim.npz
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
    pol = load_policy_class(_absolute_spec(a.policy))(meta, spec_a, **json.loads(V13.read_text()))
    hv = env.building.simulator._hvac
    vids = sorted(hv.vavs)
    ahus = list(hv.air_handler.ahus)
    ahu_of = [ahus.index(hv.vavs[v].air_handler) for v in vids]
    obs, _ = env.reset()
    rec = {k: [] for k in ("damper", "vmax", "flow", "ratio", "ahu_flow", "ahu_max", "ahu_p", "ahu_sat", "T", "lo",
                           "occ")}
    for k in range(a.end):
        act = evaluate.validate_action(pol.get_action(obs), spec_a)
        obs, r, term, trunc, _ = env.step(act)
        if k < a.start:
            continue
        vv = [hv.vavs[v] for v in vids]
        rec["damper"].append([v.damper_setting for v in vv])
        rec["vmax"].append([v.max_air_flow_rate for v in vv])
        rec["flow"].append([v.flow_rate_demand for v in vv])
        rec["ratio"].append([v.supply_air_flow_ratio for v in vv])
        rec["ahu_flow"].append([h.air_flow_rate for h in ahus])
        rec["ahu_max"].append([h.max_air_flow_rate for h in ahus])
        rec["ahu_p"].append([h.supply_air_static_pressure_sensor for h in ahus])
        rec["ahu_sat"].append([h.supply_air_temperature_sensor for h in ahus])
        info, _ = env.get_reward_info_and_response()
        zr = info.zone_reward_infos
        zn = [v.replace("VAV_", "room_") for v in vids]
        rec["T"].append([zr[z].zone_air_temperature if z in zr else np.nan for z in zn])
        rec["lo"].append([zr[z].heating_setpoint_temperature if z in zr else np.nan for z in zn])
        rec["occ"].append([zr[z].average_occupancy if z in zr else np.nan for z in zn])
        if term or trunc:
            break
    np.savez(out, **{k: np.array(v, dtype=float) for k, v in rec.items()}, vids=np.array(vids),
             ahu_of=np.array(ahu_of))
    print("saved", out)


if __name__ == "__main__":
    main()
