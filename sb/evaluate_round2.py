"""Score the round-2 hypotheses (docs/PREREGISTRATION_2.md).

    python -m sb.evaluate_round2 --results D:/SmartBuildings_data/results/heldout2
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sb.evaluate_prereg import BASELINES, load, score

# Pass marks, copied from the frozen pre-registration (docs/preregistration2/).
H1_MIN_REDUCTION_VS_V7 = 0.20
H2_MIN_WINS_VS_V7 = 10
H3_MIN_REDUCTION_VS_BEST_BASELINE = 0.30


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", default="docs/RESULTS_ROUND2.md")
    a = ap.parse_args(argv)
    r = Path(a.results)
    runs = {k: load(r / k) for k in ["v8", "v7", *BASELINES]}
    keys = sorted(runs["v8"])
    assert len(keys) == 12, f"expected 12 scenarios, got {len(keys)}"
    for k, v in runs.items():
        assert sorted(v) == keys, f"{k} is missing scenarios"
    s = {k: score(v) for k, v in runs.items()}
    best_b = min(BASELINES, key=s.get)
    red_v7 = 1 - s["v8"] / s["v7"]
    wins_v7 = sum(1 for k in keys if runs["v8"][k]["mean_reward"] > runs["v7"][k]["mean_reward"])
    red_b = 1 - s["v8"] / s[best_b]
    comfort = {k: sum(x["components"]["prod"] for x in v.values()) for k, v in runs.items()}

    cols = ["v8", "v7", *BASELINES]
    lines = ["# Round-2 results (pre-registered)", ""]
    info = r / "RUN_INFO.json"
    if info.exists():
        lines += [f"Run info: `{info.read_text().strip()}`", ""]
    lines += ["| scenario | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for k in keys:
        lines.append(f"| {k} | " + " | ".join(f"{abs(runs[c][k]['mean_reward']):.5f}" for c in cols) + " |")
    lines.append("| **score** | " + " | ".join(f"**{s[c]:.5f}**" if c == "v8" else f"{s[c]:.5f}" for c in cols) + " |")
    lines.append("| comfort regret (sum, normalised) | " + " | ".join(f"{comfort[c]:.1f}" for c in cols) + " |")
    lines += [
        "",
        f"- **R2-H1** (v8 score at least {H1_MIN_REDUCTION_VS_V7:.0%} below v7's): reduction {red_v7:.1%} -> "
        f"**{'PASSED' if red_v7 >= H1_MIN_REDUCTION_VS_V7 else 'FAILED'}**",
        f"- **R2-H2** (v8 better than v7 in at least {H2_MIN_WINS_VS_V7} of 12): {wins_v7} of 12 -> "
        f"**{'PASSED' if wins_v7 >= H2_MIN_WINS_VS_V7 else 'FAILED'}**",
        f"- **R2-H3** (v8 at least {H3_MIN_REDUCTION_VS_BEST_BASELINE:.0%} below the best baseline, {best_b}): "
        f"reduction {red_b:.1%} -> **{'PASSED' if red_b >= H3_MIN_REDUCTION_VS_BEST_BASELINE else 'FAILED'}**",
        f"- **R2-H4** (v8 total comfort regret at most v7's): {comfort['v8']:.1f} vs {comfort['v7']:.1f} -> "
        f"**{'PASSED' if comfort['v8'] >= comfort['v7'] else 'FAILED'}** (regret is negative; closer to 0 is better)",
    ]
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
