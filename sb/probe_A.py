"""The public-board test of the size finding (docs/BIG_BUILDINGS.md, rule of 27 Oct, 12:23).

Checks the premise (rejected candidate A gives v14's per-step rewards on six shipped training buildings, first 2880
steps) and, if it holds, builds A's notebook and checks it with sb/nbcheck.py on a full-size scenario whose first two
days include the Sunday setback (where A acts). Writes D:/SmartBuildings_data/probeA_finish.txt; its last line starts
with "PROBE". The queue (sb/pipeline_v15.py) runs it as a job, since the notebook check is a simulation.

    python -m sb.probe_A
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
R = Path("D:/SmartBuildings_data/results")
OUT = R / "probeA_2880" / "A_sus"
V14_RUNS = R / "dev14_8640" / "of3"
SCEN = ["building_train_1__fairbanks_1", "building_train_2__phoenix_6", "building_train_4__fairbanks_4",
        "building_train_5__singapore_4", "building_train_7__denver_5", "building_train_8__phoenix_4"]
POLICY = "D:/SmartBuildings_data/frozen/zonal_v15dev_a.py"
NB = REPO / "submission" / "zonal_probeA_submission.ipynb"
PARAMS = REPO / "submission" / "PROBE_A_PARAMS.json"
CHECK = "D:/SmartBuildings_data/bigdev/scenarios/building_7001/chicago_jan15"
MARKER = Path("D:/SmartBuildings_data/probeA_finish.txt")


def premise() -> tuple[list[str], list[str]]:
    """(scenarios still missing, scenarios where A's per-step rewards differ from v14's)."""
    missing, differ = [], []
    for s in SCEN:
        f = OUT / f"{s}.npy"
        if not f.exists():
            missing.append(s)
            continue
        a = np.load(f)
        v = np.load(V14_RUNS / f"{s}.npy")[: len(a)]
        if not np.array_equal(a, v):
            differ.append(f"{s} (first step {int(np.argmax(np.any(a != v, axis=1)))}, loss "
                          f"{-a[:, 0].mean():.6f} vs {-v[:, 0].mean():.6f})")
    return missing, differ


def main() -> int:
    missing, differ = premise()
    if missing:
        print("runs missing:", missing, flush=True)
        return 2
    if differ:
        msg = "PROBE: premise fails, nothing submitted; A differs from v14 on " + "; ".join(differ)
    else:
        from sb.make_v15_full_jobs import CANDS

        kw = json.loads((REPO / "submission/V14_PARAMS.json").read_text())
        kw.update(CANDS["A_sus"])
        PARAMS.write_text(json.dumps(kw, indent=1))
        py = sys.executable
        r1 = subprocess.run([py, "-m", "sb.make_notebook", "--policy", POLICY, "--params", json.dumps(kw), "--out",
                             str(NB)], cwd=REPO, capture_output=True, text=True)
        r2 = subprocess.run([py, "-m", "sb.nbcheck", "--notebook", str(NB), "--policy", POLICY, "--params", str(PARAMS),
                             "--scenario", CHECK, "--steps", "576"], cwd=REPO, capture_output=True, text=True)
        print(r1.stdout[-2000:], r1.stderr[-1000:], r2.stdout[-3000:], r2.stderr[-1000:], flush=True)
        ok = r1.returncode == 0 and r2.returncode == 0
        msg = (f"PROBE: premise holds on {len(SCEN)} shipped buildings; READY TO SUBMIT {NB.name}" if ok else
               f"PROBE: notebook step failed (make_notebook {r1.returncode}, nbcheck {r2.returncode})")
    MARKER.write_text(msg + "\n")
    print(msg, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
