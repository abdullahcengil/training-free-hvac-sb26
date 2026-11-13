"""Apply the v14 rule (docs/TUNING_LOG.md, 23 Oct 21:25): offset_free 3 becomes v14 if the 30-training mean is at most
0.3 % above v13's and the 40-stress mean at least 1 % below v13's.

    python -m sb.v14_eval
"""

from __future__ import annotations

import json
from pathlib import Path

R = Path("D:/SmartBuildings_data/results")


def mean(d: Path, names: list[str]) -> float:
    return sum(abs(json.loads((d / f"{n}.json").read_text())["mean_reward"]) for n in names) / len(names)


def main() -> None:
    train = sorted(f.stem for f in (R / "dev13_8640/v13_all30").glob("*.json"))
    stress = sorted(f.stem for f in (R / "stress/v13").glob("*.json"))
    new = R / "dev14_8640/of3"
    done = {f.stem for f in new.glob("*.json")}
    missing = [n for n in train + stress if n not in done]
    if missing:
        print(f"{len(missing)} runs missing, e.g. {missing[:3]}")
        return
    t13, t14 = mean(R / "dev13_8640/v13_all30", train), mean(new, train)
    s13, s14 = mean(R / "stress/v13", stress), mean(new, stress)
    rt, rs = t14 / t13 - 1, s14 / s13 - 1
    print(f"training (30): v13 {t13:.6f}  offset_free 3 {t14:.6f}  {100 * rt:+.2f} %  (mark: at most +0.3 %)")
    print(f"stress (40):   v13 {s13:.6f}  offset_free 3 {s14:.6f}  {100 * rs:+.2f} %  (mark: at most -1 %)")
    for label, names, d13 in (("training", train, R / "dev13_8640/v13_all30"), ("stress", stress, R / "stress/v13")):
        ch = sorted(((abs(json.loads((new / f"{n}.json").read_text())["mean_reward"])
                      / abs(json.loads((d13 / f"{n}.json").read_text())["mean_reward"]) - 1), n) for n in names)
        better = sum(c < -1e-9 for c, _ in ch)
        worse = sum(c > 1e-9 for c, _ in ch)
        print(f"   {label}: better {better}, worse {worse}; best {100 * ch[0][0]:+.2f} % ({ch[0][1]}), "
              f"worst {100 * ch[-1][0]:+.2f} % ({ch[-1][1]})")
    print("v14:", "YES" if rt <= 0.003 and rs <= -0.01 else "NO")


if __name__ == "__main__":
    main()
