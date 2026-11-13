"""Read the size-gate diagnostic traces (docs/SIZEGATE.md): per building, after each day, the median over zones of the
identified mass-model gain g (K per kW per step), envelope term b (per step) and conductance b/g (kW per K), the
share of zones at the gain's lower bound, and the rank correlation of 1/g and b/g with the true room area (which the
controller never sees).

    python -m sb.sizegate_read [D:/SmartBuildings_data/results/sizegate/*.npz]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

DIR = Path("D:/SmartBuildings_data/results/sizegate")
G_MIN = 0.05   # m2_lo of the gain in frozen/zonal_v14f.py


def _rank_corr(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 4:
        return float("nan")
    ra = np.argsort(np.argsort(a[ok])).astype(float)
    rb = np.argsort(np.argsort(b[ok])).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def read(path: Path) -> list[dict]:
    d = np.load(path)
    th = d["p_theta2"]                       # steps x zones x 5: [-lam, g, c, b, c_cm]
    area = d["area"] * float(d["cv_m"]) ** 2  # m2
    tag, b, w = path.stem.split("__")
    rows = []
    for day in (1, 2, 3):
        k = min(day * 288, th.shape[0]) - 1
        g, env = th[k, :, 1], th[k, :, 3]
        ua = env / g
        rows.append(dict(tag=tag, building=b.replace("building_", ""), weather=w, day=day, zones=th.shape[1],
                         area_med=float(np.nanmedian(area)), area_tot=float(np.nansum(area)),
                         g_med=float(np.median(g)), inv_g_med=float(np.median(1 / g)), b_med=float(np.median(env)),
                         ua_med=float(np.median(ua)), ua_sum=float(np.sum(ua)), at_gmin=float(np.mean(g <= G_MIN + 1e-9)),
                         r_area_invg=_rank_corr(area, 1 / g), r_area_ua=_rank_corr(area, ua)))
    return rows


def trajectory(files: list[Path]) -> None:
    """Median 1/g over zones every half day, and the share of zones at the gain's lower bound at the end."""
    marks = list(range(143, 864, 144))
    print("median 1/g at day " + " ".join(f"{(k + 1) / 288:.1f}" for k in marks) + " | zones at g bound (end)")
    for f in files:
        d = np.load(f)
        inv_g = 1.0 / d["p_theta2"][:, :, 1]
        n = inv_g.shape[0]
        med = [np.median(inv_g[min(k, n - 1)]) for k in marks]
        at = float(np.mean(d["p_theta2"][n - 1, :, 1] <= G_MIN + 1e-9))
        print(f"{f.stem:44s} " + " ".join(f"{m:5.2f}" for m in med) + f" | {at:.2f}")


def main(paths: list[str]) -> None:
    if paths and paths[0] == "--traj":
        trajectory([Path(p) for p in paths[1:]] or sorted(DIR.glob("*.npz")))
        return
    files = [Path(p) for p in paths] or sorted(DIR.glob("*.npz"))
    rows = [r for f in files for r in read(f)]
    head = ("tag", "building", "day", "zones", "area_med", "area_tot", "g_med", "inv_g_med", "b_med", "ua_med",
            "ua_sum", "at_gmin", "r_area_invg", "r_area_ua")
    print(" ".join(f"{h:>11}" for h in head))
    for r in sorted(rows, key=lambda r: (r["day"], r["tag"], r["building"])):
        print(" ".join(f"{r[h]:>11.4g}" if isinstance(r[h], float) else f"{r[h]:>11}" for h in head))


if __name__ == "__main__":
    main(sys.argv[1:])
