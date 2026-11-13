"""Read the v15 screen by its rule (docs/BIGDEV.md, fixed before any candidate run).

A candidate passes if its mean loss over the 12 full-size scenarios (2880 steps) is at least 1 % below v14's and no
scenario is more than 2 % worse. Of the passing candidates the lowest mean goes on; a simpler one (fewer options) is
preferred if within 0.3 % of it. Prints the per-scenario table and the decision.

    python -m sb.v15_screen_eval
"""

from __future__ import annotations

import json
from pathlib import Path

R = Path("D:/SmartBuildings_data/results/bigdev")
CANDS = {"A_sus": 1, "B_glo": 1, "C_sus_glo": 2, "D_sus_h48": 2}   # number of options


def load(tag: str) -> dict[str, tuple[float, float]]:
    out = {}
    for f in (R / tag).glob("*.json"):
        j = json.loads(f.read_text())
        out[f.stem] = (abs(j["mean_reward"]), -0.6 * j["components"]["prod"] / j["steps"])
    return out


def decide(say=print) -> str | None:
    """The candidate the rule chooses, or None (none passes yet)."""
    ref = load("v14")
    say(f"v14: {len(ref)} scenarios, mean {sum(v[0] for v in ref.values()) / max(len(ref), 1):.5f}")
    passing = []
    for tag, n_opt in CANDS.items():
        c = load(tag)
        common = sorted(set(ref) & set(c))
        if not common:
            continue
        m_ref = sum(ref[s][0] for s in common) / len(common)
        m_c = sum(c[s][0] for s in common) / len(common)
        worst = max(c[s][0] / ref[s][0] - 1 for s in common)
        better = sum(c[s][0] < ref[s][0] for s in common)
        complete = len(common) == 12
        ok = complete and m_c <= 0.99 * m_ref and worst <= 0.02
        status = ("PASS" if ok else "FAIL (a scenario more than 2 % worse)" if worst > 0.02 else
                  "fail (mean not 1 % below)" if complete else "incomplete")
        say(f"\n{tag}: {len(common)}/12, mean {m_c:.5f} vs {m_ref:.5f} ({100 * (m_c / m_ref - 1):+.2f} %), "
            f"better in {better}, worst {100 * worst:+.2f} % -> {status}")
        for s in common:
            say(f"   {s:30s} {ref[s][0]:.5f} -> {c[s][0]:.5f} ({100 * (c[s][0] / ref[s][0] - 1):+6.2f} %)  "
                f"comfort {ref[s][1]:.5f} -> {c[s][1]:.5f}")
        if ok:
            passing.append((m_c, n_opt, tag))
    if not passing:
        say("\nno candidate passes (yet)")
        return None
    best = min(passing)
    simpler = [p for p in passing if p[1] < best[1] and p[0] <= 1.003 * best[0]]
    choice = min(simpler) if simpler else best
    say(f"\nchosen by the rule: {choice[2]} (mean {choice[0]:.5f})")
    return choice[2]


def main() -> None:
    decide()


if __name__ == "__main__":
    main()
