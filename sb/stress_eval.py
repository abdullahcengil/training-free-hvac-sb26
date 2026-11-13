"""Read the climate stress test by the rule in docs/STRESS_TEST.md (fixed before any run).

    python -m sb.stress_eval D:/SmartBuildings_data/results/stress

1. Ratio of means v13 / pid_water over all scenarios: <= 0.163 keeps the advantage, >= 0.204 loses ground.
2. Weak spot: a city with ratio of means >= 0.204 over its scenarios, or any scenario where v13 is worse than pid_water.
Also prints each scenario's comfort share of v13's loss (0.6 x productivity regret over the total), for diagnosis.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

KEEP, LOSE = 0.163, 0.204
STEPS = 8640


def load(d: Path) -> dict[str, dict]:
    return {f.stem: json.loads(f.read_text()) for f in sorted(d.glob("*.json"))}


def main(root: str) -> None:
    v, p = load(Path(root) / "v13"), load(Path(root) / "pid_water")
    keys = sorted(set(v) & set(p))
    lv = {k: abs(v[k]["mean_reward"]) for k in keys}
    lp = {k: abs(p[k]["mean_reward"]) for k in keys}
    ratio = sum(lv.values()) / sum(lp.values())
    verdict = "keeps its advantage" if ratio <= KEEP else ("loses ground" if ratio >= LOSE else "between the marks")
    print(f"{len(keys)} scenarios; v13 {sum(lv.values()) / len(keys):.5f}, pid_water {sum(lp.values()) / len(keys):.5f}")
    print(f"1. ratio of means {ratio:.3f}: {verdict} (keep <= {KEEP}, lose >= {LOSE})")
    city = defaultdict(list)
    for k in keys:
        city[k.split("__")[1].rsplit("_", 1)[0]].append(k)
    weak = []
    print("2. by city (ratio of means over its scenarios):")
    for c, ks in sorted(city.items(), key=lambda kv: -sum(lv[k] for k in kv[1]) / sum(lp[k] for k in kv[1])):
        r = sum(lv[k] for k in ks) / sum(lp[k] for k in ks)
        flag = "  WEAK" if r >= LOSE else ""
        weak += [c] if flag else []
        print(f"   {c:13s} {r:.3f} ({len(ks)} scenarios){flag}")
    worse = [k for k in keys if lv[k] > lp[k]]
    print(f"   scenarios where v13 is worse than pid_water: {worse or 'none'}")
    print("comfort share of v13's loss, highest five:")
    share = {k: 0.6 * abs(v[k]["components"]["prod"]) / (lv[k] * STEPS) for k in keys}
    for k in sorted(share, key=share.get, reverse=True)[:5]:
        print(f"   {k:40s} {100 * share[k]:.1f} %  (v13 {lv[k]:.5f}, pid_water {lp[k]:.5f}, ratio {lv[k] / lp[k]:.3f})")
    print("weak spots:", weak + worse or "none")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "D:/SmartBuildings_data/results/stress")
