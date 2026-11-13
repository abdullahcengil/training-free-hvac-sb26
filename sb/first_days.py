"""Loss of the first days of each episode against the same weekday later in the window (v15 full-length runs).

For each window: day d = steps 288*d .. 288*(d+1) from the 06:00 start. Day 0 is compared with days 7, 14, 21 (same
weekday, same time of day); day 1 with 8, 15, 22. Reports the excess of days 0 and 1 over their later twins, as a
share of the 30-day loss. Holiday weeks are excluded from the twins.
"""
import numpy as np
from pathlib import Path
import pandas as pd
from sb import run_holiday as rh

rows = []
for j in rh.full_jobs():
    f = Path(j["result"]).with_suffix(".npy")
    s = f.stem
    loss = -np.load(f).astype(float)[:, 0]
    t0 = rh.start(s)
    days = loss[: 30 * 288].reshape(30, 288).sum(1)
    hol = [((t0 + pd.Timedelta(days=d)).date() in rh.HOL) for d in range(30)]
    out = []
    for d in (0, 1, 2):
        twins = [days[d + 7 * k] for k in (1, 2, 3) if d + 7 * k < 30 and not hol[d + 7 * k]]
        out.append(days[d] - np.mean(twins))
    rows.append((s, loss.sum(), *out, t0.day_name()[:3]))
tot = sum(r[1] for r in rows)
for d in range(3):
    ex = sum(r[2 + d] for r in rows)
    print(f"day {d}: excess over its later same-weekday twins, summed over 70 windows: {ex:+.2f} ({100 * ex / tot:+.2f} % of the total loss {tot:.1f})")
w = sorted(rows, key=lambda r: -(r[2] + r[3]) / r[1])[:6]
for r in w:
    print(f"   {r[0]:40s} start {r[5]}  days 0-1 excess {100 * (r[2] + r[3]) / r[1]:+.2f} % of the window")
