"""Run a list of (policy, parameters, output folder, scenario) jobs in one pool, so that the machine stays
at a fixed number of simulations however many settings are being screened. Finished jobs are skipped
(sb.run.run_job returns the stored result).

    python -m sb.jobs jobs.json --workers 4

jobs.json: [{"policy": "D:/.../zonal_x.py:TransferPolicy", "kwargs": {...}, "out": "D:/.../results/tag",
             "scenario": "building_train_1__fairbanks_1"}, ...]   (kwargs are merged over V10_PARAMS.json
             when "base": "v10" is given)
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path

from sb.run import run_job

SC = Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios")
V10 = Path(__file__).resolve().parents[1] / "docs" / "preregistration4" / "V10_PARAMS.json"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--steps", type=int, default=8640)
    a = ap.parse_args(argv)
    spec = json.loads(Path(a.jobs).read_text())
    base = json.loads(V10.read_text())
    jobs = []
    for j in spec:
        kw = dict(base) if j.get("base", "v10") == "v10" else {}
        kw.update(j.get("kwargs", {}))
        b, w = j["scenario"].split("__")
        root = Path(j.get("root", SC))
        jobs.append((j["policy"], str(root / b / w), j["out"], a.steps, True, kw))
    print(f"{len(jobs)} jobs, {a.workers} workers", flush=True)
    t0 = time.time()
    with mp.get_context("spawn").Pool(a.workers) as pool:
        for r in pool.imap_unordered(run_job, jobs):
            print(f"{Path(r.get('policy', '')).name[:30]} {r['building']}/{r['weather']}: {abs(r['mean_reward']):.5f} "
                  f"({r['seconds']:.0f}s)", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
