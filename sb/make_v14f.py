"""Build the v14 policy file: the frozen v13 file (zonal_v11f.py) plus the offset_free option, nothing else.

The development file (policies/zonal.py) also carries training-only diagnostics (occ_oracle) that must not appear
in a submission, so v14's file is the v13 file with the same offset_free code inserted at the same place. Checks
(sb/nbcheck.py and sb.run): offset_free 0 gives v13 bit for bit; offset_free 3 gives the development file's actions.

    python -m sb.make_v14f D:/SmartBuildings_data/frozen/zonal_v11f.py D:/SmartBuildings_data/frozen/zonal_v14f.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PARAM_OLD = "    damping=0.7,           # fraction of the gap to target closed per step\n"
PARAM_NEW = PARAM_OLD + (
    "    offset_free=0,         # 1: damp only the move from the next predicted temperature, not the heat that holds the\n"
    "                           # zone (no steady droop under large losses or gains; stress test, 23 Oct)\n")
GOAL_OLD = '        goal = t2_free + p["damping"] * (aim - t2_free)\n'
GOAL_NEW = GOAL_OLD + '''        # Only in comfort time: outside it a zone below its floor costs nothing and the droop saves energy.
        of = p["offset_free"] if h2c == 0.0 else 0
        if of == 1:
            # Damp only the move from where the zone is going (t1), not the heat that holds it there. Damping the
            # whole gap from the free trajectory leaves a steady droop of about (1 - damping) / damping times the
            # zone's loss per step: large in high-loss zones in deep cold (docs/STRESS_TEST.md, building 7 in Duluth).
            base = np.where(need_heat, np.minimum(t1, aim), np.where(need_cool, np.maximum(t1, aim), t2_free))
            goal = base + p["damping"] * (aim - base)
        elif of == 2:
            # The droop is allowed only down to the band edge: the goal is never below a damped move from
            # min(t1, lo) (above max(t1, hi) when cooling). Mild loads change nothing; large ones no longer push
            # the zone out of its band.
            b_h = np.minimum(t1, lo)
            b_c = np.maximum(t1, hi)
            goal = np.where(need_heat, np.maximum(goal, b_h + p["damping"] * (aim - b_h)),
                            np.where(need_cool, np.minimum(goal, b_c + p["damping"] * (aim - b_c)), goal))
        elif of == 3:
            # Only a goal outside the comfort band itself is raised (lowered) to just inside it: the margins
            # (margin_heat, margin_cool) still absorb the droop under mild loads, as tuned.
            c_lo = np.minimum(self.comfort[0] + p["aim_inside"], aim)
            c_hi = np.maximum(self.comfort[1] - p["aim_inside"], aim)
            goal = np.where(need_heat, np.maximum(goal, c_lo), np.where(need_cool, np.minimum(goal, c_hi), goal))
'''


def main(src: str, dst: str) -> None:
    s = Path(src).read_text(encoding="utf-8")
    for old, new in ((PARAM_OLD, PARAM_NEW), (GOAL_OLD, GOAL_NEW)):
        assert s.count(old) == 1, old
        s = s.replace(old, new)
    assert not Path(dst).exists(), f"{dst} exists"
    Path(dst).write_text(s, encoding="utf-8")
    print("wrote", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
