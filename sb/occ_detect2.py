"""Departure localisation with a fixed lag: zone error, heat, and both combined (sb/occ_dump.py traces)."""
import sys
import numpy as np
d = np.load(sys.argv[1])
T, q, occ, hour, err, g = d["T"], d["q"], d["occ"], d["hour"], d["err"], d["g"]
n, nz = T.shape
ev = [(k, z) for k in range(40, n - 40) for z in range(nz) if occ[k, z] < occ[k - 1, z] - 0.5 and 13 <= hour[k] < 19.5]
nerr = np.nanstd(np.diff(err[10:], axis=0), axis=0) / np.sqrt(2)
nq = np.nanstd(np.diff(q[10:], axis=0), axis=0) / np.sqrt(2)
print(sys.argv[1].split("/")[-1])
for lag in (2, 3):
    for m in (3, 6, 12, 24):
        hits = {"err": 0, "q": 0, "both": 0}
        tot = 0
        for k, z in ev:
            e = k + lag
            if e - m < 1 or e + m > n:
                continue
            cand = np.flatnonzero(occ[k - 1] > 0.5)
            s_err = np.nanmean(err[e:e + m], 0) - np.nanmean(err[e - m:e], 0)       # expect -0.07 g
            s_q = np.nanmean(q[e:e + m], 0) - np.nanmean(q[e - m:e], 0)             # expect +0.07 kW
            z_err = -s_err / (0.07 * g)          # in persons
            z_q = s_q / 0.07
            hits["err"] += cand[np.argmax(z_err[cand])] == z
            hits["q"] += cand[np.argmax(z_q[cand])] == z
            # combine with inverse noise weights (both in persons)
            w_e = 1.0 / (nerr / (0.07 * g)) ** 2
            w_q = 1.0 / (nq / 0.07) ** 2
            comb = (w_e * z_err + w_q * z_q) / (w_e + w_q)
            hits["both"] += cand[np.argmax(comb[cand])] == z
            tot += 1
        print(f"  lag {lag} m {m:2d}: first among occupied: err {hits['err']/tot:.0%}, q {hits['q']/tot:.0%}, "
              f"combined {hits['both']/tot:.0%}  (n={tot}, chance ~{np.mean([1/max((occ[k-1]>0.5).sum(),1) for k,_ in ev]):.0%})")
