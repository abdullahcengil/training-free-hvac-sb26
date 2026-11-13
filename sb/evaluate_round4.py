"""Score the round-4 hypotheses (docs/PREREGISTRATION_4.md).

    python -m sb.evaluate_round4 --results D:/SmartBuildings_data/results/heldout4
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sb.evaluate_prereg import load, score

WARM_STRIPS = ("phoenix_jun25", "phoenix_aug06", "atlanta_jul30", "atlanta_4", "singapore_2", "singapore_5")

# Pass marks, copied from the frozen pre-registration (docs/preregistration4/).
H1_MIN_REDUCTION_WARM = 0.06
H2_MIN_WINS_WARM = 5
H3_MIN_REDUCTION_COLD = 0.02
H4_MIN_REDUCTION_ALL = 0.05
H5_MAX_COMFORT_RATIO = 1.0


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", default="docs/RESULTS_ROUND4.md")
    a = ap.parse_args(argv)
    r = Path(a.results)
    cols = ["v10", "v9", "pid_water"]
    runs = {k: load(r / k) for k in cols}
    keys = sorted(runs["v10"])
    assert len(keys) == 12, f"expected 12 scenarios, got {len(keys)}"
    for k, v in runs.items():
        assert sorted(v) == keys, f"{k} is missing scenarios"
    warm = [k for k in keys if k.split("__")[1] in WARM_STRIPS]
    cold = [k for k in keys if k not in warm]
    assert len(cold) == 6 and len(warm) == 6
    sub = lambda c, ks: {k: runs[c][k] for k in ks}
    s = {c: score(runs[c]) for c in cols}
    sc = {c: score(sub(c, cold)) for c in cols}
    sw = {c: score(sub(c, warm)) for c in cols}
    red_warm = 1 - sw["v10"] / sw["v9"]
    wins_warm = sum(1 for k in warm if runs["v10"][k]["mean_reward"] > runs["v9"][k]["mean_reward"])
    red_cold = 1 - sc["v10"] / sc["v9"]
    red_all = 1 - s["v10"] / s["v9"]
    comfort = {c: sum(x["components"]["prod"] for x in runs[c].values()) for c in cols}
    ratio = comfort["v10"] / comfort["v9"]

    lines = ["# Round-4 results (pre-registered)", ""]
    info = r / "RUN_INFO.json"
    if info.exists():
        lines += [f"Run info: `{info.read_text().strip()}`", ""]
    lines += ["| scenario | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for k in warm + cold:
        lines.append(f"| {k} | " + " | ".join(f"{abs(runs[c][k]['mean_reward']):.5f}" for c in cols) + " |")
    lines.append("| **warm (6)** | " + " | ".join(f"{sw[c]:.5f}" for c in cols) + " |")
    lines.append("| **cold (6)** | " + " | ".join(f"{sc[c]:.5f}" for c in cols) + " |")
    lines.append("| **all (12)** | " + " | ".join(f"{s[c]:.5f}" for c in cols) + " |")
    lines.append("| comfort regret (sum, normalised) | " + " | ".join(f"{comfort[c]:.1f}" for c in cols) + " |")
    ok = lambda b: "PASSED" if b else "FAILED"
    lines += [
        "",
        f"- **R4-H1** (v10 at least {H1_MIN_REDUCTION_WARM:.0%} below v9 on the warm scenarios): reduction "
        f"{red_warm:.1%} -> **{ok(red_warm >= H1_MIN_REDUCTION_WARM)}**",
        f"- **R4-H2** (v10 better than v9 in at least {H2_MIN_WINS_WARM} of 6 warm scenarios): {wins_warm} of 6 -> "
        f"**{ok(wins_warm >= H2_MIN_WINS_WARM)}**",
        f"- **R4-H3** (v10 at least {H3_MIN_REDUCTION_COLD:.0%} below v9 on the cold scenarios): reduction "
        f"{red_cold:.1%} -> **{ok(red_cold >= H3_MIN_REDUCTION_COLD)}**",
        f"- **R4-H4** (v10 at least {H4_MIN_REDUCTION_ALL:.0%} below v9 on all 12): reduction "
        f"{red_all:.1%} -> **{ok(red_all >= H4_MIN_REDUCTION_ALL)}**",
        f"- **R4-H5** (v10 total comfort regret at most {H5_MAX_COMFORT_RATIO:.2f} x v9's, all 12): "
        f"{comfort['v10']:.1f} vs {comfort['v9']:.1f} (ratio {ratio:.2f}) -> **{ok(ratio <= H5_MAX_COMFORT_RATIO)}** "
        "(regret is negative; the ratio compares magnitudes)",
    ]
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
