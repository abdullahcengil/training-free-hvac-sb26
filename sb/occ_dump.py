"""Per-zone trace for occupancy detection: the true occupancy of every zone and the zone model's one-step error.

Runs a policy with the mass model (mass_model 1) from the start of a scenario and records, per step and per zone
in the policy's zone order, the people in the zone during the step (from the reward), the mass model's one-step
prediction error before its update (K per step), the heat the policy applied, the zone temperature, and the
building total the policy observes. Each person gives off 70 W in the zone they are in
(simulator_flexible_floor_plan.py), so a departure should show as a lasting negative shift in that zone's error.

    python -m sb.occ_dump --policy D:/.../zonal_v11f.py:TransferPolicy \
        --scenario .../training_scenarios/building_train_8/fairbanks_8 --steps 2016 --out occ.npz \
        --kwargs "$(cat submission/V12_PARAMS.json)"
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
    ap.add_argument("--steps", type=int, required=True)
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
    rooms = [meta["observation_field_names"][i].split("_zone_air")[0].replace("VAV_", "room_") for i in pol.z_t]

    errs = []
    orig = pol._identify_m2

    def wrapped(temps):
        if pol.tm is not None and pol.prev_t is not None:
            phi = np.stack([pol.prev_t - pol.tm, pol.prev_q2, np.ones(pol.nz), pol.prev_oat - pol.prev_t,
                            np.full(pol.nz, pol.prev_cm)], axis=1)
            errs.append(temps - pol.prev_t - np.einsum("ni,ni->n", phi, pol.theta2))
        else:
            errs.append(np.full(pol.nz, np.nan))
        return orig(temps)

    pol._identify_m2 = wrapped
    rec = {k: [] for k in ("occ", "q", "T", "n_obs", "hour")}
    obs, _ = env.reset()
    for k in range(a.steps):
        act = evaluate.validate_action(pol.get_action(obs), spec_a)
        rec["q"].append(pol.prev_q.copy())
        rec["T"].append(np.asarray(obs)[pol.z_t] * pol.t_std + pol.t_mean)
        rec["n_obs"].append(float(np.asarray(obs)[pol.occ_obs]) if pol.occ_obs is not None else np.nan)
        rec["hour"].append(pol._clock(np.asarray(obs, dtype=np.float64))[0])
        obs, r, term, trunc, _ = env.step(act)
        info, _ = env.get_reward_info_and_response()
        zr = info.zone_reward_infos
        rec["occ"].append([zr[r_].average_occupancy if r_ in zr else np.nan for r_ in rooms])
        if term or trunc:
            break
    n = len(rec["occ"])
    np.savez(out, err=np.array(errs[:n]), **{k: np.array(v) for k, v in rec.items()}, rooms=np.array(rooms),
             g=pol.theta2[:, 1].copy())
    print("saved", out, n, "steps,", len(rooms), "zones")


if __name__ == "__main__":
    main()
