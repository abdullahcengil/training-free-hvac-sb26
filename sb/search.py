"""CMA-ES parameter search on shortened training episodes (round-4 development).

Every candidate is run on the same training scenarios for the first STEPS
steps; the objective is the leaderboard metric, the mean |reward| per step
over the scenarios. Every candidate that was run is appended to
<out>/log.jsonl, so nothing is left out of the development log.

    python -m sb.search --out D:/SmartBuildings_data/results/search/s1 \
        --base '{"safety_pred": 2, ...}' --space s1 --steps 2016 --gens 10 --popsize 8

The CMA-ES is the standard (mu/mu_w, lambda) algorithm with rank-one and
rank-mu updates (Hansen, "The CMA Evolution Strategy: A Tutorial", 2016),
written out here so no package has to be downloaded. It works in [0, 1]^n,
mapped linearly to each parameter's range; samples outside are clipped.
"""

from __future__ import annotations

import os as _os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")

import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path

import numpy as np

from sb.run import _absolute_spec, run_job

SC_ROOT = Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios")

# name: (low, high). Start point: the base parameters (v9), else the policy default.
SPACES = {
    "s1": {
        "margin_heat": (0.1, 1.0),
        "margin_cool": (0.1, 1.0),
        "aim_inside": (0.0, 0.6),
        "damping": (0.4, 1.0),
        "lead_h": (0.5, 3.0),
        "guard": (-1.0, 2.0),
        "sat_econ_max": (289.0, 297.0),
        "f_heat_max": (0.1, 0.4),
        "glide_floor": (-8.0, 0.0),
        "glide_safety": (0.4, 1.0),
        "f_heat_rec": (0.2, 0.6),
        "cool_ceiling": (0.0, 8.0),
        "cool_safety": (0.4, 1.0),
        "cool_rec_frac": (0.3, 1.0),
    },
    # After screens 1-4: cooling glide on with the free-cooling test; cool_rec_frac
    # dropped (the rate bound binds), the rate bound, the free margin and a
    # seasonal gate added.
    "s2": {
        "margin_heat": (0.1, 1.0),
        "margin_cool": (0.1, 1.0),
        "aim_inside": (0.0, 0.6),
        "damping": (0.4, 1.0),
        "f_heat_max": (0.1, 0.4),
        "f_heat_rec": (0.2, 0.6),
        "glide_floor": (-8.0, 0.0),
        "glide_safety": (0.4, 1.0),
        "cool_ceiling": (2.0, 10.0),
        "cool_safety": (0.4, 1.0),
        "cool_rate_max": (0.5, 4.0),
        "cool_free_dt": (0.0, 3.0),
        "cool_glide_oat": (283.0, 300.0),
        "sat_econ_max": (290.0, 297.0),
    },
}


def _defaults(path: str) -> dict:
    import importlib.util

    spec = importlib.util.spec_from_file_location("zonal_defaults", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(mod._DEFAULTS)


class CMA:
    def __init__(self, x0: np.ndarray, sigma: float, popsize: int, seed: int) -> None:
        n = len(x0)
        self.n, self.lam = n, popsize
        self.mu = popsize // 2
        w = np.log(self.mu + 0.5) - np.log(np.arange(1, self.mu + 1))
        self.w = w / w.sum()
        self.mueff = 1.0 / np.sum(self.w ** 2)
        self.cc = (4 + self.mueff / n) / (n + 4 + 2 * self.mueff / n)
        self.cs = (self.mueff + 2) / (n + self.mueff + 5)
        self.c1 = 2 / ((n + 1.3) ** 2 + self.mueff)
        self.cmu = min(1 - self.c1, 2 * (self.mueff - 2 + 1 / self.mueff) / ((n + 2) ** 2 + self.mueff))
        self.damps = 1 + 2 * max(0.0, np.sqrt((self.mueff - 1) / (n + 1)) - 1) + self.cs
        self.chin = np.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n))
        self.m, self.sigma = x0.astype(float).copy(), sigma
        self.pc, self.ps = np.zeros(n), np.zeros(n)
        self.C = np.eye(n)
        self.gen = 0
        self.rng = np.random.default_rng(seed)

    def ask(self) -> list[np.ndarray]:
        self.D2, self.B = np.linalg.eigh(self.C)
        self.D = np.sqrt(np.maximum(self.D2, 1e-20))
        self.z = self.rng.standard_normal((self.lam, self.n))
        self.y = self.z @ (self.B * self.D).T
        return [self.m + self.sigma * yi for yi in self.y]

    def tell(self, f: list[float]) -> None:
        idx = np.argsort(f)[: self.mu]
        y_w = self.w @ self.y[idx]
        self.m = self.m + self.sigma * y_w
        c_inv_half = self.B @ np.diag(1 / self.D) @ self.B.T
        self.ps = (1 - self.cs) * self.ps + np.sqrt(self.cs * (2 - self.cs) * self.mueff) * c_inv_half @ y_w
        self.gen += 1
        hsig = np.linalg.norm(self.ps) / np.sqrt(1 - (1 - self.cs) ** (2 * self.gen)) / self.chin < 1.4 + 2 / (self.n + 1)
        self.pc = (1 - self.cc) * self.pc + hsig * np.sqrt(self.cc * (2 - self.cc) * self.mueff) * y_w
        rank_mu = (self.y[idx].T * self.w) @ self.y[idx]
        self.C = ((1 - self.c1 - self.cmu) * self.C
                  + self.c1 * (np.outer(self.pc, self.pc) + (1 - hsig) * self.cc * (2 - self.cc) * self.C)
                  + self.cmu * rank_mu)
        self.sigma *= np.exp((self.cs / self.damps) * (np.linalg.norm(self.ps) / self.chin - 1))


def evaluate(pool, spec: str, cands: list[dict], scenarios: list[str], steps: int, out: Path,
             tags: list[str]) -> list[dict]:
    jobs, owner = [], []
    for ci, (kw, tag) in enumerate(zip(cands, tags)):
        for s in scenarios:
            jobs.append((spec, str(SC_ROOT / s), str(out / tag), steps, True, kw))
            owner.append(ci)
    res = [[] for _ in cands]
    for i, r in enumerate(pool.imap(run_job, jobs)):
        res[owner[i]].append(r)
    rows = []
    for kw, tag, rs in zip(cands, tags, res):
        per = {f"{r['building']}/{r['weather']}": abs(r["total_reward"]) / r["steps"] for r in rs}
        comfort = float(np.mean([abs(r["components"]["prod"]) / r["steps"] for r in rs])) * 0.6
        rows.append(dict(tag=tag, kwargs=kw, score=float(np.mean(list(per.values()))),
                         comfort=comfort, per=per))
    return rows


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--policy", required=True, help="snapshot file:Class (never the working copy)")
    ap.add_argument("--base", required=True, help="JSON parameters every candidate starts from")
    ap.add_argument("--fixed", default="{}", help="JSON parameters added to every candidate, not searched")
    ap.add_argument("--space", default="s1")
    ap.add_argument("--scenarios", nargs="+", required=True)
    ap.add_argument("--steps", type=int, default=2016)
    ap.add_argument("--gens", type=int, default=10)
    ap.add_argument("--popsize", type=int, default=8)
    ap.add_argument("--sigma", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    space = SPACES[a.space]
    names = list(space)
    lo = np.array([space[k][0] for k in names])
    hi = np.array([space[k][1] for k in names])
    base = json.loads(a.base)
    fixed = json.loads(a.fixed)
    spec = _absolute_spec(a.policy)
    dflt = _defaults(spec.rsplit(":", 1)[0])
    start = np.array([float(base.get(k, dflt[k])) for k in names])
    x0 = np.clip((start - lo) / (hi - lo), 0, 1)

    def to_kw(x):
        v = lo + np.clip(x, 0, 1) * (hi - lo)
        kw = dict(base)
        kw.update({k: round(float(vi), 4) for k, vi in zip(names, v)})
        kw.update(fixed)
        return kw

    log = out / "log.jsonl"
    cma = CMA(x0, a.sigma, a.popsize, a.seed)
    t0 = time.time()
    with mp.get_context("spawn").Pool(a.workers) as pool:
        ref = evaluate(pool, spec, [dict(base, **fixed)], a.scenarios, a.steps, out, ["base"])[0]
        with log.open("a") as fh:
            fh.write(json.dumps(dict(gen=-1, **ref)) + "\n")
        print(f"base {ref['score']:.5f}", flush=True)
        best = ref
        for g in range(a.gens):
            xs = cma.ask()
            cands = [to_kw(x) for x in xs]
            tags = [f"g{g:02d}_{i}" for i in range(len(xs))]
            rows = evaluate(pool, spec, cands, a.scenarios, a.steps, out, tags)
            with log.open("a") as fh:
                for r in rows:
                    fh.write(json.dumps(dict(gen=g, **r)) + "\n")
            cma.tell([r["score"] for r in rows])
            gbest = min(rows, key=lambda r: r["score"])
            if gbest["score"] < best["score"]:
                best = gbest
            mean_kw = to_kw(cma.m)
            print(f"gen {g}: best {gbest['score']:.5f} (overall {best['score']:.5f}, base {ref['score']:.5f}) "
                  f"sigma {cma.sigma:.3f} {time.time() - t0:.0f}s", flush=True)
            (out / "state.json").write_text(json.dumps(dict(gen=g, best=best, mean=mean_kw, sigma=cma.sigma), indent=1))
    print("SEARCH DONE", json.dumps(best["kwargs"]))


if __name__ == "__main__":
    main()
