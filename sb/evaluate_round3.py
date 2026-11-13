"""Score the round-3 hypotheses (docs/PREREGISTRATION_3.md).

    python -m sb.evaluate_round3 --results D:/SmartBuildings_data/results/heldout3
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sb.evaluate_prereg import load, score

# Pass marks, copied from the frozen pre-registration (docs/preregistration3/).
H1_MIN_REDUCTION_COLD = 0.05
H2_MIN_WINS_COLD = 5
H3_MAX_INCREASE_WARM = 0.02


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", default="docs/RESULTS_ROUND3.md")
    a = ap.parse_args(argv)
    r = Path(a.results)
    cols = ["v9", "v8", "pid_water"]
    runs = {k: load(r / k) for k in cols}
    keys = sorted(runs["v9"])
    assert len(keys) == 12, f"expected 12 scenarios, got {len(keys)}"
    for k, v in runs.items():
        assert sorted(v) == keys, f"{k} is missing scenarios"
    cold = [k for k in keys if k.endswith("_dec")]
    warm = [k for k in keys if k not in cold]
    assert len(cold) == 6 and len(warm) == 6
    sub = lambda c, ks: {k: runs[c][k] for k in ks}
    s = {c: score(runs[c]) for c in cols}
    sc = {c: score(sub(c, cold)) for c in cols}
    sw = {c: score(sub(c, warm)) for c in cols}
    red_cold = 1 - sc["v9"] / sc["v8"]
    wins_cold = sum(1 for k in cold if runs["v9"][k]["mean_reward"] > runs["v8"][k]["mean_reward"])
    inc_warm = sw["v9"] / sw["v8"] - 1
    comfort = {c: sum(x["components"]["prod"] for x in runs[c].values()) for c in cols}

    lines = ["# Round-3 results (pre-registered)", ""]
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
    lines += [
        "",
        f"- **R3-H1** (v9 at least {H1_MIN_REDUCTION_COLD:.0%} below v8 on the cold scenarios): reduction "
        f"{red_cold:.1%} -> **{'PASSED' if red_cold >= H1_MIN_REDUCTION_COLD else 'FAILED'}**",
        f"- **R3-H2** (v9 better than v8 in at least {H2_MIN_WINS_COLD} of 6 cold scenarios): {wins_cold} of 6 -> "
        f"**{'PASSED' if wins_cold >= H2_MIN_WINS_COLD else 'FAILED'}**",
        f"- **R3-H3** (v9 at most {H3_MAX_INCREASE_WARM:.0%} worse than v8 on the warm scenarios): change "
        f"{inc_warm:+.1%} -> **{'PASSED' if inc_warm <= H3_MAX_INCREASE_WARM else 'FAILED'}**",
        f"- **R3-H4** (v9 total comfort regret at most v8's, all 12): {comfort['v9']:.1f} vs {comfort['v8']:.1f} -> "
        f"**{'PASSED' if comfort['v9'] >= comfort['v8'] else 'FAILED'}** (regret is negative; closer to 0 is better)",
    ]
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
