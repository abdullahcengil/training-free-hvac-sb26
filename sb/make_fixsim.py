"""A patched copy of the simulator with both proposed energy fixes (docs/FIXSIM.md): the energy-balanced tank
(sb/make_tankfix.py, starter-kit pull request 2) and return air mixed by airflow, not floor area (pull request 3; forum
thread 753804). Our own code, written from the description; the pull requests' files are not downloaded or run.

    python -m sb.make_fixsim --out D:/SmartBuildings_data/kit_fixed
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

FILE = "smart_buildings/smart_control/simulator/simulator_flexible_floor_plan.py"
# Each AHU's recirculated air is the VAVs' extract temperatures mixed by airflow. The handler's cap scales all its VAVs
# alike, so the uncapped demand gives the same weights; a VAV with no air keeps only the 1e-5 demand floor.
EDITS = [("      ahu_temp_weighted_sum[ahu_id] += v_sensing_temp * v_area\n      ahu_area_total[ahu_id] += v_area\n",
          "      v_flow = vav.unrestricted_flow_rate_demand  # return air mixed by airflow (sb/make_fixsim.py)\n"
          "      ahu_temp_weighted_sum[ahu_id] += v_sensing_temp * v_flow\n      ahu_area_total[ahu_id] += v_flow\n"),
         ("        ahu_temp_weighted_sum[ahu_id] += v_sensing_temp * v_area\n        ahu_area_total[ahu_id] += v_area\n",
          "        v_flow = vav.unrestricted_flow_rate_demand  # return air mixed by airflow (sb/make_fixsim.py)\n"
          "        ahu_temp_weighted_sum[ahu_id] += v_sensing_temp * v_flow\n        ahu_area_total[ahu_id] += v_flow\n")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src, out = Path("D:/SmartBuildings_data/kit_tankfix"), Path(a.out)
    shutil.copytree(src, out, dirs_exist_ok=True)
    f = out / FILE
    s = f.read_text(encoding="utf-8")
    for old, new in EDITS:
        assert s.count(old) == 1, old
        s = s.replace(old, new)
    f.write_text(s, encoding="utf-8")
    print("patched", f)


if __name__ == "__main__":
    main()
