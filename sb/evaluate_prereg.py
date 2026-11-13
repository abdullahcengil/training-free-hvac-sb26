"""Score the pre-registered hypotheses H1-H4 (docs/PREREGISTRATION.md).

    python -m sb.evaluate_prereg --heldout D:/SmartBuildings_data/results/heldout \
        --train-ours D:/SmartBuildings_data/results/train_8640/zonal \
        --train-baselines D:/SmartBuildings_data/starter-kit/baseline_returns.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BASELINES = ["bang_bang", "fixed_setpoint", "pid", "pid_water"]


def load(folder: Path) -> dict[str, dict]:
    return {f.stem: json.loads(f.read_text()) for f in sorted(folder.glob("*.json"))
            if f.name not in ("RUN_INFO.json", "RUN_DONE.json")}


def score(runs: dict[str, dict]) -> float:
    return sum(abs(r["mean_reward"]) for r in runs.values()) / len(runs)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--heldout", required=True)
    ap.add_argument("--train-ours")
    ap.add_argument("--train-baselines")
    ap.add_argument("--out", default="docs/RESULTS_HELDOUT.md")
    a = ap.parse_args(argv)
    h = Path(a.heldout)
    ours = load(h / "zonal")
    base = {b: load(h / b) for b in BASELINES}
    keys = sorted(ours)
    assert len(keys) == 12, f"expected 12 held-out scenarios, got {len(keys)}"
    for b in BASELINES:
        assert sorted(base[b]) == keys, f"{b} is missing scenarios"
    s_ours = score(ours)
    s_base = {b: score(base[b]) for b in BASELINES}
    best_b = min(s_base, key=s_base.get)
    h1_red = 1 - s_ours / s_base[best_b]
    wins = sum(1 for k in keys if ours[k]["mean_reward"] > max(base[b][k]["mean_reward"] for b in BASELINES))
    comfort_ours = sum(r["components"]["prod"] for r in ours.values())
    comfort_pw = sum(r["components"]["prod"] for r in base["pid_water"].values())
    h3_ratio = comfort_ours / comfort_pw if comfort_pw else float("nan")

    lines = ["# Held-out results (pre-registered)", ""]
    info = h / "RUN_INFO.json"
    if info.exists():
        lines.append(f"Run info: `{info.read_text().strip()}`")
        lines.append("")
    lines += ["| scenario | zonal | " + " | ".join(BASELINES) + " |",
              "|---|---|" + "---|" * len(BASELINES)]
    for k in keys:
        lines.append(f"| {k} | {abs(ours[k]['mean_reward']):.5f} | "
                     + " | ".join(f"{abs(base[b][k]['mean_reward']):.5f}" for b in BASELINES) + " |")
    lines.append(f"| **score** | **{s_ours:.5f}** | " + " | ".join(f"{s_base[b]:.5f}" for b in BASELINES) + " |")
    lines += ["",
              f"- **H1** (score at least 30 % below the best baseline, {best_b}): reduction {h1_red:.1%} -> "
              f"**{'PASSED' if h1_red >= 0.30 else 'FAILED'}**",
              f"- **H2** (better than every baseline in at least 10 of 12 scenarios): {wins} of 12 -> "
              f"**{'PASSED' if wins >= 10 else 'FAILED'}**",
              f"- **H3** (total comfort regret at most 10 % of pid_water's): {h3_ratio:.1%} -> "
              f"**{'PASSED' if h3_ratio <= 0.10 else 'FAILED'}**"]
    if a.train_ours and a.train_baselines:
        tr = load(Path(a.train_ours))
        tb = json.loads(Path(a.train_baselines).read_text())
        s_tr = score(tr)
        tb_scores = {b: sum(abs(tb[s][b]) / 8640 for s in tb) / len(tb) for b in BASELINES}
        best_tr = min(tb_scores, key=tb_scores.get)
        lines.append(f"- **H4** (descriptive): zonal / best baseline = {s_tr / tb_scores[best_tr]:.3f} on the "
                     f"30 training scenarios ({best_tr}; shipped baseline returns) and "
                     f"{s_ours / s_base[best_b]:.3f} held out ({best_b}).")
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
