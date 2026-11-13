"""Run the v15 screen (docs/BIGDEV.md) with its fail rule applied as results come in.

A candidate fails the screen as soon as one scenario is more than 2 % worse than v14 on the same scenario; its
remaining scenarios are then skipped (the rule cannot be passed any more, so they would not change the decision).
Everything else is sb.jobs: one pool, finished jobs skipped.

    python -m sb.jobs_screen sb/jobs_v15_screen.json --workers 3 --steps 2880
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

REF = Path("D:/SmartBuildings_data/results/bigdev/v14")


def failed(out_dir: str) -> str | None:
    """The scenario that already fails this candidate's 2 % rule, if any."""
    for f in Path(out_dir).glob("*.json"):
        r = REF / f.name
        if not r.exists():
            continue
        c = abs(json.loads(f.read_text())["mean_reward"])
        v = abs(json.loads(r.read_text())["mean_reward"])
        if c > 1.02 * v:
            return f.stem
    return None


def run_or_skip(job: tuple) -> dict:
    policy, scen, out, steps, comps, kw = job
    bad = failed(out)
    if bad is not None and not (Path(out) / f"{Path(scen).parent.name}__{Path(scen).name}.json").exists():
        return {"skipped": True, "out": out, "scenario": scen, "because": bad}
    from sb.run import run_job

    return {"out": out, "res": run_job(job)}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--steps", type=int, default=2880)
    a = ap.parse_args(argv)
    spec = json.loads(Path(a.jobs).read_text())
    jobs = []
    for j in spec:
        b, w = j["scenario"].split("__")
        jobs.append((j["policy"], str(Path(j["root"]) / b / w), j["out"], a.steps, True, j.get("kwargs", {})))
    print(f"{len(jobs)} jobs, {a.workers} workers", flush=True)
    t0 = time.time()
    with mp.get_context("spawn").Pool(a.workers) as pool:
        for r in pool.imap(run_or_skip, jobs):
            if r.get("skipped"):
                print(f"skipped {Path(r['out']).name} {Path(r['scenario']).parent.name}/{Path(r['scenario']).name}"
                      f" (fails on {r['because']})", flush=True)
            else:
                res = r["res"]
                print(f"{Path(r['out']).name} {res['building']}/{res['weather']}: {abs(res['mean_reward']):.5f} "
                      f"({res['seconds']:.0f}s)", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
