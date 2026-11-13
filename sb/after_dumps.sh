#!/usr/bin/env bash
# Screens and the rest of the v11 candidate (2 workers) once the two energy dumps have exited.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
while tasklist //FI "PID eq 17584" | grep -q python || tasklist //FI "PID eq 21260" | grep -q python; do sleep 15; done
$PY - <<'PY'
# smoke test of dp_reset on a few steps (fails loudly before the pool starts)
import json, os, numpy as np
from pathlib import Path
from smart_buildings import evaluate
from sb.run import load_policy_class
root = Path.cwd()
scen = Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios/building_train_1/fairbanks_1")
os.chdir(Path(evaluate.__file__).resolve().parents[1])
env = evaluate.load_hybrid_environment(scen / "config.gin"); env.metrics_path = None
meta = evaluate.create_building_meta_data(env, scen); spec = env.action_spec()
kw = json.loads((root / "docs/preregistration4/V10_PARAMS.json").read_text())
kw.update({"mass_model": 1, "glide_floor": -12.0, "margin_cool": 0.25, "f_heat_safety": 0.45, "dp_reset": 1})
pol = load_policy_class(str(root / "policies/zonal.py") + ":TransferPolicy")(meta, spec, **kw)
obs, _ = env.reset(); dps = []
for k in range(72):
    act = evaluate.validate_action(pol.get_action(obs), spec)
    dps.append(float(act["continuous_action"][pol.dp_idx]))
    obs, r, *_ = env.step(act)
print("SMOKE dp_reset ok; dp commands (normalised):", np.round(dps[::8], 3).tolist())
PY
$PY -m sb.jobs sb/jobs_v11c_3.json --workers 2 2>&1 | grep --line-buffered -v -i warn
