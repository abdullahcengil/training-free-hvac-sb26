"""Recompute Table 1 of the paper (training and blind-round columns) from the result files and compare with the
numbers printed in paper/main.tex. Reads JSON summaries only; runs no simulation.

    python -m sb.check_table1
"""

from __future__ import annotations

import re
from pathlib import Path

from sb.evaluate_prereg import load, score

R = Path("D:/SmartBuildings_data/results")
REPO = Path(__file__).resolve().parents[1]
STRESS = ("_jan15", "_jul15")

# version: (training folder, blind-round folder, ours, previous, baseline)
ROWS = {
    "v7": ("train_8640/zonal", "heldout", "zonal", None, "pid_water"),
    "v8": ("train_8640/v8", "heldout2", "v8", "v7", "pid_water"),
    "v9": ("train_8640/v9f", "heldout3", "v9", "v8", "pid_water"),
    "v10": ("train_8640/v10c", "heldout4", "v10", "v9", "pid_water"),
    "v11": ("dev11_8640/v11f", "heldout5", "v11", "v10", "pid_water"),
    "v12": ("dev12_8640/v12_all30", None, None, None, None),
    "v13": ("dev13_8640/v13_all30", None, None, None, None),
    "v14": ("dev14_8640/of3", None, None, None, None),
    "v15": ("holiday/ed1_full", "round6h", "ed1", "v14", "pid_water"),
    "v16": ("chatter/t_chm", "round7", "chm", "v15", "pid_water"),
}


def training(folder: str) -> tuple[float, int]:
    runs = {k: v for k, v in load(R / folder).items() if not k.endswith(STRESS)}
    return score(runs), len(runs)


def paper_rows() -> dict[str, list[str]]:
    tex = (REPO / "paper/main.tex").read_text(encoding="utf-8")
    body = tex[tex.index(r"\label{tab:main}"):tex.index(r"\end{tabular}", tex.index(r"\label{tab:main}"))]
    out = {}
    for line in body.splitlines():
        m = re.match(r"(v\d+|pid\\_water) &", line.strip())
        if m:
            cells = [c.strip().rstrip("\\").strip() for c in line.split("&")]
            out[m.group(1).replace("\\_", "_")] = cells
    return out


def main() -> None:
    printed = paper_rows()
    bad = 0
    for v, (tr, rnd, ours, prev, base) in ROWS.items():
        cells = printed[v]
        t, n = training(tr)
        checks = [("training", t, cells[2], n)]
        if rnd:
            for label, name, col in (("blind", ours, 4), ("previous", prev, 5), ("pid_water", base, 6)):
                if name:
                    runs = load(R / rnd / name)
                    checks.append((label, score(runs), cells[col], len(runs)))
        for label, value, shown, n in checks:
            ok = shown not in ("", "--") and abs(value - float(shown)) < 0.6e-5
            bad += not ok
            print(f"{v:4s} {label:9s} computed {value:.6f} over {n:2d} scenarios, paper {shown:8s} {'ok' if ok else 'MISMATCH'}")
    print("all Table 1 numbers match" if not bad else f"{bad} mismatches")


if __name__ == "__main__":
    main()
