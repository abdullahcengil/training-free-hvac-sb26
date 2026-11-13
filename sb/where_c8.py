"""Where does the tuned line (c8 = c7fhm30) gain energy and lose comfort against v16? Read-only analysis of stored runs.

    python -m sb.where_c8 [cand]      (default c8; any folder under results/tuned)

Per window: loss split into comfort (productivity weight x regret) and energy+carbon, by day type and hour block.
Day types: first work day after a weekend or holiday ("Monday"), other work days, weekend/holiday.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sb.run_tuned import R, sets

W_PROD = 0.6


def start_of(root: Path, s: str) -> pd.Timestamp:
    b, w = s.split("__")
    txt = (root / b / w / "config.gin").read_text(encoding="utf-8")
    m = re.search(r"start_timestamp\s*=\s*'([^']+)'", txt)
    return pd.Timestamp(m.group(1))


def main() -> None:
    cand = sys.argv[1] if len(sys.argv) > 1 else "c8"
    from smart_buildings.smart_control.utils import conversion_utils as cu  # noqa: F401 (holiday calendar)
    try:
        from smart_buildings.smart_control.utils.conversion_utils import is_work_day
    except Exception:  # pragma: no cover
        is_work_day = lambda t: t.weekday() < 5
    rows = []
    for name, root, ss, refs in sets(False):
        for s in ss:
            fc = R / "tuned" / cand / name / f"{s}.npy"
            fv = refs[s] / f"{s}.npy"
            if not (fc.exists() and fv.exists()):
                continue
            c = np.load(fc).astype(float)[:2880]
            v = np.load(fv).astype(float)[:2880]
            n = min(len(c), len(v))
            t0 = start_of(root, s)
            ts = pd.date_range(t0, periods=n, freq="5min")
            work = np.array([bool(is_work_day(t)) for t in ts])
            day = ts.normalize()
            prev_work = {}
            # first work day after a non-work day
            days = sorted(set(day))
            first = set()
            start_day = days[0]
            for i, d in enumerate(days):
                wd = bool(is_work_day(d))
                if wd and (i == 0 or not bool(is_work_day(days[i - 1]))):
                    first.add(d)
            dtype = np.where(~work, "off", np.where(day == start_day, "start", np.where(day.isin(list(first)), "mon", "work")))
            hour = ts.hour.values
            blk = np.select([hour < 3, hour < 6, hour < 8, hour < 19], ["00-03", "03-06", "06-08", "08-19"], "19-24")
            for arr, pol in ((c, cand), (v, "v16")):
                comfort = -W_PROD * arr[:n, 1]
                total = -arr[:n, 0]
                for dt in ("start", "mon", "work", "off"):
                    for b in ("00-03", "03-06", "06-08", "08-19", "19-24"):
                        m = (dtype == dt) & (blk == b)
                        rows.append(dict(win=f"{name}/{s}", pol=pol, dtype=dt, blk=b,
                                         comfort=comfort[m].sum() / n, energy=(total[m] - comfort[m]).sum() / n))
    df = pd.DataFrame(rows)
    if df.empty:
        print("no data")
        return
    nwin = df.win.nunique()
    g = df.groupby(["pol", "dtype", "blk"])[["comfort", "energy"]].sum() / nwin
    piv = g.unstack("pol")
    piv[("d", "comfort")] = piv[("comfort", cand)] - piv[("comfort", "v16")]
    piv[("d", "energy")] = piv[("energy", cand)] - piv[("energy", "v16")]
    tot_v = (g.xs("v16", level="pol").sum()).sum()
    print(f"{nwin} windows; v16 mean loss {tot_v:.5f}; {cand} - v16 by day type and hour block (mean loss per step):")
    print((piv * 1e5).round(1).to_string())
    print("totals x1e5:", (g.groupby("pol").sum() * 1e5).round(1).to_string())


if __name__ == "__main__":
    main()
