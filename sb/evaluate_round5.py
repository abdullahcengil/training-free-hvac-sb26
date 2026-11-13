"""Score the round-5 hypotheses (docs/PREREGISTRATION_5.md).

    python -m sb.evaluate_round5 --results D:/SmartBuildings_data/results/heldout5
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sb.evaluate_prereg import load, score

WARM_STRIPS = ("phoenix_may14", "phoenix_sep17", "singapore_may21", "singapore_jan01", "atlanta_jun18", "atlanta_sep10")

# Pass marks, copied from the frozen pre-registration (docs/preregistration5/).
H1_MIN_REDUCTION_ALL = 0.15
H2_MIN_WINS_ALL = 10
H3_MIN_REDUCTION_COLD = 0.15
H4_MIN_REDUCTION_WARM = 0.15
H5_MAX_COMFORT_RATIO = 0.55


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", default="docs/RESULTS_ROUND5.md")
    a = ap.parse_args(argv)
    assert None not in (H1_MIN_REDUCTION_ALL, H2_MIN_WINS_ALL, H3_MIN_REDUCTION_COLD, H4_MIN_REDUCTION_WARM,
                        H5_MAX_COMFORT_RATIO), "pass marks not set"
    r = Path(a.results)
    # pid_water is descriptive (no hypothesis) and runs last; the hypotheses are scored without it if it is not done.
    cols = ["v11", "v10"] + (["pid_water"] if len(list((r / "pid_water").glob("*.json"))) >= 12 else [])
    runs = {k: load(r / k) for k in cols}
    keys = sorted(runs["v11"])
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
    red_all = 1 - s["v11"] / s["v10"]
    wins_all = sum(1 for k in keys if runs["v11"][k]["mean_reward"] > runs["v10"][k]["mean_reward"])
    red_cold = 1 - sc["v11"] / sc["v10"]
    red_warm = 1 - sw["v11"] / sw["v10"]
    comfort = {c: sum(x["components"]["prod"] for x in runs[c].values()) for c in cols}
    ratio = comfort["v11"] / comfort["v10"]

    lines = ["# Round-5 results (pre-registered)", ""]
    info = r / "RUN_INFO.json"
    if info.exists():
        lines += [f"Run info: `{info.read_text().strip()}`", ""]
    lines += ["| scenario | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for k in cold + warm:
        lines.append(f"| {k} | " + " | ".join(f"{abs(runs[c][k]['mean_reward']):.5f}" for c in cols) + " |")
    lines.append("| **cold (6)** | " + " | ".join(f"{sc[c]:.5f}" for c in cols) + " |")
    lines.append("| **warm (6)** | " + " | ".join(f"{sw[c]:.5f}" for c in cols) + " |")
    lines.append("| **all (12)** | " + " | ".join(f"{s[c]:.5f}" for c in cols) + " |")
    lines.append("| comfort regret (sum, normalised) | " + " | ".join(f"{comfort[c]:.1f}" for c in cols) + " |")
    ok = lambda b: "PASSED" if b else "FAILED"
    lines += [
        "",
        f"- **R5-H1** (v11 at least {H1_MIN_REDUCTION_ALL:.0%} below v10 on all 12): reduction "
        f"{red_all:.1%} -> **{ok(red_all >= H1_MIN_REDUCTION_ALL)}**",
        f"- **R5-H2** (v11 better than v10 in at least {H2_MIN_WINS_ALL} of 12): {wins_all} of 12 -> "
        f"**{ok(wins_all >= H2_MIN_WINS_ALL)}**",
        f"- **R5-H3** (v11 at least {H3_MIN_REDUCTION_COLD:.0%} below v10 on the cold scenarios): reduction "
        f"{red_cold:.1%} -> **{ok(red_cold >= H3_MIN_REDUCTION_COLD)}**",
        f"- **R5-H4** (v11 at least {H4_MIN_REDUCTION_WARM:.0%} below v10 on the warm scenarios): reduction "
        f"{red_warm:.1%} -> **{ok(red_warm >= H4_MIN_REDUCTION_WARM)}**",
        f"- **R5-H5** (v11 total comfort regret at most {H5_MAX_COMFORT_RATIO:.2f} x v10's, all 12): "
        f"{comfort['v11']:.1f} vs {comfort['v10']:.1f} (ratio {ratio:.2f}) -> **{ok(ratio <= H5_MAX_COMFORT_RATIO)}** "
        "(regret is negative; the ratio compares magnitudes)",
    ]
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
