"""Plant-side trace for the big-building question (docs/BIG_BUILDINGS.md): where does v14's hot-weather energy go?

For every step in [--start, --end): the reward's components; per air handler its airflow, maximum, static pressure
setpoint, supply-air setpoint and temperature, recirculation, run state, fan and cooling power (as the simulator bills
them); per box (sorted by id) the damper, maximum airflow, real airflow, the air handler's share, reheat valve, zone
temperature, band and occupancy; the boiler's gas and pump power; the outside temperature; and the policy's clock.
Default policy: v14 (frozen/zonal_v14f.py + submission/V14_PARAMS.json); --policy baseline:pid_water for the baseline.

    python -m sb.bigbld_dump --scenario D:/SmartBuildings_data/bigbld/scenarios/building_7402/dubai_jul15 \
        --start 0 --end 2016 --out D:/SmartBuildings_data/results/bigbld_diag/v14_7402_dubai_full.npz
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

V14 = Path(__file__).resolve().parents[1] / "submission" / "V14_PARAMS.json"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy")
    ap.add_argument("--kwargs", default=None, help="JSON dict merged over V14_PARAMS (zonal policies only)")
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--start", type=int, default=0)
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
    cls = load_policy_class(_absolute_spec(a.policy))
    if a.policy.startswith("baseline:"):
        pol = evaluate.initialize_policy(cls, meta, spec_a)
    else:
        kw = json.loads(V14.read_text())
        kw.update(json.loads(a.kwargs or "{}"))
        pol = cls(meta, spec_a, **kw)
    sim = env.building.simulator
    hv = sim._hvac
    vids = sorted(hv.vavs)
    ahus = list(hv.air_handler.ahus)
    ahu_of = [ahus.index(hv.vavs[v].air_handler) for v in vids]
    zn = [v.replace("VAV_", "room_") for v in vids]
    obs, _ = env.reset()
    keys = ("reward", "prod", "energy", "carbon", "occ_total", "elec_blower", "elec_ac", "gas", "pump", "oat", "hour",
            "day", "a_flow", "a_max", "a_p", "a_sat_sp", "a_sat", "a_recirc", "a_on", "a_fan_w", "damper", "vmax",
            "flow", "ratio", "valve", "T", "lo", "hi", "occ", "tank")
    rec = {k: [] for k in keys}
    # The zonal policy's own state, per zone in the policy's order (mapped to box order below).
    internal = hasattr(pol, "theta2")
    if internal:
        names = meta["observation_field_names"]
        pz = [names[i].replace("_zone_air_temperature_sensor", "") for i in pol.z_t]
        missing = [v for v in vids if v not in pz]
        if missing:
            raise SystemExit(f"boxes without a policy zone: {missing}")
        to_box = [pz.index(v) for v in vids]
        for k in ("p_theta2", "p_dhat", "p_tm", "p_q", "p_flow"):
            rec[k] = []
    for k in range(a.end):
        o = np.asarray(obs, dtype=np.float64)
        act = evaluate.validate_action(pol.get_action(obs), spec_a)
        obs, r, term, trunc, _ = env.step(act)
        if k >= a.start:
            info, resp = env.get_reward_info_and_response()
            rec["reward"].append(float(r))
            rec["prod"].append(resp.normalized_productivity_regret)
            rec["energy"].append(resp.normalized_energy_cost)
            rec["carbon"].append(resp.normalized_carbon_emission)
            rec["occ_total"].append(resp.total_occupancy)
            ah = list(info.air_handler_reward_infos.values())
            rec["elec_blower"].append(sum(x.blower_electrical_energy_rate for x in ah))
            rec["elec_ac"].append(sum(x.air_conditioning_electrical_energy_rate for x in ah))
            bo = list(info.boiler_reward_infos.values())
            rec["gas"].append(sum(x.natural_gas_heating_energy_rate for x in bo))
            rec["pump"].append(sum(x.pump_electrical_energy_rate for x in bo))
            hs, hc = meta["observation_field_names"].index("hod_sin_000"), meta["observation_field_names"].index("hod_cos_000")
            ds, dc = meta["observation_field_names"].index("dow_sin_000"), meta["observation_field_names"].index("dow_cos_000")
            rec["hour"].append((np.arctan2(o[hs], o[hc]) % (2 * np.pi)) * 24 / (2 * np.pi))
            rec["day"].append(int(round((np.arctan2(o[ds], o[dc]) % (2 * np.pi)) * 7 / (2 * np.pi))) % 7)
            rec["oat"].append(float(sim._weather_controller.get_current_temp(sim._current_timestamp)))
            rec["a_flow"].append([h.air_flow_rate for h in ahus])
            rec["a_max"].append([h.max_air_flow_rate for h in ahus])
            rec["a_p"].append([h.supply_air_static_pressure_setpoint for h in ahus])
            rec["a_sat_sp"].append([h.supply_air_temperature_setpoint for h in ahus])
            rec["a_sat"].append([h.supply_air_temperature_sensor for h in ahus])
            rec["a_recirc"].append([h.recirculation for h in ahus])
            rec["a_on"].append([float(h.run_command.value) if hasattr(h.run_command, "value") else float(h.run_command)
                                for h in ahus])
            rec["a_fan_w"].append([h.compute_intake_fan_energy_rate() + h.compute_exhaust_fan_energy_rate()
                                   for h in ahus])
            vv = [hv.vavs[v] for v in vids]
            rec["damper"].append([v.damper_setting for v in vv])
            rec["vmax"].append([v.max_air_flow_rate for v in vv])
            rec["flow"].append([v.flow_rate_demand for v in vv])
            rec["ratio"].append([v.supply_air_flow_ratio for v in vv])
            rec["valve"].append([v.reheat_valve_setting for v in vv])
            zr = info.zone_reward_infos
            rec["T"].append([zr[z].zone_air_temperature if z in zr else np.nan for z in zn])
            rec["lo"].append([zr[z].heating_setpoint_temperature if z in zr else np.nan for z in zn])
            rec["hi"].append([zr[z].cooling_setpoint_temperature if z in zr else np.nan for z in zn])
            rec["occ"].append([zr[z].average_occupancy if z in zr else np.nan for z in zn])
            # The private attribute: the sensor property moves the tank temperature each time it is read.
            rec["tank"].append(float(hv.hot_water_system._heat_source._current_temperature))
            if internal:
                sel = np.asarray(to_box)
                rec["p_theta2"].append(pol.theta2[sel].copy())
                rec["p_dhat"].append(pol.dhat[sel].copy())
                rec["p_tm"].append(pol.tm[sel].copy())
                rec["p_q"].append(pol.prev_q[sel].copy())
                rec["p_flow"].append(pol.prev_flow_cmd[sel].copy())
        if term or trunc:
            break
    room_area = {z: len(c) for z, c in sim.building.room_dict.items()}
    np.savez(out, **{k: np.array(v, dtype=float) for k, v in rec.items()}, vids=np.array(vids),
             ahu_of=np.array(ahu_of), area=np.array([room_area.get(z, np.nan) for z in zn], dtype=float),
             cv_m=float(sim.building.cv_size_cm) / 100.0)
    print("saved", out, flush=True)


if __name__ == "__main__":
    main()
