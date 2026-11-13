"""Probe how the num_occupants observation is scaled (training scenario, v10 policy, first 420 steps)."""
import json
import os
from pathlib import Path

import numpy as np

from sb.run import load_policy_class
from smart_buildings import evaluate

scen = Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios/building_train_8/singapore_7")
os.chdir(Path(evaluate.__file__).resolve().parents[1])
env = evaluate.load_hybrid_environment(scen / "config.gin")
env.metrics_path = None
env._occupancy_normalization_constant = 125.0
meta = evaluate.create_building_meta_data(env, scen)
names = list(meta["observation_field_names"])
i = names.index("num_occupants")
print("normalization metadata:", (meta.get("observation_normalization_metadata") or {}).get("num_occupants"))
pol = load_policy_class("D:/SmartBuildings_data/frozen/zonal_24f07c3344ece0087d183cd3bc3a25ba080dece7.py:TransferPolicy")(
    meta, env.action_spec(), **json.loads(Path("./docs/preregistration4/V10_PARAMS.json").read_text()))
obs, _ = env.reset()
vals = []
for k in range(420):
    obs, r, *_ = env.step(evaluate.validate_action(pol.get_action(obs), env.action_spec()))
    vals.append((k, float(obs[i]), env.building.num_occupants))
for k, v, n in vals[::12] + vals[-30::3]:
    print(k, round(v, 6), n)
