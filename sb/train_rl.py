"""Trains the neural residual controller with PPO (docs/TRAINED_BASELINE.md). Three simulations at most.

Run on the corrected simulator, so that the policy cannot learn to use the simulator's hot-water accounting issue:

    PYTHONPATH=D:/SmartBuildings_data/kit_fixed python -m sb.train_rl --hours 34 --tag main >> D:/SmartBuildings_data/rl_main.log 2>&1

Restartable: --resume continues from the last state saved in results/rl/<tag>/. A file named STOP in that folder ends the
run cleanly at the next iteration.
"""

from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import csv
import gc
import json
import multiprocessing as mp
import pickle
import sys
import time
import traceback
from multiprocessing.connection import wait as conn_wait
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from sb.rl_core import Adam, Agent  # noqa: E402

ROOT = Path("D:/SmartBuildings_data/starter-kit/smart_buildings/training_scenarios").resolve()
OUT = Path("D:/SmartBuildings_data/results/rl")
VAL_BUILDING = "building_train_4"     # kept out of training; used only to choose the checkpoint
POLICY = f"{REPO / 'policies/trained_residual.py'}:TrainedResidualPolicy"
ZONE_DIM, AHU_DIM = 27, 27

CFG = dict(gamma=0.98, lam=0.95, rscale=5.0, rclip=10.0, vscale=10.0, every=3,
           zone=dict(mb=1024, epochs=4, clip=0.2, ent=5e-4, ls_min=-3.0, ls_max=-0.7, target_kl=0.02, vscale=10.0),
           ahu=dict(mb=256, epochs=4, clip=0.2, ent=5e-4, ls_min=-3.0, ls_max=-0.7, target_kl=0.02, vscale=10.0),
           hidden=(64, 64), lr0=1.5e-4, lr1=5e-5, z_ls0=-1.4, a_ls0=-1.2, max_ep=2880, ema=0.99)


def mlp_forward(params: list[np.ndarray], x: np.ndarray) -> np.ndarray:
    h = x
    for i in range(0, len(params) - 2, 2):
        h = np.tanh(h @ params[i] + params[i + 1])
    return h @ params[-2] + params[-1]


def scenarios(root: Path = ROOT) -> list[Path]:
    return sorted(p.parent for p in root.glob("*/*/config.gin"))


# ------------------------------------------------------------------- worker
class Sim:
    def __init__(self, wid: int, seed: int, train: list[str], cfg: dict) -> None:
        self.wid, self.train, self.cfg = wid, train, cfg
        self.rng = np.random.default_rng(seed)
        self.env = None
        self.pol = None

    def _open(self, scen: str, weights: dict | None, explore: bool) -> None:
        from smart_buildings import evaluate

        from sb.run import load_policy_class

        self.env = None
        self.pol = None
        gc.collect()
        scen_p = Path(scen)
        os.chdir(Path(evaluate.__file__).resolve().parents[1])
        env = evaluate.load_hybrid_environment(scen_p / "config.gin")
        env.metrics_path = None
        env._occupancy_normalization_constant = 125.0
        meta = evaluate.create_building_meta_data(env, scen_p)
        self.spec = env.action_spec()
        cls = load_policy_class(POLICY)
        self.pol = cls(meta, self.spec, weights=weights, decide_every=self.cfg["every"], explore=explore,
                       seed=int(self.rng.integers(1 << 31)))
        self.env = env
        self.scen = scen
        self.ep_steps = 0
        self.obs, _ = env.reset()
        self.ref = float(getattr(env.reward_function, "_productivity_deviation_ref", 5.0))

    def _local(self, cont: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Each zone's share of the building's loss in this step, scaled so that the mean over zones is the building's reward."""
        ri, rr = self.env.get_reward_info_and_response()
        p = self.pol
        n = p.nz
        occ, dev, flow = np.zeros(n), np.zeros(n), np.zeros(n)
        zm = ri.zone_reward_infos
        for i, room in enumerate(p.z_room):
            if room not in zm:
                continue
            z = zm[room]
            occ[i] = z.average_occupancy
            flow[i] = z.air_flow_rate
            dev[i] = max(0.0, z.zone_air_temperature - z.cooling_setpoint_temperature,
                         z.heating_setpoint_temperature - z.zone_air_temperature)
        w = self.ref
        short = np.where(dev <= w, dev / w, 1.0 + ((dev - w) / w) ** 2)
        reg = short * occ
        s = float(reg.sum())
        prod = (-rr.normalized_productivity_regret) * (reg / s) if s > 0 else np.zeros(n)
        en = 0.2 * rr.normalized_energy_cost + 0.2 * rr.normalized_carbon_emission
        g, e = rr.natural_gas_energy_cost, rr.electricity_energy_cost
        gf = g / (g + e) if g + e > 0 else 0.0
        fs = (flow + 1e-9) / (flow + 1e-9).sum()
        rh = np.where(p.z_reheat >= 0, (cont[np.maximum(p.z_reheat, 0)] + 1.0) / 2.0, 0.0)
        h = flow * np.maximum(rh, 0.0)
        hs = h / h.sum() if h.sum() > 0 else fs
        rz = -n * (0.6 * prod + en * (gf * hs + (1.0 - gf) * fs))
        ra = np.array([rz[m].mean() if len(m) else 0.0 for m in p.members])
        return rz, ra

    @staticmethod
    def _seg() -> dict:
        return {"d": [], "rz": [], "ra": []}

    def _close(self, seg: dict, w: dict) -> dict | None:
        c = self.cfg
        T = min(len(seg["d"]), len(seg["rz"]))
        if T == 0:
            return None
        xz_b, xa_b = self.pol.peek(self.obs)
        on = np.stack([d["on"] for d in seg["d"][:T]])
        out = {}
        for t, xk, ak, lk, rk, boot, vk, act in (
                ("zone", "xz", "az", "lpz", "rz", xz_b, "z_v", on[:, self.pol.z_ahu]),
                ("ahu", "xa", "aa", "lpa", "ra", xa_b, "a_v", on)):
            x = np.stack([d[xk] for d in seg["d"][:T]])
            a = np.stack([d[ak] for d in seg["d"][:T]])
            lp = np.stack([d[lk] for d in seg["d"][:T]])
            r = np.maximum(np.stack(seg[rk][:T]) * c["rscale"], -c["rclip"])
            n, dim = x.shape[1], x.shape[2]
            v = mlp_forward(w[vk], x.reshape(-1, dim)).reshape(T, n) * c["vscale"]
            vb = mlp_forward(w[vk], boot)[:, 0] * c["vscale"]
            adv = np.zeros_like(r)
            last = np.zeros(n)
            for k in range(T - 1, -1, -1):
                nv = v[k + 1] if k + 1 < T else vb
                delta = r[k] + c["gamma"] * nv - v[k]
                last = delta + c["gamma"] * c["lam"] * last
                adv[k] = last
            ret = adv + v
            out[t] = {"x": x.reshape(-1, dim).astype(np.float32), "a": a.reshape(-1, a.shape[2]).astype(np.float32),
                      "lp": lp.reshape(-1).astype(np.float32), "adv": adv.reshape(-1).astype(np.float32),
                      "ret": ret.reshape(-1).astype(np.float32), "active": act.reshape(-1)}
        return out

    def collect(self, w: dict, n: int) -> dict:
        from smart_buildings import evaluate

        if self.env is None:
            self._open(str(self.rng.choice(self.train)), w, True)
        self.pol.w = w
        every = self.cfg["every"]
        out, seg = [], self._seg()
        steps, loss = 0, 0.0
        acc_z, acc_a = None, None
        while steps < n or self.pol.k % every != 0:
            due = self.pol.k % every == 0
            act = self.pol.get_action(self.obs)
            if due:
                seg["d"].append(self.pol.last)
                acc_z, acc_a = np.zeros(self.pol.nz), np.zeros(self.pol.n_ahu)
            a = evaluate.validate_action(act, self.spec)
            self.obs, r, term, trunc, _ = self.env.step(a)
            rz, ra = self._local(np.asarray(a["continuous_action"], dtype=np.float64))
            acc_z += rz
            acc_a += ra
            loss -= float(r)
            steps += 1
            self.ep_steps += 1
            if self.pol.k % every == 0:
                seg["rz"].append(acc_z)
                seg["ra"].append(acc_a)
            if term or trunc or (self.ep_steps >= self.cfg.get("max_ep", 10 ** 9) and self.pol.k % every == 0):
                out.append(self._close(seg, w))
                self._open(str(self.rng.choice(self.train)), w, True)
                seg = self._seg()
        out.append(self._close(seg, w))
        out = [o for o in out if o is not None]
        res: dict = {}
        for t in ("zone", "ahu"):
            res[t] = {key: np.concatenate([o[t][key] for o in out], axis=0)
                      for key in ("x", "a", "lp", "adv", "ret", "active")}
        res["loss"] = loss / steps
        res["steps"] = steps
        res["scen"] = Path(self.scen).parent.name + "/" + Path(self.scen).name
        return res

    def evaluate(self, scen: str, w: dict | None, steps: int) -> dict:
        from smart_buildings import evaluate

        self._open(scen, w, False)
        total, comfort = 0.0, 0.0
        n = 0
        for _ in range(steps):
            a = evaluate.validate_action(self.pol.get_action(self.obs), self.spec)
            self.obs, r, term, trunc, _ = self.env.step(a)
            total -= float(r)
            _, rr = self.env.get_reward_info_and_response()
            comfort -= 0.6 * rr.normalized_productivity_regret
            n += 1
            if term or trunc:
                break
        self.env = None
        self.pol = None
        gc.collect()
        return {"scen": scen, "loss": total / n, "comfort": comfort / n}


def worker_main(conn, wid: int, seed: int, train: list[str], cfg: dict) -> None:
    sim = Sim(wid, seed, train, cfg)
    while True:
        try:
            msg = conn.recv()
        except EOFError:
            break
        cmd = msg["cmd"]
        if cmd == "stop":
            break
        try:
            if cmd == "collect":
                conn.send(sim.collect(msg["w"], msg["n"]))
            elif cmd == "eval":
                conn.send(sim.evaluate(msg["scen"], msg["w"], msg["steps"]))
        except Exception:
            sim.env = None
            sim.pol = None
            conn.send({"error": traceback.format_exc()})


# ------------------------------------------------------------------- pool
class Pool:
    def __init__(self, n: int, seed: int, train: list[str], cfg: dict) -> None:
        self.n, self.seed, self.train, self.cfg = n, seed, train, cfg
        self.ctx = mp.get_context("spawn")
        self.procs: list = [None] * n
        self.conns: list = [None] * n
        self.spawns = 0
        for i in range(n):
            self._spawn(i)

    def _spawn(self, i: int) -> None:
        if self.procs[i] is not None:
            try:
                self.procs[i].kill()
            except Exception:
                pass
        a, b = self.ctx.Pipe()
        self.spawns += 1
        p = self.ctx.Process(target=worker_main, args=(b, i, self.seed + 1000 * self.spawns + i, self.train, self.cfg),
                             daemon=True)
        p.start()
        b.close()
        self.procs[i], self.conns[i] = p, a

    def collect(self, w: dict, steps: int) -> list[dict]:
        for c in self.conns:
            c.send({"cmd": "collect", "w": w, "n": steps})
        out = []
        for i, c in enumerate(self.conns):
            try:
                r = c.recv()
            except (EOFError, ConnectionError, OSError):
                print(f"worker {i} died during collection; restarted", flush=True)
                self._spawn(i)
                continue
            if isinstance(r, dict) and "error" in r:
                print(f"worker {i} error:\n{r['error']}", flush=True)
                continue
            out.append(r)
        return out

    def map_eval(self, scens: list[str], w: dict | None, steps: int) -> list[dict]:
        todo = list(scens)
        results: list[dict] = []
        busy: dict = {}
        tries = {s: 0 for s in scens}
        for i in range(self.n):
            if todo:
                s = todo.pop(0)
                self.conns[i].send({"cmd": "eval", "scen": s, "w": w, "steps": steps})
                busy[self.conns[i]] = (i, s)
        while busy:
            for c in conn_wait(list(busy)):
                i, s = busy.pop(c)
                try:
                    r = c.recv()
                except (EOFError, ConnectionError, OSError):
                    print(f"worker {i} died during evaluation of {s}; restarted", flush=True)
                    self._spawn(i)
                    r = {"error": "died"}
                if "error" in r:
                    print(f"evaluation error on {s}: {r['error']}", flush=True)
                    tries[s] += 1
                    if tries[s] < 3:
                        todo.append(s)
                else:
                    results.append(r)
                if todo:
                    s2 = todo.pop(0)
                    self.conns[i].send({"cmd": "eval", "scen": s2, "w": w, "steps": steps})
                    busy[self.conns[i]] = (i, s2)
        return results

    def stop(self) -> None:
        for c in self.conns:
            try:
                c.send({"cmd": "stop"})
            except Exception:
                pass
        for p in self.procs:
            p.join(timeout=20)
            if p.is_alive():
                p.kill()


def weights_of(z: Agent, a: Agent, critics: bool = True) -> dict:
    w = {"z_mu": [p.copy() for p in z.mu.params], "z_ls": z.log_std.copy(),
         "a_mu": [p.copy() for p in a.mu.params], "a_ls": a.log_std.copy()}
    if critics:
        w["z_v"] = [p.copy() for p in z.vf.params]
        w["a_v"] = [p.copy() for p in a.vf.params]
    return w


def atomic_pickle(obj, path: Path) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(obj, f)
    os.replace(tmp, path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--hours", type=float, required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--nsteps", type=int, default=576)
    ap.add_argument("--val-every", type=int, default=150)
    ap.add_argument("--val-steps", type=int, default=2880)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--only", default=None, help="train on this building only (smoke tests)")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--actor-from", default=None, help="with --resume: take the actors from this checkpoint and reset their optimiser")
    a = ap.parse_args()
    if a.workers > 3:
        raise SystemExit("at most three simulations at a time")

    out = OUT / a.tag
    out.mkdir(parents=True, exist_ok=True)
    all_s = scenarios()
    train = [str(s) for s in all_s if s.parent.name != VAL_BUILDING]
    val = [str(s) for s in all_s if s.parent.name == VAL_BUILDING]
    if a.only:
        train = [s for s in train if a.only in s]
    print(f"{len(train)} training scenarios, {len(val)} validation scenarios ({VAL_BUILDING}); simulator "
          f"{__import__('smart_buildings.evaluate', fromlist=['x']).__file__}", flush=True)

    c = CFG
    rng = np.random.default_rng(a.seed)
    state_f = out / "state.pkl"
    if a.resume and state_f.exists():
        with open(state_f, "rb") as f:
            st = pickle.load(f)
        z, ah, it, env_steps, elapsed0, best = st["z"], st["a"], st["it"], st["env_steps"], st["elapsed"], st["best"]
        rng.bit_generator.state = st["rng"]
        if (out / "best.json").exists():
            best = min(best, json.loads((out / "best.json").read_text())["val_loss"])
        print(f"resumed at iteration {it}, {elapsed0 / 3600:.2f} h used", flush=True)
        if a.actor_from:
            with open(a.actor_from, "rb") as f:
                ck = pickle.load(f)
            for ag, mu, ls in ((z, ck["z_mu"], ck["z_ls"]), (ah, ck["a_mu"], ck["a_ls"])):
                for p, q in zip(ag.mu.params, mu):
                    p[:] = q
                ag.log_std[:] = ls
                ag.opt_a = Adam(ag.mu.params + [ag.log_std])
            print(f"actors taken from {a.actor_from}", flush=True)
    else:
        z = Agent(ZONE_DIM, 2, c["hidden"], c["z_ls0"], rng)
        ah = Agent(AHU_DIM, 3, c["hidden"], c["a_ls0"], rng)
        it, env_steps, elapsed0, best = 0, 0, 0.0, float("inf")
        (out / "config.json").write_text(json.dumps({"cfg": c, "args": vars(a), "train": train, "val": val}, indent=1))

    pool = Pool(a.workers, a.seed, train, c)
    tlog = out / "train.csv"
    vlog = out / "val.csv"
    if not tlog.exists():
        with open(tlog, "w", newline="") as f:
            csv.writer(f).writerow(["it", "hours", "env_steps", "loss", "z_kl", "a_kl", "z_v", "a_v", "z_sigma", "a_sigma",
                                    "z_active", "lr", "scen"])
    t0 = time.time()

    ema = weights_of(z, ah, critics=False)

    def update_ema() -> None:
        t = c.get("ema", 0.0)
        for key, ag in (("z", z), ("a", ah)):
            for e, p in zip(ema[f"{key}_mu"], ag.mu.params):
                e[:] = t * e + (1.0 - t) * p
            ema[f"{key}_ls"] = ag.log_std.copy()

    def validate(label: int) -> float:
        w = {k: ([x.copy() for x in v] if isinstance(v, list) else v.copy()) for k, v in ema.items()}
        r = pool.map_eval(val, w, a.val_steps)
        m = float(np.mean([x["loss"] for x in r]))
        cf = float(np.mean([x["comfort"] for x in r]))
        new = not vlog.exists()
        with open(vlog, "a", newline="") as f:
            wr = csv.writer(f)
            if new:
                wr.writerow(["it", "hours", "env_steps", "val_loss", "val_comfort", "n"])
            wr.writerow([label, round((elapsed0 + time.time() - t0) / 3600, 3), env_steps, round(m, 6), round(cf, 6), len(r)])
        atomic_pickle(w, out / f"ckpt_{label:05d}.pkl")
        return m

    base_f = out / "val_baseline.json"
    if not base_f.exists():
        r = pool.map_eval(val, None, a.val_steps)
        base_f.write_text(json.dumps(r, indent=1))
        print(f"validation, pid_water on the corrected simulator: {np.mean([x['loss'] for x in r]):.5f}", flush=True)

    if it == 0:
        m = validate(0)
        print(f"validation at start: {m:.5f}", flush=True)

    while True:
        elapsed = elapsed0 + time.time() - t0
        if elapsed > a.hours * 3600 or (out / "STOP").exists():
            break
        frac = min(1.0, elapsed / (a.hours * 3600))
        lr = c["lr0"] + (c["lr1"] - c["lr0"]) * frac
        w = weights_of(z, ah)
        res = pool.collect(w, a.nsteps)
        if not res:
            continue
        zb = {k: np.concatenate([r["zone"][k] for r in res], axis=0).astype(np.float64 if k != "active" else bool)
              for k in ("x", "a", "lp", "adv", "ret", "active")}
        ab = {k: np.concatenate([r["ahu"][k] for r in res], axis=0).astype(np.float64 if k != "active" else bool)
              for k in ("x", "a", "lp", "adv", "ret", "active")}
        oz = z.update(zb, c["zone"], lr, rng)
        oa = ah.update(ab, c["ahu"], lr, rng)
        update_ema()
        it += 1
        env_steps += sum(r["steps"] for r in res)
        loss = float(np.mean([r["loss"] for r in res]))
        with open(tlog, "a", newline="") as f:
            csv.writer(f).writerow([it, round((elapsed0 + time.time() - t0) / 3600, 3), env_steps, round(loss, 6),
                                    round(oz["kl"], 5), round(oa["kl"], 5), round(oz["v_loss"], 4), round(oa["v_loss"], 4),
                                    round(float(np.exp(z.log_std).mean()), 4), round(float(np.exp(ah.log_std).mean()), 4),
                                    oz["n_active"], f"{lr:.2e}", ";".join(r["scen"] for r in res)])
        if it % 10 == 0:
            print(f"it {it} {(elapsed0 + time.time() - t0) / 3600:.2f} h steps {env_steps} loss {loss:.5f} "
                  f"kl {oz['kl']:.4f}/{oa['kl']:.4f} sigma {np.exp(z.log_std).mean():.3f}/{np.exp(ah.log_std).mean():.3f}",
                  flush=True)
        if it % a.val_every == 0:
            m = validate(it)
            if m < best:
                best = m
                atomic_pickle(ema, out / "best.pkl")
                (out / "best.json").write_text(json.dumps({"it": it, "val_loss": m}))
            print(f"validation at it {it}: {m:.5f} (best {best:.5f})", flush=True)
        if it % 20 == 0:
            atomic_pickle({"z": z, "a": ah, "it": it, "env_steps": env_steps, "elapsed": elapsed0 + time.time() - t0,
                           "best": best, "rng": rng.bit_generator.state}, state_f)

    atomic_pickle({"z": z, "a": ah, "it": it, "env_steps": env_steps, "elapsed": elapsed0 + time.time() - t0, "best": best,
                   "rng": rng.bit_generator.state}, state_f)
    m = validate(it)
    if m < best:
        best = m
        atomic_pickle(ema, out / "best.pkl")
        (out / "best.json").write_text(json.dumps({"it": it, "val_loss": m}))
    print(f"finished at iteration {it}, {env_steps} simulator steps; last validation {m:.5f}, best {best:.5f}", flush=True)
    pool.stop()


if __name__ == "__main__":
    main()
