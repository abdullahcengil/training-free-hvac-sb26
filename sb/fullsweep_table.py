"""LaTeX rows for the full-size sensitivity of v14 (docs/FULLSWEEP.md): change of the mean loss over the four
scenarios and per scenario, against v14, for every finished variant.

    python -m sb.fullsweep_table
"""

from __future__ import annotations

import numpy as np

from sb.run_fullsweep import FOUR, OUT, REF, V14, VARS, loss

SHORT = {"building_7001__dubai_jul15": "Dubai", "building_7005__lasvegas_jul15": "Las Vegas",
         "building_7001__chicago_jan15": "Chicago", "building_7007__newyork_jan15": "New York"}
NAMES = {"f_heat_max": "heating airflow cap", "glide_safety": "setback rate factor", "damping": "damping",
         "cool_safety": "pull-down rate factor", "margin_heat": "heating margin (K)"}


def main() -> None:
    ref = np.array([loss(REF, s) for s in FOUR])
    print("% " + " & ".join(SHORT[s] for s in FOUR) + f" (v14: {' '.join(f'{x:.5f}' for x in ref)})")
    for v, change in VARS.items():
        (k, val), = change.items()
        got = [loss(OUT / v, s) for s in FOUR]
        if any(g is None for g in got):
            continue
        b = np.array(got)
        per = " & ".join(f"{100 * (y / x - 1):+.1f}" for x, y in zip(ref, b))
        print(f"{NAMES.get(k, k)} & {V14[k]:g} $\\to$ {val:g} & {100 * (b.mean() / ref.mean() - 1):+.2f} & {per} \\\\")


if __name__ == "__main__":
    main()
