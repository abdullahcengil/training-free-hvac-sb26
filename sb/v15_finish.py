"""Last step of the v15 queue (docs/BIGDEV.md): read the full check and, if all three items pass, build and check the
notebook (sb/make_v15_submission.sh). Writes D:/SmartBuildings_data/v15_finish_<cand>.txt with the outcome; its last
line starts with "PIPELINE END". The queue runs it as a job, since the notebook check is a simulation.

    python -m sb.v15_finish --cand B_glo
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from sb import v15_full_eval

REPO = Path(__file__).resolve().parents[1]
BASH = "C:/Program Files/Git/bin/bash.exe"


def marker(cand: str) -> Path:
    return Path(f"D:/SmartBuildings_data/v15_finish_{cand}.txt")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    a = ap.parse_args(argv)
    code = v15_full_eval.main(["--cand", a.cand])
    if code == 2:
        print("runs missing; nothing decided", flush=True)
        return 2
    if code != 0:
        msg = f"PIPELINE END: {a.cand} does not pass the full check; v14 stays"
    else:
        r = subprocess.run([BASH, "sb/make_v15_submission.sh", a.cand], cwd=REPO, capture_output=True, text=True)
        print(r.stdout[-4000:], r.stderr[-2000:], flush=True)
        msg = (f"PIPELINE END: READY TO SUBMIT {a.cand}" if r.returncode == 0 else
               f"PIPELINE END: notebook step failed (code {r.returncode})")
    marker(a.cand).write_text(msg + "\n")
    print(msg, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
