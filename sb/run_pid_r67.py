"""pid_water on the buildings of blind rounds 6 and 7 (docs/BASELINE_R67.md): descriptive, no hypothesis. Both rounds
ran only our versions, so their twelve full-size scenarios are missing from the transfer figure (sb/fig_transfer.py).
First 2880 steps each, as in the rounds. Restartable (sb.memsched); start it after round 7 has finished.

    python -m sb.run_pid_r67 >> D:/SmartBuildings_data/pid_r67.log 2>&1
    python -m sb.run_pid_r67 --read
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

from sb import memsched

DATA = Path("D:/SmartBuildings_data")
R = DATA / "results"
# (round, scenario root, results folder, our arms in that round)
ROUNDS = [(6, DATA / "round6h/scenarios", R / "round6h", ["ed1", "v14"]),
          (7, DATA / "round7/scenarios", R / "round7", ["chm", "v15"])]
STEPS = 2880


def scenarios(root: Path) -> list[str]:
    return sorted(f"{c.parent.parent.name}__{c.parent.name}" for c in root.glob("*/*/config.gin"))


def jobs() -> list[dict]:
    return [memsched.job({"policy": "baseline:pid_water", "base": "none", "out": str(out / "pid_water"),
                          "scenario": s, "root": str(root)}, STEPS)
            for _, root, out, _ in ROUNDS for s in scenarios(root)]


def plan() -> tuple[list[dict], list[dict]]:
    return [j for j in jobs() if not Path(j["result"]).exists()], []


def loss(f: Path) -> float:
    return float(-np.load(f).astype(float)[:STEPS, 0].mean())


def read() -> None:
    for rnd, root, out, arms in ROUNDS:
        print(f"round {rnd} (ours: {', '.join(arms)}; ratio = ours / pid_water)")
        for s in scenarios(root):
            p = out / "pid_water" / f"{s}.npy"
            if not p.exists():
                print(f"  {s}: pid_water not finished")
                continue
            lp = loss(p)
            cols = [f"pid_water {lp:.5f}"]
            for a in arms:
                f = out / a / f"{s}.npy"
                if f.exists():
                    la = loss(f)
                    cols.append(f"{a} {la:.5f} (x{la / lp:.3f})")
            print(f"  {s:38s} " + "  ".join(cols))


def main() -> None:
    if "--read" in sys.argv:
        read()
        return
    say = lambda m: print(f"{time.strftime('%d %b %H:%M:%S')} {m}", flush=True)
    say(f"pid_water r6-r7 starts: {len(plan()[0])} of {len(jobs())} runs to do")
    memsched.run(plan, max_jobs=3, reserve=0.5, say=say)
    say("pid_water r6-r7 END")
    read()


if __name__ == "__main__":
    main()
