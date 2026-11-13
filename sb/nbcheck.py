"""Check that a Kaggle notebook gives the same actions as the frozen policy file.

Runs the notebook's policy code (its gateway wrapper included, with the
gateway's Policy base class stubbed) and the frozen file side by side on one
environment; the frozen file's actions drive the environment, and every step's
continuous and discrete actions must be identical.

    python -m sb.nbcheck --notebook submission/zonal_v10_submission.ipynb \
        --policy D:/SmartBuildings_data/frozen/zonal_<commit>.py --params docs/preregistration4/V10_PARAMS.json \
        --scenario .../building_train_1/atlanta_2 --steps 576
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import json
import os
import sys
import types
from pathlib import Path

import numpy as np

from sb.run import load_policy_class


def notebook_policy_class(nb_path: Path):
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    policy_src, wrapper_src = "".join(code[0]["source"]), "".join(code[1]["source"])
    # Stub the gateway module; drop the lines that start the server.
    stub = types.ModuleType("kaggle_evaluation.smart_buildings_inference_server")

    class Policy:
        def __init__(self, building_meta_data, action_spec):
            self.building_meta_data, self.action_spec = building_meta_data, action_spec

    stub.Policy = Policy
    stub.SmartBuildingsInferenceServer = None
    pkg = types.ModuleType("kaggle_evaluation")
    pkg.smart_buildings_inference_server = stub
    sys.modules["kaggle_evaluation"] = pkg
    sys.modules["kaggle_evaluation.smart_buildings_inference_server"] = stub
    wrapper_src = wrapper_src.split("smart_buildings_inference_server.SmartBuildingsInferenceServer(")[0]
    ns: dict = {"__name__": "nb_policy"}
    exec(compile(policy_src + "\n" + wrapper_src, str(nb_path), "exec"), ns)
    return ns["SubmissionPolicy"], ns["PARAMS"]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--notebook", required=True)
    ap.add_argument("--policy", required=True, help="frozen policy file")
    ap.add_argument("--params", required=True, help="JSON file with the frozen parameters")
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--steps", type=int, default=576)
    a = ap.parse_args(argv)
    nb_cls, nb_params = notebook_policy_class(Path(a.notebook).resolve())
    params = json.loads(Path(a.params).read_text())
    assert nb_params == params, f"notebook parameters {nb_params} differ from {params}"
    ref_cls = load_policy_class(str(Path(a.policy).resolve()) + ":TransferPolicy")
    scen = Path(a.scenario).resolve()

    from smart_buildings import evaluate

    os.chdir(Path(evaluate.__file__).resolve().parents[1])
    env = evaluate.load_hybrid_environment(scen / "config.gin")
    env.metrics_path = None
    env._occupancy_normalization_constant = 125.0
    meta = evaluate.create_building_meta_data(env, scen)
    spec = env.action_spec()
    nb_pol = nb_cls(meta, spec)
    ref_pol = ref_cls(meta, spec, **params)
    obs, _ = env.reset()
    total = 0.0
    for k in range(a.steps):
        a_nb = nb_pol.get_action(obs)
        a_ref = ref_pol.get_action(obs)
        c_ref = np.clip(a_ref["continuous_action"], spec["continuous_action"].low, spec["continuous_action"].high)
        d_ref = np.clip(a_ref["discrete_action"], spec["discrete_action"].low, spec["discrete_action"].high)
        if not (np.array_equal(a_nb["continuous_action"], c_ref.astype(np.float32))
                and np.array_equal(a_nb["discrete_action"], d_ref.astype(np.int32))):
            raise SystemExit(f"actions differ at step {k}")
        obs, r, term, trunc, _ = env.step(evaluate.validate_action(a_ref, spec))
        total += float(r)
        if term or trunc:
            break
    print(f"identical actions for {k + 1} steps; total reward {total:.6f}")


if __name__ == "__main__":
    main()
