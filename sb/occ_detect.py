"""Can a departure be seen in the zone model's error? Offline test on sb/occ_dump.py traces.

For every step at which someone left a zone (true occupancy from the reward), compare the mean one-step model
error of every zone over m steps after the step with its mean over m steps before; the zone that lost 70 W
should show the most negative change. Reports the lag at which occupancy enters the error, the size of one
person in K per step, the error's noise, and how often the true zone ranks first among the zones that were
occupied (the detector would also know, from the building total, how many people left in that step).

    python -m sb.occ_detect D:/SmartBuildings_data/results/occdump/b8_fairbanks_8.npz
"""

from __future__ import annotations

import sys

import numpy as np


def main(path: str) -> None:
    d = np.load(path)
    err, occ, hour = d["err"], d["occ"], d["hour"]
    n, nz = err.shape
    ok = np.all(np.isfinite(err), axis=1)
    print(f"{path}: {n} steps, {nz} zones, people max {np.nanmax(occ.sum(1)):.0f}")
    # Lag: err[k] against occ[k - L], zone by zone after removing each zone's mean.
    best = None
    for lag in range(-1, 4):
        # err[k] paired with occ[k - lag]
        a, b = (err[5 + lag:], occ[5:n - lag]) if lag >= 0 else (err[5:n + lag], occ[5 - lag:])
        m = np.all(np.isfinite(a), axis=1)
        a, b = a[m] - a[m].mean(0), b[m] - b[m].mean(0)
        coef = float((a * b).sum() / max((b * b).sum(), 1e-9))
        print(f"  lag {lag}: error per person {coef * 1000:+.2f} mK/step")
        if best is None or coef > best[1]:
            best = (lag, coef)
    lag, per = best
    noise = np.nanstd(np.diff(err[ok], axis=0), axis=0) / np.sqrt(2)
    print(f"  best lag {lag}: one person = {per * 1000:.1f} mK/step; step-to-step noise of the error: median "
          f"{np.median(noise) * 1000:.1f} mK/step (zones {np.percentile(noise, 10) * 1000:.1f}-"
          f"{np.percentile(noise, 90) * 1000:.1f}); median model gain g {np.median(d['g']):.3f} K/kW/step")
    # Departure events: occupancy of a zone falls between step k-1 and step k (afternoon).
    ev = [(k, z) for k in range(30, n - 30) for z in range(nz)
          if occ[k, z] < occ[k - 1, z] - 0.5 and 13.0 <= hour[k] < 19.5]
    print(f"  {len(ev)} afternoon departures")
    # Expected drop per zone if one person leaves: 70 W through the zone's own identified gain.
    delta = 0.07 * np.clip(d["g"], 0.02, None)
    for m in (3, 6, 12, 24):
        hits_occ, hits_all, hits_llr, ranks = 0, 0, 0, []
        for k, z in ev:
            e = k + lag                               # first error without the person (err[j] ~ occ[j - lag])
            if e - m < 1 or e + m > n:
                continue
            after = np.nanmean(err[e:e + m], axis=0)
            before = np.nanmean(err[e - m:e], axis=0)
            s = after - before
            cand = np.flatnonzero(occ[k - 1] > 0.5)
            order = cand[np.argsort(s[cand])]
            r = int(np.flatnonzero(order == z)[0]) if z in order else len(cand)
            ranks.append(r / max(len(cand) - 1, 1))
            hits_occ += r == 0
            hits_all += int(np.argmin(s)) == z
            # Log-likelihood ratio of "this zone lost delta" against "no change", with each zone's own noise.
            var = 2.0 * noise ** 2 / m
            llr = (-s * delta - 0.5 * delta ** 2) / var
            hits_llr += int(cand[np.argmax(llr[cand])]) == z
        tot = len(ranks)
        print(f"  m={m:2d}: true zone first among occupied {hits_occ}/{tot} ({hits_occ / max(tot, 1):.0%}), "
              f"by likelihood ratio {hits_llr / max(tot, 1):.0%}, among all {hits_all / max(tot, 1):.0%}; "
              f"mean relative rank {np.mean(ranks):.2f} (0 best, 0.5 chance)")


if __name__ == "__main__":
    main(sys.argv[1])
