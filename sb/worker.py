r"""Second-computer worker: runs simulation jobs that the main computer drops into a shared folder.

The main computer writes one JSON file per job into <share>/queue/ (same fields as sb/jobs.py, with the
policy file given by name inside <share>/policies/). Each worker claims a job by renaming it (atomic on
one file system), runs it with sb.run.run_job against its own copy of the training scenarios, writes the
result into <share>/results/<tag>/ and removes the claim. Several workers may share one queue.

    python -m sb.worker --share \\MAINPC\sb_share --workers 3 --scenarios <starter-kit>/smart_buildings/training_scenarios
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import json
import multiprocessing as mp
import socket
import time
from pathlib import Path


def _run(args):
    share, claim, scenarios = args
    from sb.run import run_job

    j = json.loads(Path(claim).read_text())
    b, w = j["scenario"].split("__")
    policy = str(Path(share) / "policies" / j["policy_file"]) + ":TransferPolicy"
    out = Path(share) / "results" / j["tag"]
    r = run_job((policy, str(Path(scenarios) / b / w), str(out), int(j.get("steps", 8640)), True, j["kwargs"]))
    Path(claim).unlink(missing_ok=True)
    return f"{j['tag']} {j['scenario']}: {abs(r['mean_reward']):.5f} ({r['seconds']:.0f}s)"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--share", required=True)
    ap.add_argument("--scenarios", required=True)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args(argv)
    share = Path(a.share)
    q = share / "queue"
    host = socket.gethostname()
    print(f"worker on {host}: {a.workers} at a time, queue {q}", flush=True)
    with mp.get_context("spawn").Pool(a.workers) as pool:
        running = []
        while True:
            running = [r for r in running if not r.ready()]
            while len(running) < a.workers:
                jobs = sorted(q.glob("*.json"))
                if not jobs:
                    break
                claim = jobs[0].with_suffix(f".{host}.claimed")
                try:
                    jobs[0].rename(claim)
                except OSError:
                    continue
                running.append(pool.apply_async(_run, ((str(share), str(claim), a.scenarios),),
                                                callback=lambda s: print(s, flush=True),
                                                error_callback=lambda e: print("ERROR", e, flush=True)))
            if (share / "STOP_WORKERS").exists() and not running:
                print("stopped", flush=True)
                return
            time.sleep(10)


if __name__ == "__main__":
    main()
