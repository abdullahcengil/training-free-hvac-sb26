"""A small PPO in numpy for the comparison with a trained policy (docs/TRAINED_BASELINE.md).

Numpy only, so nothing has to be installed. The networks are small (two hidden layers), so hand-written backprop is enough
and fast on one CPU thread.

    python -m sb.rl_core      # checks every gradient against finite differences
"""

from __future__ import annotations

import numpy as np

LOG2PI = float(np.log(2.0 * np.pi))


def _orth(shape: tuple[int, int], gain: float, rng: np.random.Generator) -> np.ndarray:
    a = rng.standard_normal(shape)
    u, _, vt = np.linalg.svd(a, full_matrices=False)
    q = u if u.shape == shape else vt
    return gain * q


class MLP:
    """Fully connected net: tanh between layers, linear output. `params` is a flat list [W0, c0, W1, c1, ...]."""

    def __init__(self, sizes: list[int], rng: np.random.Generator, last_gain: float = 0.01) -> None:
        self.params: list[np.ndarray] = []
        n = len(sizes) - 1
        for i, (a, b) in enumerate(zip(sizes[:-1], sizes[1:])):
            self.params.append(_orth((a, b), last_gain if i == n - 1 else float(np.sqrt(2.0)), rng))
            self.params.append(np.zeros(b))

    def forward(self, x: np.ndarray, keep: bool = False):
        h = x
        cache = []
        n = len(self.params) // 2
        for i in range(n):
            y = h @ self.params[2 * i] + self.params[2 * i + 1]
            if keep:
                cache.append((h, y))
            h = np.tanh(y) if i < n - 1 else y
        return (h, cache) if keep else h

    def backward(self, cache: list, dout: np.ndarray) -> list[np.ndarray]:
        """Gradient of the loss given d(loss)/d(output) per sample (already including any 1/N)."""
        n = len(self.params) // 2
        grads: list[np.ndarray] = [np.empty(0)] * (2 * n)
        g = dout
        for i in range(n - 1, -1, -1):
            inp, y = cache[i]
            if i < n - 1:
                t = np.tanh(y)
                g = g * (1.0 - t * t)
            grads[2 * i] = inp.T @ g
            grads[2 * i + 1] = g.sum(axis=0)
            g = g @ self.params[2 * i].T
        return grads


class Adam:
    def __init__(self, params: list[np.ndarray], eps: float = 1e-5) -> None:
        self.p = params
        self.m = [np.zeros_like(x) for x in params]
        self.v = [np.zeros_like(x) for x in params]
        self.t = 0
        self.eps = eps

    def step(self, grads: list[np.ndarray], lr: float, max_norm: float = 0.5) -> float:
        norm = float(np.sqrt(sum(float((g * g).sum()) for g in grads)))
        f = min(1.0, max_norm / (norm + 1e-12))
        self.t += 1
        b1, b2 = 0.9, 0.999
        for i, (p, g0) in enumerate(zip(self.p, grads)):
            g = g0 * f
            self.m[i] = b1 * self.m[i] + (1 - b1) * g
            self.v[i] = b2 * self.v[i] + (1 - b2) * g * g
            mh = self.m[i] / (1 - b1 ** self.t)
            vh = self.v[i] / (1 - b2 ** self.t)
            p -= lr * mh / (np.sqrt(vh) + self.eps)
        return norm


class Agent:
    """An actor (Gaussian, state-independent log-std) and a critic for one type of agent (zone or air handler)."""

    def __init__(self, n_in: int, n_act: int, hidden: tuple[int, ...], log_std0: float, rng: np.random.Generator) -> None:
        self.mu = MLP([n_in, *hidden, n_act], rng, last_gain=0.01)
        self.vf = MLP([n_in, *hidden, 1], rng, last_gain=1.0)
        self.log_std = np.full(n_act, float(log_std0))
        self.opt_a = Adam(self.mu.params + [self.log_std])
        self.opt_v = Adam(self.vf.params)

    def actor_grads(self, x, a, lp0, adv, clip, ent):
        """PPO clipped objective (to maximise) and its gradients as a loss. Returns grads, loss, approx_kl, clip fraction."""
        n, k = x.shape[0], a.shape[1]
        mu, cache = self.mu.forward(x, keep=True)
        sig = np.exp(self.log_std)
        z = (a - mu) / sig
        lp = -0.5 * (z * z).sum(axis=1) - self.log_std.sum() - 0.5 * k * LOG2PI
        lr = lp - lp0
        ratio = np.exp(np.clip(lr, -20.0, 20.0))
        c = np.clip(ratio, 1.0 - clip, 1.0 + clip)
        s1, s2 = ratio * adv, c * adv
        inside = (ratio > 1.0 - clip) & (ratio < 1.0 + clip)
        use1 = (s1 <= s2) | inside
        g = adv * ratio * use1
        dmu = -(g[:, None] * (z / sig)) / n
        grads = self.mu.backward(cache, dmu)
        gs = -(g[:, None] * (z * z - 1.0)).mean(axis=0) - ent * np.ones(k)
        grads.append(gs)
        loss = -float(np.minimum(s1, s2).mean()) - ent * float(self.log_std.sum() + 0.5 * k * (LOG2PI + 1.0))
        kl = float(((ratio - 1.0) - lr).mean())
        return grads, loss, kl, float((~inside).mean())

    def critic_grads(self, x, ret, vscale):
        v, cache = self.vf.forward(x, keep=True)
        e = v[:, 0] * vscale - ret
        dout = (e * vscale)[:, None] / x.shape[0]
        return self.vf.backward(cache, dout), 0.5 * float((e * e).mean())

    def update(self, b: dict, cfg: dict, lr: float, rng: np.random.Generator) -> dict:
        x, a, lp0, adv, ret, act = b["x"], b["a"], b["lp"], b["adv"], b["ret"], b["active"]
        out = {"pi_loss": 0.0, "kl": 0.0, "clip": 0.0, "v_loss": 0.0, "n_active": int(act.sum()), "n": int(len(x))}
        ia = np.flatnonzero(act)
        # Policy: only samples whose air handler is running (otherwise the action changes nothing and its advantage is noise).
        if len(ia) >= 32:
            xa, aa, lp, ad = x[ia], a[ia], lp0[ia], adv[ia]
            ad = (ad - ad.mean()) / (ad.std() + 1e-8)
            nb = max(1, len(ia) // cfg["mb"])
            count = 0
            stop = False
            for _ in range(cfg["epochs"]):
                perm = rng.permutation(len(ia))
                for mb in np.array_split(perm, nb):
                    g, loss, kl, cf = self.actor_grads(xa[mb], aa[mb], lp[mb], ad[mb], cfg["clip"], cfg["ent"])
                    self.opt_a.step(g, lr)
                    self.log_std[:] = np.clip(self.log_std, cfg["ls_min"], cfg["ls_max"])
                    out["pi_loss"] += loss
                    out["kl"] += kl
                    out["clip"] += cf
                    count += 1
                _, _, kl, _ = self.actor_grads(xa, aa, lp, ad, cfg["clip"], cfg["ent"])
                if kl > 1.5 * cfg["target_kl"]:
                    stop = True
                    break
            out["pi_loss"] /= max(count, 1)
            out["kl"] /= max(count, 1)
            out["clip"] /= max(count, 1)
            out["early_stop"] = stop
        # Value function: all samples.
        nb = max(1, len(x) // cfg["mb"])
        count = 0
        for _ in range(cfg["epochs"]):
            perm = rng.permutation(len(x))
            for mb in np.array_split(perm, nb):
                g, vl = self.critic_grads(x[mb], ret[mb], cfg["vscale"])
                self.opt_v.step(g, lr, max_norm=5.0)
                out["v_loss"] += vl
                count += 1
        out["v_loss"] /= max(count, 1)
        return out


def _numeric_check() -> None:
    rng = np.random.default_rng(0)
    ag = Agent(5, 2, (7, 6), -1.0, rng)
    # A last layer that is not nearly zero, so that the check also exercises it.
    ag.mu.params[-2] += rng.standard_normal(ag.mu.params[-2].shape) * 0.3
    x = rng.standard_normal((40, 5))
    a = rng.standard_normal((40, 2)) * 0.4
    adv = rng.standard_normal(40)
    mu = ag.mu.forward(x)
    sig = np.exp(ag.log_std)
    lp0 = -0.5 * (((a - mu) / sig) ** 2).sum(1) - ag.log_std.sum() - LOG2PI + 0.05 * rng.standard_normal(40)
    ret = rng.standard_normal(40)

    def lossa() -> float:
        return ag.actor_grads(x, a, lp0, adv, 0.2, 0.01)[1]

    def lossv() -> float:
        return ag.critic_grads(x, ret, 3.0)[1]

    def check(params, grads, f, name):
        worst = 0.0
        for p, g in zip(params, grads):
            it = np.nditer(p, flags=["multi_index"])
            while not it.finished:
                i = it.multi_index
                old = p[i]
                h = 1e-6
                p[i] = old + h
                up = f()
                p[i] = old - h
                dn = f()
                p[i] = old
                num = (up - dn) / (2 * h)
                worst = max(worst, abs(num - g[i]) / (abs(num) + abs(g[i]) + 1e-8))
                it.iternext()
        print(f"{name}: worst relative difference {worst:.2e}")
        assert worst < 1e-3, name

    g, *_ = ag.actor_grads(x, a, lp0, adv, 0.2, 0.01)
    check(ag.mu.params + [ag.log_std], g, lossa, "actor")
    g, _ = ag.critic_grads(x, ret, 3.0)
    check(ag.vf.params, g, lossv, "critic")

    # A toy problem: the action that matches a target function of the input gets the highest reward.
    rng = np.random.default_rng(1)
    ag = Agent(3, 1, (32, 32), -0.7, rng)
    cfg = dict(mb=256, epochs=4, clip=0.2, ent=0.0, ls_min=-3.0, ls_max=0.0, target_kl=0.02, vscale=1.0)
    for it in range(300):
        x = rng.standard_normal((2048, 3))
        mu = ag.mu.forward(x)
        sig = np.exp(ag.log_std)
        a = mu + sig * rng.standard_normal(mu.shape)
        lp = -0.5 * (((a - mu) / sig) ** 2).sum(1) - ag.log_std.sum() - 0.5 * LOG2PI
        r = -((a[:, 0] - np.sin(x[:, 0]) * 0.7) ** 2)
        v = ag.vf.forward(x)[:, 0]
        ag.update({"x": x, "a": a, "lp": lp, "adv": r - v, "ret": r, "active": np.ones(len(x), bool)}, cfg, 1e-3, rng)
    x = rng.standard_normal((4000, 3))
    e = float(np.mean((ag.mu.forward(x)[:, 0] - np.sin(x[:, 0]) * 0.7) ** 2))
    print(f"toy problem: mean squared error of the learned action {e:.4f} (zero policy {np.mean((np.sin(x[:, 0]) * 0.7) ** 2):.4f}), "
          f"final sigma {float(np.exp(ag.log_std[0])):.3f}")
    assert e < 0.03


if __name__ == "__main__":
    _numeric_check()
