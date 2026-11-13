"""Step-by-step diagnostics for one scenario: what the plant does and costs.

    python -m sb.debug --policy policies/zonal.py:TransferPolicy \
        --scenario .../building_train_1/atlanta_2 --steps 576 --out debug.csv
"""

from __future__ import annotations

import os as _os

# One BLAS thread per process: otherwise every worker commits ~1 GB of thread
# buffers at import and the machine runs out of commit memory.
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from sb.run import _absolute_spec, load_policy_class


def _policy_stats(pol) -> dict:
    th = getattr(pol, "theta", None)
    if th is None:
        return {}
    return dict(g_med=float(np.median(th[:, 1])), g_min=float(np.min(th[:, 1])),
                lam_med=float(-np.median(th[:, 0])), c_med=float(np.median(th[:, 2])),
                c_min=float(np.min(th[:, 2])), c_max=float(np.max(th[:, 2])))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--steps", type=int, default=576)
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
    cls = load_policy_class(spec)
    try:
        pol = cls(meta, spec_a, **json.loads(a.kwargs))
    except TypeError:
        pol = evaluate.initialize_policy(cls, meta, spec_a)
    obs, _ = env.reset()
    rows = []
    for _ in range(a.steps):
        act = evaluate.validate_action(pol.get_action(obs), spec_a)
        obs, r, term, trunc, _ = env.step(act)
        info, rr = env.get_reward_info_and_response()
        zt = np.array([z.zone_air_temperature for z in info.zone_reward_infos.values()])
        hs = np.array([z.heating_setpoint_temperature for z in info.zone_reward_infos.values()])
        cs = np.array([z.cooling_setpoint_temperature for z in info.zone_reward_infos.values()])
        occ = np.array([z.average_occupancy for z in info.zone_reward_infos.values()])
        blower = sum(x.blower_electrical_energy_rate for x in info.air_handler_reward_infos.values())
        ac = sum(abs(x.air_conditioning_electrical_energy_rate) for x in info.air_handler_reward_infos.values())
        pump = sum(x.pump_electrical_energy_rate for x in info.boiler_reward_infos.values())
        gas = sum(x.natural_gas_heating_energy_rate for x in info.boiler_reward_infos.values())
        dev = np.maximum(0, np.maximum(zt - cs, hs - zt))
        ahus = env.building.simulator._hvac.air_handler.ahus
        on = [u for u in ahus if u.air_flow_rate > 0]
        exhaust = sum(u.compute_exhaust_fan_energy_rate() for u in ahus)
        plant = dict(
            exhaust_kw=exhaust / 1e3,
            flow=sum(u.air_flow_rate for u in ahus),
            sat=float(np.mean([u.supply_air_temperature_setpoint for u in on])) - 273.15 if on else np.nan,
            recirc=float(np.mean([u.recirculation for u in on])) if on else np.nan,
            sp=float(np.mean([u.supply_air_static_pressure_setpoint for u in on])) if on else np.nan,
        )
        rows.append(dict(
            ts=str(env.building.current_timestamp), reward=float(r),
            prod=rr.normalized_productivity_regret, energy=rr.normalized_energy_cost,
            carbon=rr.normalized_carbon_emission, occ=float(occ.sum()),
            tmin=zt.min() - 273.15, tmean=zt.mean() - 273.15, tmax=zt.max() - 273.15,
            dev_occ=float((dev * occ).sum() / max(occ.sum(), 1e-9)), n_out=int((dev > 0).sum()),
            blower_kw=blower / 1e3, ac_kw=ac / 1e3, pump_kw=pump / 1e3, gas_kw=gas / 1e3,
            ahu_on=int(act["discrete_action"][:-1].sum()), pump_on=int(act["discrete_action"][-1]),
            oat=float(env.building.simulator._hvac.air_handler.ahus[0].outside_air_temperature_sensor) - 273.15,
            tw=float(env.building.simulator._hvac.hot_water_system.supply_water_temperature_sensor) - 273.15,
            **plant, **_policy_stats(pol),
        ))
        if term or trunc:
            break
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    print(df.describe().T[["mean", "min", "max"]].round(3).to_string())


if __name__ == "__main__":
    main()
