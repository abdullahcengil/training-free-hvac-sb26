"""Device-level energy trace of one policy run (training scenarios only): which device the energy goes to.

Runs the policy from the start of the scenario for --steps steps and records per step the electricity of the
supply and exhaust fans (blower), the air conditioning, the pumps and any heat pump, the boiler gas, the outside
temperature, the air handlers' setpoints and flows, the zone temperatures and flows, and the reward components.

    python analysis/energy_dump.py --policy D:/.../zonal_x.py:TransferPolicy --kwargs '{...}' \
        --scenario building_train_8__fairbanks_8 --steps 2016 --out D:/.../edump_f8.npz
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sb.run import _absolute_spec, load_policy_class  # noqa: E402

SC = Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--kwargs", default="{}")
    ap.add_argument("--base", default="v10", help="'v10' merges the kwargs over V10_PARAMS.json")
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--steps", type=int, default=2016)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    spec = _absolute_spec(a.policy)
    b, w = a.scenario.split("__")
    scen = (SC / b / w).resolve()
    out = Path(a.out).resolve()
    kw = {}
    if a.base == "v10":
        kw = json.loads((Path(__file__).resolve().parents[1] / "docs/preregistration4/V10_PARAMS.json").read_text())
    kw.update(json.loads(a.kwargs))

    from smart_buildings import evaluate

    os.chdir(Path(evaluate.__file__).resolve().parents[1])
    env = evaluate.load_hybrid_environment(scen / "config.gin")
    env.metrics_path = None
    env._occupancy_normalization_constant = 125.0
    meta = evaluate.create_building_meta_data(env, scen)
    spec_a = env.action_spec()
    pol = load_policy_class(spec)(meta, spec_a, **kw)
    hv = env.building.simulator._hvac
    ahus = hv.air_handler.ahus
    obs, _ = env.reset()
    rec = {k: [] for k in ("blower", "ac", "gas", "pump", "hp", "oat", "sat", "dp", "recirc", "flow_ahu",
                           "T", "zflow", "occ", "lo", "hi", "reward", "prod", "energy", "carbon")}
    for _ in range(a.steps):
        act = evaluate.validate_action(pol.get_action(obs), spec_a)
        obs, r, term, trunc, _ = env.step(act)
        info, rr = env.get_reward_info_and_response()
        ah = list(info.air_handler_reward_infos.values())
        bo = list(info.boiler_reward_infos.values())
        hp = list(info.heat_pump_reward_infos.values())
        zr = list(info.zone_reward_infos.values())
        rec["blower"].append(sum(x.blower_electrical_energy_rate for x in ah))
        rec["ac"].append(sum(x.air_conditioning_electrical_energy_rate for x in ah))
        rec["gas"].append(sum(x.natural_gas_heating_energy_rate for x in bo))
        rec["pump"].append(sum(x.pump_electrical_energy_rate for x in bo) + sum(x.pump_electrical_energy_rate for x in hp))
        rec["hp"].append(sum(x.electricity_heating_energy_rate for x in hp))
        rec["oat"].append(float(ahus[0].outside_air_temperature_sensor))
        rec["sat"].append([float(x.supply_air_temperature_setpoint) for x in ahus])
        rec["dp"].append([float(x.supply_air_static_pressure_setpoint) for x in ahus])
        rec["recirc"].append([float(x.recirculation) for x in ahus])
        rec["flow_ahu"].append([float(x.air_flow_rate) for x in ahus])
        rec["T"].append([z.zone_air_temperature for z in zr])
        rec["zflow"].append([z.air_flow_rate for z in zr])
        rec["occ"].append([z.average_occupancy for z in zr])
        rec["lo"].append([z.heating_setpoint_temperature for z in zr])
        rec["hi"].append([z.cooling_setpoint_temperature for z in zr])
        rec["reward"].append(float(r))
        rec["prod"].append(rr.normalized_productivity_regret)
        rec["energy"].append(rr.normalized_energy_cost)
        rec["carbon"].append(rr.normalized_carbon_emission)
        if term or trunc:
            break
    gin = (scen / "config.gin").read_text()
    start = gin.split("start_timestamp = '")[1].split("'")[0]
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **{k: np.array(v) for k, v in rec.items()}, start=np.array(start), n_ahu=np.array(len(ahus)),
             kwargs=np.array(json.dumps(kw)))
    print("saved", out, len(rec["reward"]), "steps")


if __name__ == "__main__":
    main()
