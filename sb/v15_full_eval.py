"""The v15 full check (docs/BIGDEV.md, fixed 25 Oct before any candidate run): the chosen candidate becomes v15 only if
1. its mean over the 30 training scenarios (full length) is at most 0.3 % above v14's 0.007328,
2. its mean over the 40 stress scenarios (full length) is not above v14's 0.007302,
3. its mean over the full-size held-out set is below v14's (sb/v15_bigtest_eval.py).
v14's two means are recomputed from its result files as a check on the numbers in the rule. Exit code 0 = all pass,
1 = a fail, 2 = runs missing.

    python -m sb.v15_full_eval --cand A_sus
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sb import v15_bigtest_eval

R = Path("D:/SmartBuildings_data/results")
FULL = Path(__file__).resolve().parent / "jobs_v14_full.json"


def mean(d: Path, names: list[str]) -> float | None:
    fs = [d / f"{n}.json" for n in names]
    if not all(f.exists() for f in fs):
        return None
    return sum(abs(json.loads(f.read_text())["mean_reward"]) for f in fs) / len(fs)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    a = ap.parse_args(argv)
    jobs = json.loads(FULL.read_text())
    train = [j["scenario"] for j in jobs if "root" not in j]
    stress = [j["scenario"] for j in jobs if "root" in j]
    v14, cand = R / "dev14_8640/of3", R / f"dev15_8640/{a.cand}"
    t14, s14 = mean(v14, train), mean(v14, stress)
    tc, sc = mean(cand, train), mean(cand, stress)
    print(f"v14 from its files: training {t14:.6f} (rule 0.007328), stress {s14:.6f} (rule 0.007302)")
    code = 0
    if tc is None or sc is None:
        n = sum((cand / f"{s}.json").exists() for s in train + stress)
        print(f"{a.cand}: {n}/70 training and stress runs")
        code = 2
    else:
        i1, i2 = tc <= 1.003 * 0.007328, sc <= 0.007302
        print(f"1. training (30): {a.cand} {tc:.6f} ({100 * (tc / 0.007328 - 1):+.2f} % vs v14; mark +0.3 %) -> "
              f"{'pass' if i1 else 'FAIL'}")
        print(f"2. stress (40):   {a.cand} {sc:.6f} ({100 * (sc / 0.007302 - 1):+.2f} % vs v14; mark 0 %) -> "
              f"{'pass' if i2 else 'FAIL'}")
        for label, names in (("training", train), ("stress", stress)):
            ch = sorted((abs(json.loads((cand / f"{n}.json").read_text())["mean_reward"])
                         / abs(json.loads((v14 / f"{n}.json").read_text())["mean_reward"]) - 1, n) for n in names)
            print(f"   {label}: better {sum(c < -1e-9 for c, _ in ch)}, worse {sum(c > 1e-9 for c, _ in ch)}; "
                  f"best {100 * ch[0][0]:+.2f} % ({ch[0][1]}), worst {100 * ch[-1][0]:+.2f} % ({ch[-1][1]})")
        code = 0 if i1 and i2 else 1
    print("3. full-size held-out set:")
    c3 = v15_bigtest_eval.main(["--cand", a.cand])
    if code == 2 or c3 == 2:
        return 2
    ok = code == 0 and c3 == 0
    print(f"v15 = {a.cand}: {'YES' if ok else 'NO'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
