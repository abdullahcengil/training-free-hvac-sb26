"""A neural residual controller, for the comparison with a trained policy (docs/TRAINED_BASELINE.md).

One small network is shared by every zone and another by every air handler, so the same weights run on any building, of any
size. Each network adds a correction to the action of the strongest official baseline (pid_water, copied verbatim in
pid_water_official.py); with no weights the policy is exactly pid_water. A decision is taken every `decide_every` steps
(15 minutes) and held. The on/off commands and the hot-water loop stay with pid_water.

The weights come from sb/train_rl.py.
"""

from __future__ import annotations

import copy
import importlib.util
import math
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np

ZONE_DIM = 27
AHU_DIM = 27
LOG2PI = float(np.log(2.0 * np.pi))


def _load_base():
    name = "pid_water_official_for_rl"
    if name in sys.modules:
        return sys.modules[name].PIDWaterResetPolicy
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / "pid_water_official.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod.PIDWaterResetPolicy


def _mlp(params: list[np.ndarray], x: np.ndarray) -> np.ndarray:
    h = x
    for i in range(0, len(params) - 2, 2):
        h = np.tanh(h @ params[i] + params[i + 1])
    return h @ params[-2] + params[-1]


def _num(name: str) -> int:
    digits = "".join(ch for ch in name if ch.isdigit())
    return int(digits) if digits else 0


class TrainedResidualPolicy:
    def __init__(self, building_meta_data: dict[str, Any], action_spec: Any, weights: dict | None = None,
                 weights_file: str | None = None, decide_every: int = 3, explore: bool = False, seed: int = 0,
                 **_: Any) -> None:
        m = building_meta_data
        self.base = _load_base()(m, action_spec)
        if weights is None and weights_file:
            with open(weights_file, "rb") as f:
                weights = pickle.load(f)
        self.w = weights
        self.every = int(decide_every)
        self.explore = bool(explore)
        self.rng = np.random.default_rng(seed)

        names = list(m["observation_field_names"])
        self.idx = idx = {n: i for i, n in enumerate(names)}
        self.comfort = tuple(float(x) for x in m["comfort_temp_window"])
        self.eco = tuple(float(x) for x in m["eco_temp_window"])
        self.morning = float(m["morning_start_hour"])
        self.evening = float(m["evening_start_hour"])
        self.temp_idx = list(m["temp_indices"])
        self.n_ahu = len(self.temp_idx)
        press = list(m["pressure_indices"])
        recirc = list(m["recirculation_indices"])
        self.press_idx = press[: self.n_ahu]
        self.recirc_idx = recirc[: self.n_ahu] + [-1] * (self.n_ahu - len(recirc))
        norm = m["observation_normalization_metadata"]["zone_air_temperature_sensor"]
        self.t_mean, self.t_std = float(norm["sample_mean"]), float(norm["sample_std"])

        assign = m["ahu_zone_assignments"]
        zai = m["zone_action_indices"]
        zt, zmax, zd, zr, za, rooms, zdo, zro = [], [], [], [], [], [], [], []
        self.members: list[np.ndarray] = []
        for a, ahu in enumerate(sorted(assign.keys(), key=_num)[: self.n_ahu]):
            mem = []
            for room in assign[ahu]:
                vav = room.replace("room_", "VAV_")
                t = idx.get(vav + "_zone_air_temperature_sensor")
                if t is None or vav not in zai:
                    continue
                mem.append(len(zt))
                zt.append(t)
                zmax.append(idx.get(vav + "_supply_air_flowrate_setpoint", -1))
                zd.append(zai[vav].get("supply_air_damper_percentage_command", -1))
                zr.append(zai[vav].get("reheat_valve_percentage_command", -1))
                zdo.append(idx.get(vav + "_supply_air_damper_percentage_command", -1))
                zro.append(idx.get(vav + "_reheat_valve_percentage_command", -1))
                za.append(a)
                rooms.append(room)
            self.members.append(np.asarray(mem, dtype=int))
        self.z_t = np.asarray(zt, dtype=int)
        self.z_maxflow = np.asarray(zmax, dtype=int)
        self.z_damper = np.asarray(zd, dtype=int)
        self.z_reheat = np.asarray(zr, dtype=int)
        self.z_damper_obs = np.asarray(zdo, dtype=int)
        self.z_reheat_obs = np.asarray(zro, dtype=int)
        self.z_ahu = np.asarray(za, dtype=int)
        self.z_room = rooms
        self.nz = len(zt)
        self.a_sat = [idx.get(f"ahs_ahu_{a + 1}_supply_air_temperature_sensor", -1) for a in range(self.n_ahu)]
        self.a_flow = [idx.get(f"ahs_ahu_{a + 1}_supply_air_flowrate_sensor", -1) for a in range(self.n_ahu)]
        self.a_press = [idx.get(f"ahs_ahu_{a + 1}_supply_air_static_pressure_sensor", -1) for a in range(self.n_ahu)]
        self.a_recirc = [idx.get(f"ahs_ahu_{a + 1}_recirculation_percentage_command", -1) for a in range(self.n_ahu)]
        self.oat_idx = idx.get("ahs_ahu_1_outside_air_temperature_sensor")
        self.water_obs = idx.get("hws_supply_water_temperature_sensor")
        self.cm_now = idx.get("comfort_mode_now")
        self.cm_soon = idx.get("comfort_mode_soon")
        self.occ_obs = idx.get("num_occupants")
        self.hs, self.hc = idx.get("hod_sin_000"), idx.get("hod_cos_000")
        self.ds, self.dc = idx.get("dow_sin_000"), idx.get("dow_cos_000")

        self.k = 0
        self.t1: np.ndarray | None = None
        self.t2: np.ndarray | None = None
        self.oat_avg: float | None = None
        self.occ_zero = math.inf
        self.arrived = False
        self.dz = np.zeros((self.nz, 2))
        self.da = np.zeros((self.n_ahu, 3))
        self.last: dict | None = None

    # ---------------------------------------------------------------- features
    def _clock(self, obs: np.ndarray) -> tuple[float, int]:
        hour = (math.atan2(obs[self.hs], obs[self.hc]) % (2 * math.pi)) * 24 / (2 * math.pi)
        day = int(round((math.atan2(obs[self.ds], obs[self.dc]) % (2 * math.pi)) * 7 / (2 * math.pi))) % 7
        return hour, day

    def _h2c(self, hour: float, day: int) -> float:
        for k in range(0, 8):
            if (day + k) % 7 >= 5:
                continue
            if k == 0 and self.morning <= hour < self.evening:
                return 0.0
            start = self.morning + 24 * k
            if start - hour > 0:
                return start - hour
        return 99.0

    def _features(self, obs: np.ndarray, temps: np.ndarray, cont: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        hour, day = self._clock(obs)
        now = float(obs[self.cm_now]) > 0.5 if self.cm_now is not None else (day < 5 and self.morning <= hour < self.evening)
        soon = float(obs[self.cm_soon]) if self.cm_soon is not None else 0.0
        h2c = min(self._h2c(hour, day), 12.0) / 12.0
        lo, hi = self.comfort if now else self.eco
        mid = 0.5 * (self.comfort[0] + self.comfort[1])
        t1 = self.t1 if self.t1 is not None else temps
        t2 = self.t2 if self.t2 is not None else t1
        oat = float(obs[self.oat_idx]) if self.oat_idx is not None else 290.0
        oat_avg = self.oat_avg if self.oat_avg is not None else oat
        tw = float(obs[self.water_obs]) if self.water_obs is not None else 330.0
        occ_raw = float(obs[self.occ_obs]) if self.occ_obs is not None else 0.0
        occ = min(max(occ_raw - self.occ_zero, 0.0) * 125.0 / max(self.nz, 1) / 3.0, 3.0)
        hod_s, hod_c, dow_s, dow_c = float(obs[self.hs]), float(obs[self.hc]), float(obs[self.ds]), float(obs[self.dc])
        wd = 1.0 if day < 5 else 0.0
        oat_f, oat_avg_f, tw_f = (oat - 295.0) / 15.0, (oat_avg - 295.0) / 15.0, (tw - 330.0) / 20.0

        e = (temps - mid) / 3.0
        n = self.nz
        amean, amin, amax = np.zeros(self.n_ahu), np.zeros(self.n_ahu), np.zeros(self.n_ahu)
        for a, mem in enumerate(self.members):
            if len(mem):
                amean[a], amin[a], amax[a] = e[mem].mean(), e[mem].min(), e[mem].max()
        maxflow = np.where(self.z_maxflow >= 0, obs[np.maximum(self.z_maxflow, 0)], 2.0)
        maxflow = np.maximum(maxflow, 1e-3)
        sat = np.array([(float(obs[i]) - 295.0) / 10.0 if i >= 0 else 0.0 for i in self.a_sat])
        damp_prev = np.where(self.z_damper_obs >= 0, obs[np.maximum(self.z_damper_obs, 0)], 0.0)
        reheat_prev = np.where(self.z_reheat_obs >= 0, obs[np.maximum(self.z_reheat_obs, 0)], 0.0)
        base_d = np.where(self.z_damper >= 0, cont[np.maximum(self.z_damper, 0)], 0.0)
        base_r = np.where(self.z_reheat >= 0, cont[np.maximum(self.z_reheat, 0)], 0.0)

        xz = np.empty((n, ZONE_DIM))
        xz[:, 0] = e
        xz[:, 1] = (temps - lo) / 3.0
        xz[:, 2] = (temps - hi) / 3.0
        xz[:, 3] = (temps - t1) * 2.0
        xz[:, 4] = (t1 - t2) * 2.0
        xz[:, 5] = 1.0 if now else 0.0
        xz[:, 6] = soon
        xz[:, 7] = h2c
        xz[:, 8], xz[:, 9], xz[:, 10], xz[:, 11] = hod_s, hod_c, dow_s, dow_c
        xz[:, 12] = wd
        xz[:, 13], xz[:, 14] = oat_f, oat_avg_f
        xz[:, 15] = occ
        xz[:, 16] = 1.0 if self.arrived else 0.0
        xz[:, 17], xz[:, 18] = damp_prev, reheat_prev
        xz[:, 19] = np.log(maxflow / 2.0)
        xz[:, 20] = sat[self.z_ahu]
        xz[:, 21], xz[:, 22], xz[:, 23] = amean[self.z_ahu], amin[self.z_ahu], amax[self.z_ahu]
        xz[:, 24] = tw_f
        xz[:, 25], xz[:, 26] = base_d, base_r

        xa = np.empty((self.n_ahu, AHU_DIM))
        for a, mem in enumerate(self.members):
            xa[a, 0], xa[a, 1], xa[a, 2] = amean[a], amin[a], amax[a]
            if len(mem):
                xa[a, 3] = float((temps[mem] < lo).mean())
                xa[a, 4] = float((temps[mem] > hi).mean())
                xa[a, 5] = float(((temps - t1)[mem]).mean()) * 2.0
                flow_cap = float(maxflow[mem].sum())
                xa[a, 20] = float(damp_prev[mem].mean())
            else:
                xa[a, 3] = xa[a, 4] = xa[a, 5] = xa[a, 20] = 0.0
                flow_cap = 1.0
            xa[a, 6] = 1.0 if now else 0.0
            xa[a, 7] = soon
            xa[a, 8] = h2c
            xa[a, 9], xa[a, 10], xa[a, 11], xa[a, 12] = hod_s, hod_c, dow_s, dow_c
            xa[a, 13] = wd
            xa[a, 14], xa[a, 15] = oat_f, oat_avg_f
            xa[a, 16] = occ
            xa[a, 17] = sat[a]
            xa[a, 18] = min(float(obs[self.a_flow[a]]) / flow_cap, 2.0) if self.a_flow[a] >= 0 else 0.0
            xa[a, 19] = math.tanh(float(obs[self.a_press[a]]) / 500.0) if self.a_press[a] >= 0 else 0.0
            xa[a, 21] = float(obs[self.a_recirc[a]]) if self.a_recirc[a] >= 0 else 0.0
            xa[a, 22] = float(cont[self.temp_idx[a]])
            xa[a, 23] = float(cont[self.press_idx[a]]) if a < len(self.press_idx) else 0.0
            xa[a, 24] = float(cont[self.recirc_idx[a]]) if self.recirc_idx[a] >= 0 else 0.0
            xa[a, 25] = tw_f
            xa[a, 26] = math.log(max(len(mem), 1) / 10.0)
        return xz, xa

    # ---------------------------------------------------------------- control
    def _observe(self, obs: np.ndarray, temps: np.ndarray) -> None:
        oat = float(obs[self.oat_idx]) if self.oat_idx is not None else 290.0
        self.oat_avg = oat if self.oat_avg is None else self.oat_avg + (oat - self.oat_avg) / 288.0
        if self.occ_obs is not None:
            v = float(obs[self.occ_obs])
            self.occ_zero = min(self.occ_zero, v)
            present = v > self.occ_zero + 1e-3
            comfort = float(obs[self.cm_now]) > 0.5 if self.cm_now is not None else True
            self.arrived = (self.arrived or present) if comfort else False

    def _decide(self, obs: np.ndarray, temps: np.ndarray, cont: np.ndarray, disc: np.ndarray) -> None:
        if self.w is None:
            self.dz[:] = 0.0
            self.da[:] = 0.0
            self.last = None
            return
        xz, xa = self._features(obs, temps, cont)
        mz, ma = _mlp(self.w["z_mu"], xz), _mlp(self.w["a_mu"], xa)
        if self.explore:
            sz, sa = np.exp(self.w["z_ls"]), np.exp(self.w["a_ls"])
            nz_, na_ = self.rng.standard_normal(mz.shape), self.rng.standard_normal(ma.shape)
            az, aa = mz + sz * nz_, ma + sa * na_
            lpz = -0.5 * (nz_ * nz_).sum(1) - self.w["z_ls"].sum() - 0.5 * az.shape[1] * LOG2PI
            lpa = -0.5 * (na_ * na_).sum(1) - self.w["a_ls"].sum() - 0.5 * aa.shape[1] * LOG2PI
            on = disc[: self.n_ahu] == 1
            self.last = {"xz": xz, "az": az, "lpz": lpz, "xa": xa, "aa": aa, "lpa": lpa, "on": on}
        else:
            az, aa = mz, ma
        self.dz, self.da = az, aa

    def get_action(self, obs: np.ndarray) -> dict[str, np.ndarray]:
        action = self.base.get_action(obs)   # with the observation exactly as it came (float32), as the baseline gets it
        obs = np.asarray(obs, dtype=np.float64)
        cont = np.asarray(action["continuous_action"], dtype=np.float64).copy()
        disc = np.asarray(action["discrete_action"], dtype=np.int32)
        temps = obs[self.z_t] * self.t_std + self.t_mean
        self._observe(obs, temps)
        if self.k % self.every == 0:
            self._decide(obs, temps, cont, disc)
        if self.w is not None:
            ok = self.z_damper >= 0
            cont[self.z_damper[ok]] += self.dz[ok, 0]
            ok = self.z_reheat >= 0
            cont[self.z_reheat[ok]] += self.dz[ok, 1]
            for a in range(self.n_ahu):
                cont[self.temp_idx[a]] += self.da[a, 0]
                if a < len(self.press_idx):
                    cont[self.press_idx[a]] += self.da[a, 1]
                if self.recirc_idx[a] >= 0:
                    cont[self.recirc_idx[a]] += self.da[a, 2]
        self.t2 = self.t1
        self.t1 = temps
        self.k += 1
        return {"continuous_action": np.clip(cont, -1.0, 1.0).astype(np.float32), "discrete_action": disc}

    def peek(self, obs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """The features the next decision would see, without touching the controller's state (for the critic's bootstrap)."""
        c = copy.deepcopy(self.base)
        action = c.get_action(obs)
        obs = np.asarray(obs, dtype=np.float64)
        cont = np.asarray(action["continuous_action"], dtype=np.float64)
        temps = obs[self.z_t] * self.t_std + self.t_mean
        return self._features(obs, temps, cont)
