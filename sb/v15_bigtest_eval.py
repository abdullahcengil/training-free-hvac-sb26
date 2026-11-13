"""Item 3 of the v15 full check (docs/BIGDEV.md): on the full-size held-out set the candidate's mean must be below
v14's. Also reported, not used for the decision: better/worse count, cold and hot means, comfort. Exit code 0 = pass.

    python -m sb.v15_bigtest_eval --cand A_sus
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

R = Path("D:/SmartBuildings_data/results/bigtest")


def load(tag: str) -> dict:
    out = {}
    for f in (R / tag).glob("*.json"):
        j = json.loads(f.read_text())
        out[f.stem] = (abs(j["mean_reward"]), -0.6 * j["components"]["prod"] / j["steps"])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    a = ap.parse_args(argv)
    v, c = load("v14"), load(a.cand)
    common = sorted(set(v) & set(c))
    for s in common:
        print(f"   {s:30s} {v[s][0]:.5f} -> {c[s][0]:.5f} ({100 * (c[s][0] / v[s][0] - 1):+6.2f} %)  comfort "
              f"{v[s][1]:.5f} -> {c[s][1]:.5f}")
    if len(common) < 12:
        print(f"incomplete: {len(common)}/12")
        return 2
    mv, mc = (sum(d[s][0] for s in common) / len(common) for d in (v, c))
    cold = [s for s in common if "jan" in s]
    hot = [s for s in common if "jul" in s]
    better = sum(c[s][0] < v[s][0] for s in common)
    print(f"held-out mean v14 {mv:.5f}, {a.cand} {mc:.5f} ({100 * (mc / mv - 1):+.2f} %), better in {better} of 12; "
          f"cold {sum(c[s][0] for s in cold) / len(cold):.5f} vs {sum(v[s][0] for s in cold) / len(cold):.5f}, "
          f"hot {sum(c[s][0] for s in hot) / len(hot):.5f} vs {sum(v[s][0] for s in hot) / len(hot):.5f}")
    ok = mc < mv
    print("item 3 PASSES" if ok else "item 3 FAILS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
