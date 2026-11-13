"""Audit / descriptive analysis (11 Nov 2026): where does the gap to pid_water come from? For every scenario outside
development (the 122 of Section 4.1), split the mean loss per step into the comfort term (0.6 p) and the energy and
carbon part (loss minus comfort term), for our frozen version and for pid_water. Reads result files only.

    D:/SmartBuildings_data/starter-kit/.venv/Scripts/python audit/split.py
"""
from pathlib import Path

import numpy as np

R = Path("D:/SmartBuildings_data/results")
GROUPS = {
    "rounds 2-5 (48)": [("heldout2", "v8"), ("heldout3", "v9"), ("heldout4", "v10"), ("heldout5", "v11")],
    "new climates (40)": [("stress", "v13")],
    "full size (34)": [("bigbld", "v14"), ("bigdev", "v14"), ("round6h", "ed1"), ("round7", "chm"), ("round8", "v16")],
}


def parts(f: Path, n: int) -> tuple[float, float]:
    a = np.load(f).astype(float)[:n]
    loss, comfort = -a[:, 0].mean(), -0.6 * a[:, 1].mean()
    return comfort, loss - comfort


def main() -> None:
    tot = np.zeros(4)
    n_all = 0
    rows = []
    for g, sets in GROUPS.items():
        v = []
        for folder, ours in sets:
            for f in sorted((R / folder / ours).glob("*.npy")):
                p = R / folder / "pid_water" / f.name
                if not p.exists():
                    continue
                n = min(len(np.load(f)), len(np.load(p)))
                v.append(parts(f, n) + parts(p, n))
        v = np.array(v)          # columns: our comfort, our energy, pid comfort, pid energy
        m = v.mean(0)
        tot += v.sum(0)
        n_all += len(v)
        gap = (m[2] + m[3]) - (m[0] + m[1])
        rows.append((g, len(v), m, gap))
        print(f"{g}: n {len(v)}; ours comfort {m[0]:.5f} energy+carbon {m[1]:.5f} (loss {m[0] + m[1]:.5f}); "
              f"pid_water comfort {m[2]:.5f} energy+carbon {m[3]:.5f} (loss {m[2] + m[3]:.5f}); "
              f"comfort share of pid_water's loss {m[2] / (m[2] + m[3]):.1%}, of ours {m[0] / (m[0] + m[1]):.1%}; "
              f"energy ratio ours/pid {m[1] / m[3]:.3f}; comfort ratio {m[0] / m[2]:.4f}; "
              f"share of the gap that is comfort {(m[2] - m[0]) / gap:.1%}; "
              f"ours uses less energy+carbon in {int((v[:, 1] < v[:, 3]).sum())} of {len(v)}, "
              f"less comfort term in {int((v[:, 0] < v[:, 2]).sum())}")
    m = tot / n_all
    gap = (m[2] + m[3]) - (m[0] + m[1])
    print(f"ALL {n_all}: ours comfort {m[0]:.5f} energy+carbon {m[1]:.5f}; pid_water comfort {m[2]:.5f} energy+carbon "
          f"{m[3]:.5f}; energy ratio {m[1] / m[3]:.3f}; comfort ratio {m[0] / m[2]:.4f}; comfort share of the gap "
          f"{(m[2] - m[0]) / gap:.1%}; comfort share of pid_water's loss {m[2] / (m[2] + m[3]):.1%}")


if __name__ == "__main__":
    main()
