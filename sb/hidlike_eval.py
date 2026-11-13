"""Read docs/HIDLIKE.md by its rules (written before any run).

1. Subsidy: pid_water on the patched simulator (results/tankfix/pid_water_stressjan) against its shipped runs on the
   same ten January stress scenarios (results/stress/pid_water). Mean increase >= 15 %: the subsidy alone can explain a
   large part of the public gap.
2. Hidden-like: ratio of means v14 / pid_water over the 24 hidden-like scenarios. >= 0.160 reproduces the public gap
   (0.164); <= 0.150 does not; in between unclear. Also per window and per building, and the comfort share.

    python -m sb.hidlike_eval
"""

from __future__ import annotations

import json
from pathlib import Path

R = Path("D:/SmartBuildings_data/results")


def load(d: Path) -> dict:
    out = {}
    for f in sorted(d.glob("*.json")):
        j = json.loads(f.read_text())
        if j.get("steps") == 8640:
            out[f.stem] = j
    return out


def main() -> None:
    fix, ship = load(R / "tankfix" / "pid_water_stressjan"), load(R / "stress" / "pid_water")
    common = sorted(set(fix) & set(ship))
    if common:
        ch = [(-fix[k]["mean_reward"]) / (-ship[k]["mean_reward"]) - 1 for k in common]
        for k, c in zip(common, ch):
            print(f"subsidy {k}: {100 * c:+.1f} %")
        m = sum(ch) / len(ch)
        print(f"SUBSIDY mean {100 * m:+.1f} % over {len(ch)} -> {'large (>= 15 %)' if m >= 0.15 else 'small (< 15 %)'}")
    v, p = load(R / "hidlike" / "v14"), load(R / "hidlike" / "pid_water")
    both = sorted(set(v) & set(p))
    if not both:
        return
    lv = {k: -v[k]["mean_reward"] for k in both}
    lp = {k: -p[k]["mean_reward"] for k in both}
    ratio = sum(lv.values()) / sum(lp.values())
    verdict = "reproduces the public gap" if ratio >= 0.160 else ("does not" if ratio <= 0.150 else "unclear")
    print(f"HIDLIKE ratio of means v14/pid_water {ratio:.3f} over {len(both)} of 24 -> {verdict}")
    for w in ("chicago_jan15", "helena_jan15", "dubai_jul15", "lasvegas_jul15"):
        ks = [k for k in both if k.endswith(w)]
        if ks:
            print(f"  {w}: v14 {sum(lv[k] for k in ks) / len(ks):.5f} pid {sum(lp[k] for k in ks) / len(ks):.5f} "
                  f"ratio {sum(lv[k] for k in ks) / sum(lp[k] for k in ks):.3f} (n={len(ks)})")
    for k in both:
        print(f"  {k}: v14 {lv[k]:.5f} pid {lp[k]:.5f} ratio {lv[k] / lp[k]:.3f}")


if __name__ == "__main__":
    main()
