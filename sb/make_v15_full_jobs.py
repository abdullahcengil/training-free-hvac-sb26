"""Jobs for the v15 full check (docs/BIGDEV.md): the chosen candidate on the 30 training and 40 stress scenarios
(full length) and, with v14, on the full-size held-out set (2880 steps).

    python -m sb.make_v15_full_jobs --cand A_sus
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CANDS = {"A_sus": {"glide_sus": 1}, "B_glo": {"m2_lo": [-0.8, 0.02, -2.0, 0.0, -0.5]},
         "C_sus_glo": {"glide_sus": 1, "m2_lo": [-0.8, 0.02, -2.0, 0.0, -0.5]},
         "D_sus_h48": {"glide_sus": 1, "glide_h": 48.0}}
POL = "D:/SmartBuildings_data/frozen/zonal_v15dev_a.py:TransferPolicy"
V14F = "D:/SmartBuildings_data/frozen/zonal_v14f.py:TransferPolicy"
BIGTEST = "D:/SmartBuildings_data/bigtest/scenarios"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True, choices=sorted(CANDS))
    a = ap.parse_args(argv)
    v14 = json.loads(Path("submission/V14_PARAMS.json").read_text())
    kw = dict(v14)
    kw.update(CANDS[a.cand])
    full = json.loads(Path("sb/jobs_v14_full.json").read_text())   # 30 training + 40 stress, longest first
    jobs = []
    for j in full:
        jj = {"policy": POL, "base": "none", "kwargs": kw, "out": f"D:/SmartBuildings_data/results/dev15_8640/{a.cand}",
              "scenario": j["scenario"]}
        if "root" in j:
            jj["root"] = j["root"]
        jobs.append(jj)
    Path("sb/jobs_v15_full.json").write_text(json.dumps(jobs, indent=1))
    scen = sorted(f"{p.parent.name}__{p.name}" for p in Path(BIGTEST).glob("*/*") if (p / "config.gin").exists())
    big = []
    for s in sorted(scen, key=lambda s: "7105" not in s):   # the largest building first
        big.append({"policy": V14F, "base": "none", "kwargs": v14, "out": "D:/SmartBuildings_data/results/bigtest/v14",
                    "scenario": s, "root": BIGTEST})
        big.append({"policy": POL, "base": "none", "kwargs": kw, "out": f"D:/SmartBuildings_data/results/bigtest/{a.cand}",
                    "scenario": s, "root": BIGTEST})
    Path("sb/jobs_v15_bigtest.json").write_text(json.dumps(big, indent=1))
    print(len(jobs), "full-length jobs,", len(big), "held-out jobs")


if __name__ == "__main__":
    main()
