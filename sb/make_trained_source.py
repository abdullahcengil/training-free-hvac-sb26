"""One self-contained source file (and from it the Kaggle notebook) for the trained residual controller
(docs/TRAINED_BASELINE.md): the verbatim pid_water copy, the policy, and the weights embedded as base64 of raw float64.

    python -m sb.make_trained_source --weights D:/SmartBuildings_data/results/rl/main/best.pkl
    python -m sb.make_trained_source --check   # same actions as the two-file policy with the pickled weights (one simulation)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import pickle
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "submission" / "lb"
SINGLE = OUT / "trained_policy_single.py"
NOTEBOOK = OUT / "trained_residual.ipynb"
WEIGHTS = "D:/SmartBuildings_data/results/rl/main/best.pkl"
SCENARIO = "D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios/building_train_1/atlanta_2"

TAIL = '''

_WEIGHTS_B64 = {payload!r}


def _decode(d):
    if isinstance(d, list):
        return [_decode(x) for x in d]
    return np.frombuffer(base64.b64decode(d["b"]), dtype="<f8").reshape(d["s"]).copy()


class TransferPolicy(TrainedResidualPolicy):
    """The trained weights, embedded; on Kaggle the policy is built from this class alone."""

    def __init__(self, building_meta_data, action_spec, **kw):
        w = {{k: _decode(v) for k, v in json.loads(_WEIGHTS_B64).items()}}
        super().__init__(building_meta_data, action_spec, weights=w, **kw)
'''


def encode(a: np.ndarray) -> dict:
    a = np.asarray(a, dtype=np.float64)
    return {"s": list(a.shape), "b": base64.b64encode(a.astype("<f8").tobytes()).decode("ascii")}


def build(weights: str) -> None:
    with open(weights, "rb") as f:
        w = pickle.load(f)
    payload = json.dumps({k: ([encode(x) for x in v] if isinstance(v, list) else encode(v)) for k, v in w.items()
                          if k in ("z_mu", "z_ls", "a_mu", "a_ls")})
    base = (REPO / "policies/pid_water_official.py").read_text(encoding="utf-8")
    pol = (REPO / "policies/trained_residual.py").read_text(encoding="utf-8")
    start = pol.index("def _load_base():")
    end = pol.index("def _mlp(")
    pol = pol[:start] + "def _load_base():\n    return PIDWaterResetPolicy\n\n\n" + pol[end:]
    # A future import is legal only at the top of a file; sb.make_notebook drops these lines too, so the single file is
    # what the notebook runs.
    pol = "\n".join(line for line in pol.splitlines() if line.strip() != "from __future__ import annotations") + "\n"
    src = "import base64\nimport json\n" + base + "\n\n" + pol + TAIL.format(payload=payload)
    SINGLE.parent.mkdir(parents=True, exist_ok=True)
    SINGLE.write_text(src, encoding="utf-8")
    print("wrote", SINGLE, f"({SINGLE.stat().st_size / 1024:.0f} KB)")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "sb.make_notebook", "--policy", str(SINGLE), "--params", "{}", "--out",
                           str(NOTEBOOK), "--title",
                           "Trained residual controller (PPO corrections to pid_water), for the paper's comparison"],
                          cwd=REPO)


def check(weights: str, n: int = 288) -> None:
    for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
        os.environ.setdefault(v, "1")
    sys.path.insert(0, str(REPO))
    from smart_buildings import evaluate

    from sb.run import load_policy_class

    scen = Path(SCENARIO).resolve()

    def run(make):
        os.chdir(Path(evaluate.__file__).resolve().parents[1])
        env = evaluate.load_hybrid_environment(scen / "config.gin")
        env.metrics_path = None
        env._occupancy_normalization_constant = 125.0
        meta = evaluate.create_building_meta_data(env, scen)
        spec = env.action_spec()
        pol = make(meta, spec)
        o, _ = env.reset()
        tot, acts = 0.0, []
        for _ in range(n):
            a = evaluate.validate_action(pol.get_action(o), spec)
            acts.append(a["continuous_action"].copy())
            o, r, _, _, _ = env.step(a)
            tot += float(r)
        return tot, np.array(acts)

    two = load_policy_class(f"{REPO / 'policies/trained_residual.py'}:TrainedResidualPolicy")
    one = load_policy_class(f"{SINGLE}:TransferPolicy")
    t1, a1 = run(lambda m, s: two(m, s, weights_file=weights))
    t2, a2 = run(lambda m, s: one(m, s))
    print(f"two-file policy {t1:.6f}, single file {t2:.6f}, largest action difference {float(np.abs(a1 - a2).max()):.2e}")
    assert float(np.abs(a1 - a2).max()) == 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default=WEIGHTS)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        check(a.weights)
    else:
        build(a.weights)


if __name__ == "__main__":
    main()
