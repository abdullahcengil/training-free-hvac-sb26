"""Write a jobs file that runs one policy setting on all 30 training scenarios at full length, longest first.

    python -m sb.make_all30_jobs --policy D:/.../zonal_v11f.py --params docs/preregistration5/V11_PARAMS.json \
        --extra '{"boost_k": 0.5}' --out-dir D:/SmartBuildings_data/results/dev12_8640/v12_all30 --jobs sb/jobs_x.json

Job order follows v11's own run times (dev11_8640/v11f), so the pool finishes with short jobs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

V11_RUNS = Path("D:/SmartBuildings_data/results/dev11_8640/v11f")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--params", required=True)
    ap.add_argument("--extra", default="{}")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--jobs", required=True)
    a = ap.parse_args(argv)
    kw = json.loads(Path(a.params).read_text())
    kw.update(json.loads(a.extra))
    runs = sorted(V11_RUNS.glob("*.json"), key=lambda f: -json.loads(f.read_text())["seconds"])
    jobs = [{"policy": f"{a.policy}:TransferPolicy", "base": "none", "kwargs": kw, "out": a.out_dir,
             "scenario": f.stem} for f in runs]
    Path(a.jobs).write_text(json.dumps(jobs, indent=1))
    print(len(jobs), "jobs ->", a.jobs)


if __name__ == "__main__":
    main()
