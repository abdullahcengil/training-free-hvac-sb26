"""Open-loop system identification of zone thermal response.

Applies random (but bounded) damper / reheat / supply-air settings and logs,
per zone and step, the zone temperature and the heat the VAV actually put in
(from the simulator internals). The fit tells us how fast a zone responds to
the heat it is given and how much of that response carries over to later
steps, which sets how cautious a one-step controller must be.

    python -m sb.probe --scenario .../building_train_1/atlanta_2 --steps 600 --out probe.npz
"""

from __future__ import annotations

import os as _os

# One BLAS thread per process: otherwise every worker commits ~1 GB of thread
# buffers at import and the machine runs out of commit memory.
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import os
from pathlib import Path

import numpy as np


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--hold", type=int, default=3, help="steps each random setting is held")
    a = ap.parse_args(argv)
    scen = Path(a.scenario).resolve()
    out = Path(a.out).resolve()
    from smart_buildings import evaluate

    os.chdir(Path(evaluate.__file__).resolve().parents[1])
    env = evaluate.load_hybrid_environment(scen / "config.gin")
    env.metrics_path = None
    meta = evaluate.create_building_meta_data(env, scen)
    spec = env.action_spec()
    rng = np.random.default_rng(a.seed)
    obs, _ = env.reset()
    hv = env.building.simulator._hvac
    vav_ids = sorted(hv.vavs.keys(), key=lambda s: int(s.split("_")[1]))
    zai = meta["zone_action_indices"]
    n_ahu = len(meta["temp_indices"])
    T, Q, OAT, OCC = [], [], [], []
    cont = np.zeros(meta["n_continuous_action"], dtype=np.float32)
    disc = np.ones(meta["n_discrete_action"], dtype=np.int32)
    for k in range(a.steps):
        if k % a.hold == 0:
            for i in meta["temp_indices"]:
                cont[i] = rng.choice([-1.0, -0.5, 0.0, 1.0])
            for i in meta["pressure_indices"][:n_ahu]:
                cont[i] = 1.0
            for i in meta["recirculation_indices"]:
                cont[i] = 1.0
            cont[meta["water_indices"][0]] = 0.0  # 330 K
            cont[meta["pressure_indices"][n_ahu]] = 1.0
            for v in vav_ids:
                cont[zai[v]["supply_air_damper_percentage_command"]] = rng.choice([-0.8, -0.2, 0.4, 1.0])
                cont[zai[v]["reheat_valve_percentage_command"]] = rng.choice([-1.0, -1.0, 1.0])
        obs, r, *_ = env.step({"continuous_action": cont.copy(), "discrete_action": disc.copy()})
        info, _ = env.get_reward_info_and_response()
        T.append([hv.vavs[v].zone_air_temperature for v in vav_ids])
        # Heat delivered during the step, from the box's own accounting.
        ahs = hv.air_handler
        avg = env.building.simulator.building.get_zone_average_temps()
        rec = sum(avg.values()) / len(avg)
        oat = ahs.ahus[0].outside_air_temperature_sensor
        tw = hv.hot_water_system.supply_water_temperature_sensor
        q = []
        for v in vav_ids:
            box = hv.vavs[v]
            sup = box.air_handler.get_supply_air_temp(rec, oat)
            dis = box.compute_zone_supply_temp(sup, tw)
            q.append((box.flow_rate_demand, dis))
        Q.append(q)
        OAT.append(oat)
        OCC.append([z.average_occupancy for z in info.zone_reward_infos.values()])
    np.savez(out, T=np.array(T), Q=np.array(Q), OAT=np.array(OAT), OCC=np.array(OCC), vav_ids=np.array(vav_ids))
    print("saved", out)


if __name__ == "__main__":
    main()
