"""Reproduction check: the repository's frozen controller file with submission/V15_PARAMS.json must reproduce v15's
recorded per-step rewards (results/holiday/ed1_full, made from a copy of the same file) exactly.

    python -m sb.repro_check building_train_1__atlanta_2

Run 30 Oct 2026 (frozen/README.md): every reward term identical at every one of the 8640 steps.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from sb.run import run_job

REPO = Path(__file__).resolve().parents[1]
DATA = Path("D:/SmartBuildings_data")
TRAIN = DATA / "starter-kit/smart_buildings/training_scenarios"
REF = DATA / "results/holiday/ed1_full"
OUT = DATA / "results/repro_v15"


def main(s: str) -> None:
    b, w = s.split("__")
    frozen = REPO / "frozen/zonal_v14f.py"
    print("sha256", hashlib.sha256(frozen.read_bytes()).hexdigest())
    v14 = json.loads((REPO / "submission/V14_PARAMS.json").read_text())
    v15 = json.loads((REPO / "submission/V15_PARAMS.json").read_text())
    print("V15 == V14 + empty_day 1, empty_h 1.0:", v15 == dict(v14, empty_day=1, empty_h=1.0))
    run_job((f"{frozen.as_posix()}:TransferPolicy", str(TRAIN / b / w), str(OUT), 8640, True, v15))
    new, ref = (np.load(d / f"{s}.npy").astype(float) for d in (OUT, REF))
    same = new.shape == ref.shape and float(np.max(np.abs(new - ref))) == 0.0
    a, r = (json.loads((d / f"{s}.json").read_text())["mean_reward"] for d in (OUT, REF))
    print(f"mean reward {a!r} (recorded {r!r}); every term at every step identical: {same}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "building_train_1__atlanta_2")
