"""Zonal controller for the Smart Buildings Challenge (NeurIPS 2026).

A physics-informed, training-free policy. Each zone gets a one-step model
predictive controller whose model is identified online:

    T[k+1] - T[k] = -lam_z * (T[k] - 295) + g_z * q[k-1] + c_z

where q = airflow x heat capacity x (discharge - zone temperature) is the heat
(kW) the VAV box delivers. An open-loop probe showed that the heat commanded at
one step moves the zone in the step after it, and that zones relax quickly
(lam ~ 0.3 per 5-min step) towards an equilibrium set by the envelope and the
neighbours. The three coefficients are identified online per zone by recursive
least squares with forgetting, so nothing is fitted offline. Because of the
one-step delay the controller first predicts T[k+1] from the heat already in
the pipe, then chooses q[k] so that T[k+2] lands on its target. The plant-level actions follow standard VAV sequences
(in the spirit of ASHRAE Guideline 36):

* static pressure is the lowest that still lets the most demanding zone get
  its airflow (fan power ~ flow x pressure);
* supply-air temperature is reset to the warmest value that still cools the
  most demanding zone at full flow, so idle zones are not overcooled;
* outside air is used for free cooling when it is colder than the return air;
* heating comes from VAV reheat, with the least air that carries the heat;
* the comfort band is targeted ahead of each occupied period (optimal start).

Self-contained (numpy only) so it can be pasted into the Kaggle notebook.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np

C_AIR = 1005.0 * 1.2  # J/(m3 K), volumetric heat capacity of air

_DEFAULTS = dict(
    margin_heat=0.5,       # K above the heating setpoint we aim for
    margin_cool=0.5,       # K below the cooling setpoint we aim for
    aim_inside=0.3,        # K further inside the band when we must act
    f_min=0.10,            # damper floor enforced by the simulator
    sat_min=285.0,         # coldest supply-air setpoint (K)
    sat_max=305.0,         # setpoint that disables mechanical cooling (K)
    discharge_max=308.15,  # VAV discharge-temperature cap (K)
    water_heat=350.0,      # supply water temperature while heating (K)
    water_idle=350.0,      # supply water temperature otherwise (K)
    water_idle_h=0.0,      # hours without any heat demand before water_idle applies (a boiler standby setback for
                           # long idle spells only, so the setpoint does not toggle with short heating gaps)
    dp_heat=1.0,           # pump pressure command while heating (normalised)
    dp_reset=0,            # 1: hot-water pump pressure reset (as in ASHRAE Guideline 36): the lowest pressure at which
                           # every open reheat coil still reaches its planned discharge temperature; pump power
                           # goes as pressure^1.5, and full pressure is far more than the coils need
    dp_margin=1.3,         # factor on the water capacity the coils need
    dp_valve_min=0.05,     # dp_reset 2: each open reheat valve is opened only as far as its coil needs at that pressure
    dp_min_bar=0.5,
    dp_max_bar=20.0,       # top of the action range
    dp_kv=0.108,           # reheat valve Kv (m3/h at 1 bar); the same in every generated building (scenario files)
    reheat_eff=0.9,        # assumed coil effectiveness for planning
    guard=1.0,             # K inside the eco band we defend when unoccupied (negative: wider)
    opt_start=0,           # model-based start time for the comfort period
    opt_start_max_h=8.0,
    opt_start_safety=1.3,
    lead_h=2.0,            # hours before comfort starts that we target it
    g0=0.15,               # prior gain, K per kW per step (probe median 0.16)
    lam0=0.30,             # prior relaxation per step (probe median 0.30)
    g_min=0.02,
    g_max=0.6,
    lam_min=0.02,
    lam_max=0.8,
    rls_lambda=0.99,       # forgetting factor
    p_g=1e-3, p_lam=1e-3, p_c=1e-1,   # RLS prior variances
    damping=0.7,           # fraction of the gap to target closed per step
    offset_free=0,         # 1: damp only the move from the next predicted temperature, not the heat that holds the
                           # zone (no steady droop under large losses or gains; stress test, 23 Oct)
    idle_aware=1,          # plan reheat for idle zones overcooled by the floor airflow
    err_clip=0.5,          # K, largest one-step prediction error the RLS believes
    c_max=1.0,             # K/step, bound on the identified offset
    p_trace_max=1.0,       # bound on the RLS covariance trace
    safety_k=1.5,          # K outside the target band that triggers full effort
    safety_pred=0,         # 1: full effort only if the zone is still far out after the heat in the pipe (v8);
                           # 2: the same for cooling only (heating is already capped by f_heat_max)
    dist_obs=0,            # 1: offset-free prediction with a per-zone disturbance estimate (v8)
    dist_beta=0.1,         # smoothing of the disturbance estimate (per step)
    dist_max=1.5,          # K per step, bound on the disturbance estimate
    night_glide=0,         # 1: unoccupied heating floor that rises towards the comfort target at the
                           # rate the zone can actually heat (per-zone optimal start, v9)
    glide_floor=-5.0,      # K relative to the eco band's lower edge: the lowest a zone may float
    glide_safety=0.7,      # fraction of the identified heating rate the glide path assumes
    glide_rate_max=3.0,    # K per hour, most the glide path assumes
    glide_lead=0.0,        # hours before comfort time the glide path reaches the target
    glide_oat=400.0,       # K: glide only while the 24-hour mean outside temperature is below this
    f_heat_rec=0.2,        # heating airflow cap while unoccupied (recovery costs no comfort)
    cool_glide=0,          # 1: unoccupied cooling ceiling that falls towards the comfort target at the
                           # rate the zone can actually cool (cooling-side twin of night_glide, v10)
    cool_ceiling=5.0,      # K relative to the eco band's upper edge: the warmest a zone may float
    cool_safety=0.7,       # fraction of the identified cooling rate the path assumes
    cool_rec_frac=1.0,     # airflow (fraction of the box maximum) the pull-down rate assumes
    cool_glide_oat=0.0,    # K: cooling glide only while the 24-hour mean outside temperature is above this
    cool_rate_max=3.0,     # K per hour, most the pull-down path assumes
    cool_free=0,           # 1: no cooling glide while outside air is colder than the zones' cooling target by
                           # cool_free_dt (cooling is then fan work only, and the cool is stored in the building)
    cool_free_dt=1.0,      # K
    cool_guard=0,          # 1: no cooling glide for a zone that has recently been too warm while occupied
                           # (its demonstrated cooling capacity is too small to recover from a float)
    cool_guard_beta=0.0064,  # smoothing of the occupied overshoot (per occupied step; about one day)
    cool_guard_max=0.05,   # K, smoothed overshoot above the comfort band that disables the glide
    precool=0,             # 1: before weekday comfort time in hot weather, cool zones to the lower part
                           # of the band: heat is removed at night, when outside air (30 % of the
                           # supply) is cooler and electricity cheaper, and the floor slab stores the cool
    precool_h=6.0,         # hours before comfort time the precooling starts
    precool_k=1.5,         # K below the usual cooling target
    precool_oat=295.15,    # K: only while the 24-hour mean outside temperature is above this
    mass_model=0,          # 1: zone model with a slow mass node, an envelope term and an internal-gain term
                           # (v11): dT = -lam (T - Tm) + g q[k-1] + c + b (oat - T) + c_cm cm, where Tm,
                           # the floor slab and furniture, follows the room air with a lag of mass_n steps
    mass_n=48.0,           # steps; the slab is about four hours behind the room (scenario files)
    m2_forget=0.998,       # RLS forgetting factor of the mass model (replay of v10 traces: 0.998 beats 0.995 and 0.999)
    m2_prior=(-0.33, 0.27, 0.09, 0.016, 0.25),  # medians of offline fits on four training traces
    m2_lo=(-0.8, 0.05, -2.0, 0.0, -0.5),
    m2_hi=(-0.05, 0.8, 1.5, 0.12, 1.0),
    m2_pvar=(1e-3, 1e-3, 1e-2, 1e-5, 1e-2),
    m2_rate=0,             # 1 (with mass_model): the night glide's heating rate and the cooling glide's pull-down
                           # rate from the mass model (0 keeps the first-order model, which mass_model no longer
                           # updates, so it stays at its prior)
    glide_roll=0,          # 1 (with mass_model): the night glide starts each zone's recovery from a rollout
                           # of its model at the recovery airflow, instead of a constant heating rate
    roll_safety=0.8,       # start when the rollout needs at least this fraction of the steps left
    roll_max=144,          # steps, longest rollout
    glide_learn=0,         # 1: the night glide uses each zone's own achieved heating rate, learned from the
                           # steps in which it was heated at (nearly) the recovery cap two steps in a row
                           # (self-learning optimal start; slab-limited zones learn a slow rate and start early)
    learn_beta=0.02,       # smoothing of the learned rate per observed step
    learn_full=0.8,        # fraction of the recovery-cap heat that counts as full effort
    roll_mass=0,           # 1: the rollout also waits for the slab to be warm enough for the daytime cap
    roll_mass_k=0.0,       # K added to the slab temperature that requires
    empty_day=0,           # 1: a workday on which nobody has arrived empty_h hours after comfort start is run as
                           # unoccupied until someone arrives (the occupancy model keeps people home on US
                           # federal holidays; the setpoint schedule does not know them)
    empty_h=1.5,           # hours
    empty_pm=0,            # 1: once everyone has left in the afternoon, the rest of the day is unoccupied
                           # (people who have left do not come back the same day)
    empty_pm_h=7.0,        # hours after comfort start before the afternoon rule may apply (departures from 13:00)
    rls=1,                 # ablation switch: 0 freezes the zone model at its prior
    delay_comp=1,          # ablation switch: 0 ignores the one-step delay
    risk_margin=0,         # choose band margins from the cost ratio and prediction error
    sigma0=0.1, sigma_beta=0.02, sigma_mult=1.3,
    reheat_gas_factor=2.3, # gas per kW of zone heat (outside air is heated too)
    fan_share=0.3,         # fan electricity per kW of cooling, rough
    m_min=0.05, m_max=1.0,
    f_heat_max=0.2,        # heating airflow cap as a fraction of the box maximum
    f_heat_safety=0.2,     # cap for zones below their band by more than boost_k
    boost_k=1.5,
    sat_econ=1,            # choose the supply-air setpoint by estimated cost
    sat_econ_max=295.0,
    sat_econ_step=1.0,
    fan_eff=0.9,           # simulator default
    cop=3.5,               # simulator default
    w_elec=0.0023,         # reward per kW per step, x number of AHUs (from the reward code)
    w_gas=0.00105,
    w_comfort=0.12,        # reward per K per step for the whole building's zones
)


class TransferPolicy:
    """Per-zone one-step MPC with online identification plus G36-style plant."""

    name = "zonal"

    def __init__(self, building_meta_data: Mapping[str, Any], action_spec: Any,
                 **params: float) -> None:
        self.p = dict(_DEFAULTS)
        self.p.update(params)
        m = building_meta_data
        self.n_cont = int(m["n_continuous_action"])
        self.n_disc = int(m["n_discrete_action"])
        names = list(m["observation_field_names"])
        self.idx = {n: i for i, n in enumerate(names)}
        self._norm = m.get("observation_normalization_metadata", {}) or {}
        self.comfort = tuple(float(x) for x in m["comfort_temp_window"])
        self.eco = tuple(float(x) for x in m["eco_temp_window"])
        self.morning = float(m["morning_start_hour"])
        self.evening = float(m["evening_start_hour"])

        self.temp_idx = list(m["temp_indices"])
        self.recirc_idx = list(m["recirculation_indices"])
        self.water_idx = list(m["water_indices"])
        self.n_ahu = len(self.temp_idx)
        press = list(m["pressure_indices"])
        self.press_idx = press[: self.n_ahu]
        self.dp_idx = press[self.n_ahu] if len(press) > self.n_ahu else None
        self.pump_disc = self.n_disc - 1

        assign = m["ahu_zone_assignments"]
        ahu_ids = sorted(assign.keys(), key=_num)
        zai = m["zone_action_indices"]
        zt, zmax, zd, zr, za = [], [], [], [], []
        self.ahu_members: list[np.ndarray] = []
        self.ahu_flow_obs: list[int | None] = []
        for a, ahu in enumerate(ahu_ids[: self.n_ahu]):
            members = []
            for room in assign[ahu]:
                vav = room.replace("room_", "VAV_")
                t = self.idx.get(vav + "_zone_air_temperature_sensor")
                if t is None or vav not in zai:
                    continue
                members.append(len(zt))
                zt.append(t)
                zmax.append(self.idx.get(vav + "_supply_air_flowrate_setpoint", -1))
                zd.append(zai[vav].get("supply_air_damper_percentage_command", -1))
                zr.append(zai[vav].get("reheat_valve_percentage_command", -1))
                za.append(a)
            self.ahu_members.append(np.asarray(members, dtype=int))
            self.ahu_flow_obs.append(self.idx.get(f"ahs_ahu_{a + 1}_supply_air_flowrate_sensor"))
        self.z_t = np.asarray(zt, dtype=int)
        self.z_maxflow_idx = np.asarray(zmax, dtype=int)
        self.z_damper = np.asarray(zd, dtype=int)
        self.z_reheat = np.asarray(zr, dtype=int)
        self.z_ahu = np.asarray(za, dtype=int)
        self.nz = len(zt)
        self.t_mean, self.t_std = self._norm_consts("zone_air_temperature_sensor")
        self.oat_idx = self.idx.get("ahs_ahu_1_outside_air_temperature_sensor")
        self.water_obs = self.idx.get("hws_supply_water_temperature_sensor")
        self.cm_now = self.idx.get("comfort_mode_now")
        self.occ_obs = self.idx.get("num_occupants")
        self.occ_zero = math.inf          # observed value with nobody in (its running minimum)
        self._no_heat = 0                 # steps since any zone was last heated
        self._comfort_t0 = None           # step at which today's comfort period started
        self._arrived = False             # somebody has come in today
        self.hs, self.hc = self.idx.get("hod_sin_000"), self.idx.get("hod_cos_000")
        self.ds, self.dc = self.idx.get("dow_sin_000"), self.idx.get("dow_cos_000")

        # Online model state.
        # theta = [-lam, g, c]; one RLS per zone.
        self.theta = np.tile(np.array([-self.p["lam0"], self.p["g0"], 0.0]), (self.nz, 1))
        self.Pm = np.tile(np.diag([self.p["p_lam"], self.p["p_g"], self.p["p_c"]]), (self.nz, 1, 1))
        self.prev_t = None
        self.prev_q = np.zeros(self.nz)    # heat applied during the last step
        self.prev_q2 = np.zeros(self.nz)   # heat applied during the step before
        self.prev_flow_cmd = np.zeros(self.nz)
        self.prev_ahu_on = np.zeros(self.n_ahu, dtype=bool)
        self.prev_s = np.full(self.n_ahu, 295.0)
        self.prev_dis = np.zeros(self.nz)
        self._far_cold = np.zeros(self.nz, dtype=bool)
        self._boost = np.zeros(self.nz, dtype=bool)
        self._prev_comfort = None
        self.err_var = np.full(self.nz, self.p["sigma0"] ** 2)
        self.dhat = np.zeros(self.nz)   # disturbance estimate, K per step (v8)
        self.over = np.zeros(self.nz)   # smoothed occupied overshoot above the comfort band, K (v10)
        # Mass model (v11): theta2 = [-lam, g, c, b, c_cm] per zone, Tm the slab estimate.
        self.theta2 = np.tile(np.asarray(self.p["m2_prior"], dtype=float), (self.nz, 1))
        self.P2 = np.tile(np.diag(np.asarray(self.p["m2_pvar"], dtype=float)), (self.nz, 1, 1))
        self.tm = None
        self.prev_tm = None
        self.prev_oat = None
        self.prev_cm = 0.0
        self._roll_on = np.zeros(self.nz, dtype=bool)   # zones whose recovery has started tonight
        self.rec_rate = np.full(self.nz, self.p["glide_rate_max"] / 12.0)   # learned heating rate, K/step
        self._full = np.zeros(self.nz, dtype=bool)      # heated at full recovery effort (last command)
        self._full2 = np.zeros(self.nz, dtype=bool)     # ... and the command before
        self._unocc = False
        self.oat_avg = None
        self.step = 0

    # ------------------------------------------------------------------ utils
    def _norm_consts(self, key: str) -> tuple[float, float]:
        c = self._norm.get(key)
        if not c:
            return 0.0, 1.0
        return float(c["sample_mean"]), float(c["sample_std"])

    def _clock(self, obs: np.ndarray) -> tuple[float, int]:
        hour = (math.atan2(obs[self.hs], obs[self.hc]) % (2 * math.pi)) * 24 / (2 * math.pi)
        day = int(round((math.atan2(obs[self.ds], obs[self.dc]) % (2 * math.pi)) * 7 / (2 * math.pi))) % 7
        return hour, day

    def _calibrate_schedule(self, comfort_now: bool, hour: float) -> None:
        """Align the schedule with the comfort flag the building reports.

        If the flag switches on at a different clock hour than the metadata
        says (for example a time-zone difference), shift both ends of the
        comfort period by the observed difference.
        """
        prev = self._prev_comfort
        self._prev_comfort = comfort_now
        if prev is None or prev == comfort_now:
            return
        expected = self.morning if comfort_now else self.evening
        diff = (hour - expected + 12.0) % 24.0 - 12.0
        if abs(diff) > 0.2:
            self.morning = (self.morning + diff) % 24.0
            self.evening = (self.evening + diff) % 24.0

    def _next_comfort(self, hour: float, day: int) -> float:
        """Hours to the start of the next workday's comfort period, today excluded."""
        for k in range(1, 8):
            if (day + k) % 7 < 5:
                return self.morning + 24 * k - hour
        return 99.0

    def _empty_day(self, obs: np.ndarray, h2c: float, hour: float, day: int) -> float:
        """Run an empty comfort day as unoccupied (empty_day, empty_pm); returns h2c."""
        p = self.p
        ov = float(obs[self.occ_obs])
        self.occ_zero = min(self.occ_zero, ov)
        present = ov > self.occ_zero + 1e-3
        if h2c > 0.0:
            self._comfort_t0 = None
            return h2c
        if self._comfort_t0 is None:
            self._comfort_t0, self._arrived = self.step, False
        self._arrived = self._arrived or present
        hrs = (self.step - self._comfort_t0) / 12.0
        if p["empty_day"] and not self._arrived and hrs >= p["empty_h"]:
            return self._next_comfort(hour, day)
        if p["empty_pm"] and self._arrived and not present and hrs >= p["empty_pm_h"]:
            return self._next_comfort(hour, day)
        return h2c

    def _hours_to_comfort(self, hour: float, day: int) -> float:
        for k in range(0, 8):
            d = (day + k) % 7
            if d >= 5:
                continue
            if k == 0 and self.morning <= hour < self.evening:
                return 0.0
            start = self.morning + 24 * k
            if start - hour > 0:
                return start - hour
        return 99.0

    # ---------------------------------------------------------- identification
    def _identify(self, temps: np.ndarray, obs: np.ndarray) -> None:
        if self.p["mass_model"]:
            self._identify_m2(temps)
            return
        if self.prev_t is None or not self.p["rls"]:
            return
        # The step that just ended moved prev_t -> temps under the heat that
        # was commanded one step earlier (prev_q2).
        q = self.prev_q2
        phi = np.stack([self.prev_t - 295.0, q, np.ones(self.nz)], axis=1)
        y = temps - self.prev_t
        lam = self.p["rls_lambda"]
        Pphi = np.einsum("nij,nj->ni", self.Pm, phi)
        denom = lam + np.einsum("ni,ni->n", phi, Pphi)
        k = Pphi / denom[:, None]
        err = y - np.einsum("ni,ni->n", phi, self.theta)
        if self.p["dist_obs"]:
            # Offset-free prediction: what the bounded model keeps missing is
            # tracked as a slowly varying disturbance and added to predictions.
            b_d = self.p["dist_beta"]
            self.dhat = np.clip((1 - b_d) * self.dhat + b_d * err, -self.p["dist_max"], self.p["dist_max"])
        # A single surprising step must not drag the model far (robust RLS).
        err = np.clip(err, -self.p["err_clip"], self.p["err_clip"])
        b = self.p["sigma_beta"]
        self.err_var = (1 - b) * self.err_var + b * err * err
        self.theta = self.theta + k * err[:, None]
        self.Pm = (self.Pm - np.einsum("ni,nj->nij", k, Pphi)) / lam
        self.theta[:, 0] = np.clip(self.theta[:, 0], -self.p["lam_max"], -self.p["lam_min"])
        self.theta[:, 1] = np.clip(self.theta[:, 1], self.p["g_min"], self.p["g_max"])
        self.theta[:, 2] = np.clip(self.theta[:, 2], -self.p["c_max"], self.p["c_max"])
        # Keep the covariance bounded so forgetting cannot blow it up.
        tr = np.trace(self.Pm, axis1=1, axis2=2)
        cap = self.p["p_trace_max"]
        big = tr > cap
        if np.any(big):
            self.Pm[big] *= (cap / tr[big])[:, None, None]

    def _identify_m2(self, temps: np.ndarray) -> None:
        """Recursive least squares for the mass model (v11).

        The step that just ended moved prev_t -> temps under the heat commanded
        one step earlier (prev_q2), with the slab at its previous estimate. The
        slab estimate then follows the room air with a lag of mass_n steps.
        """
        p = self.p
        if self.tm is None:
            self.tm = temps.copy()
            return
        if self.prev_t is None:
            return
        tm_prev = self.tm
        if p["rls"]:
            phi = np.stack([self.prev_t - tm_prev, self.prev_q2, np.ones(self.nz),
                            self.prev_oat - self.prev_t, np.full(self.nz, self.prev_cm)], axis=1)
            y = temps - self.prev_t
            lam = p["m2_forget"]
            Pphi = np.einsum("nij,nj->ni", self.P2, phi)
            denom = lam + np.einsum("ni,ni->n", phi, Pphi)
            k = Pphi / denom[:, None]
            err = y - np.einsum("ni,ni->n", phi, self.theta2)
            if p["dist_obs"]:
                b_d = p["dist_beta"]
                self.dhat = np.clip((1 - b_d) * self.dhat + b_d * err, -p["dist_max"], p["dist_max"])
            err = np.clip(err, -p["err_clip"], p["err_clip"])
            b = p["sigma_beta"]
            self.err_var = (1 - b) * self.err_var + b * err * err
            self.theta2 = np.clip(self.theta2 + k * err[:, None], np.asarray(p["m2_lo"]), np.asarray(p["m2_hi"]))
            self.P2 = (self.P2 - np.einsum("ni,nj->nij", k, Pphi)) / lam
            tr = np.trace(self.P2, axis1=1, axis2=2)
            cap = p["p_trace_max"]
            big = tr > cap
            if np.any(big):
                self.P2[big] *= (cap / tr[big])[:, None, None]
        self.tm = tm_prev + (self.prev_t - tm_prev) / p["mass_n"]

    def _m2_step(self, t, tm, q, oat, cmv):
        """One step of the mass model, without the disturbance estimate."""
        th = self.theta2
        return t + th[:, 0] * (t - tm) + th[:, 1] * q + th[:, 2] + th[:, 3] * (oat - t) + th[:, 4] * cmv

    def _gain(self) -> np.ndarray:
        return self.theta2[:, 1] if self.p["mass_model"] else self.theta[:, 1]

    def _free2(self, zi: int, t1: float, q0: float) -> float:
        """Zone temperature at k+2 from its prediction t1 at k+1 under heat q0 (kW)."""
        if self.p["mass_model"]:
            th = self.theta2[zi]
            tm = self._tm1[zi]
            return (t1 + th[0] * (t1 - tm) + th[1] * q0 + th[2] + th[3] * (self._oat - t1)
                    + th[4] * self._cmv + self.dhat[zi])
        th = self.theta[zi]
        return t1 + th[0] * (t1 - 295.0) + th[1] * q0 + th[2] + self.dhat[zi]

    def _roll_steps(self, temps, maxflow, oat, t_ret, tw, target, steps_left) -> np.ndarray:
        """Steps each zone needs to reach target at the recovery airflow (mass model rollout).

        Starts from the heat already in the pipe; the heat commanded now acts in
        the step after. Zones that cannot get there within the time left (or
        roll_max) return more steps than are left.
        """
        p = self.p
        s_heat = 0.7 * t_ret + 0.3 * oat
        dis = min(p["discharge_max"], s_heat + p["reheat_eff"] * (max(tw, s_heat) - s_heat))
        cap = p["f_heat_rec"]
        n_max = int(min(p["roll_max"], steps_left + 1))
        need = np.full(self.nz, float(n_max) + 1.0)
        t = self._m2_step(temps, self.tm, self.prev_q, oat, 0.0) + self.dhat
        tm = self.tm + (temps - self.tm) / p["mass_n"]
        q = cap * maxflow * np.maximum(dis - temps, 0.0) * C_AIR / 1000.0
        if p["roll_mass"]:
            # The air is not enough: the slab must be warm enough that the daytime
            # airflow cap can hold the target once comfort time starts (steady
            # air temperature of the model at the target with comfort-time gains).
            th = self.theta2
            lam = np.maximum(-th[:, 0], 1e-3)
            q_day = p["f_heat_max"] * maxflow * max(dis - target, 0.0) * C_AIR / 1000.0
            tm_req = target - (th[:, 1] * q_day + th[:, 2] + th[:, 3] * (oat - target) + th[:, 4] + self.dhat) / lam
            tm_req = tm_req + p["roll_mass_k"]
        else:
            tm_req = np.full(self.nz, -np.inf)
        done = (t >= target) & (tm >= tm_req)
        need[done] = 1.0
        for j in range(2, n_max + 1):
            if done.all():
                break
            t_new = self._m2_step(t, tm, q, oat, 0.0) + self.dhat
            tm = tm + (t - tm) / p["mass_n"]
            q = cap * maxflow * np.maximum(dis - t, 0.0) * C_AIR / 1000.0
            t = t_new
            hit = (~done) & (t >= target) & (tm >= tm_req)
            need[hit] = j
            done |= hit
        return need

    def _predict(self, t: np.ndarray, q_prev: np.ndarray) -> np.ndarray:
        th = self.theta
        return t + th[:, 0] * (t - 295.0) + th[:, 1] * q_prev + th[:, 2] + self.dhat

    def _plan_ahu(self, mem, sat_c, temps_plan, t1, q_star, need_heat, need_cool,
                  maxflow, oat, t_ret, tw, lo) -> dict:
        """Plan one air handler for a given supply-air setpoint; estimate its cost.

        sat_c None means no mechanical cooling (setpoint at maximum, maximum
        recirculation). The cost is in reward units per step: electricity and
        gas weighted as the reward weights them, plus the comfort value of any
        cooling the zones asked for but could not get.
        """
        p = self.p
        if sat_c is None:
            r = 0.7
            mixed = 0.7 * t_ret + 0.3 * oat
            sat_sp = p["sat_max"]
            s = mixed
        else:
            if oat < t_ret - 0.5:
                r = min(0.7, max(0.0, (sat_c - oat) / max(t_ret - oat, 1e-3)))
            else:
                r = 0.7
            mixed = r * t_ret + (1 - r) * oat
            sat_sp = float(sat_c)
            s = min(mixed, sat_sp)
        n = len(mem)
        flow = np.zeros(n)
        dis = np.full(n, s)
        reheat = np.zeros(n, dtype=bool)
        tp = temps_plan[mem]
        mf = maxflow[mem]
        dis_heat = min(p["discharge_max"], s + p["reheat_eff"] * (max(tw, s) - s))
        for j, zi in enumerate(mem):
            if need_cool[zi]:
                dt_air = s - tp[j]
                flow[j] = q_star[zi] / dt_air if dt_air < -0.2 else mf[j]
            elif need_heat[zi]:
                dt_air = dis_heat - tp[j]
                if dt_air > 0.2:
                    # Heating maximum (as in G36 dual-maximum logic): more air
                    # than this mostly brings in outside air the coil must heat.
                    cap = p["f_heat_safety"] if self._boost[zi] else p["f_heat_max"]
                    if self._unocc and p["night_glide"]:
                        cap = max(cap, p["f_heat_rec"])
                    flow[j] = min(q_star[zi] / dt_air, cap * mf[j])
                    reheat[j] = True
                    dis[j] = dis_heat
                else:
                    flow[j] = mf[j]
        flow = np.clip(flow, 0.0, mf)
        if p["idle_aware"]:
            scale0 = math.sqrt(max(float(np.max(flow / mf)) ** 2, 0.1))
            for j, zi in enumerate(mem):
                if need_heat[zi] or need_cool[zi]:
                    continue
                f0 = p["f_min"] * scale0 * mf[j]
                q0 = f0 * (s - tp[j]) * C_AIR / 1000.0
                t2 = self._free2(zi, t1[zi], q0)
                if t2 < lo[zi] and dis_heat - tp[j] > 0.2:
                    need = (lo[zi] + p["aim_inside"] - t2) / self._gain()[zi] * 1000.0 / C_AIR
                    fl = (need + f0 * (s - tp[j])) / (dis_heat - tp[j])
                    flow[j] = float(np.clip(max(fl, f0), 0.0, mf[j]))
                    reheat[j] = True
                    dis[j] = dis_heat
        frac = flow / mf
        pfrac = max(float(np.max(frac)) ** 2, 0.1)   # P/2000, floor 200 Pa
        scale = math.sqrt(pfrac)
        dampers = np.clip(frac / scale, p["f_min"], 1.0)
        real = dampers * scale * mf
        total = float(np.sum(real))
        fan_kw = total * pfrac * 2000.0 / p["fan_eff"] * (1.0 + (1.0 - r)) / 1000.0
        chill_kw = total * C_AIR * max(0.0, mixed - s) / p["cop"] / 1000.0
        gas_kw = float(np.sum(real[reheat] * C_AIR * (dis[reheat] - s))) / 1000.0
        # Cooling asked for but not delivered, valued at the comfort weight.
        unmet = 0.0
        for j, zi in enumerate(mem):
            if need_cool[zi]:
                got = real[j] * (s - tp[j])
                short = max(0.0, got - q_star[zi])        # both negative when cooling
                unmet += short * C_AIR / 1000.0 * self._gain()[zi]
        k = max(1, self.n_ahu)
        cost = (p["w_elec"] * (fan_kw + chill_kw) + p["w_gas"] * gas_kw) / k             + p["w_comfort"] / max(1, self.nz) * unmet
        return dict(r=r, sat_sp=sat_sp, s=s, flow=real, dis=dis, reheat=reheat,
                    dampers=dampers, pfrac=pfrac, cost=cost, any_heat=bool(np.any(reheat)))

    def _risk_margins(self) -> tuple[np.ndarray, np.ndarray]:
        """Per-zone distance from the band edge that minimises expected cost.

        Holding a zone one kelvin further inside the band costs energy at the
        rate lam/g (kW per K, from the zone's own model) times the reward price
        of that energy; ending one kelvin outside costs the comfort weight.
        With the zone's one-step prediction error sigma (tracked online), the
        cost-optimal margin is sigma * z, where P(error > margin) equals the
        ratio of the two costs.
        """
        p = self.p
        lam = np.maximum(-self.theta[:, 0], 1e-3)
        g = np.maximum(self.theta[:, 1], 1e-3)
        kw_per_k = lam / g
        k = max(1, self.n_ahu)
        cost_out = p["w_comfort"] / max(1, self.nz)
        in_heat = kw_per_k * p["reheat_gas_factor"] * p["w_gas"] / k
        in_cool = kw_per_k * (1.0 / p["cop"] + p["fan_share"]) * p["w_elec"] / k
        sigma = p["sigma_mult"] * np.sqrt(self.err_var)
        m_h = sigma * _z_upper(np.clip(in_heat / cost_out, 1e-4, 0.999))
        m_c = sigma * _z_upper(np.clip(in_cool / cost_out, 1e-4, 0.999))
        return (np.clip(m_h, p["m_min"], p["m_max"]), np.clip(m_c, p["m_min"], p["m_max"]))

    def _recovery_hours(self, temps, maxflow, oat, t_ret) -> float:
        """Hours the slowest zone needs to reach its comfort target at full effort.

        Rolls each zone's identified model forward with the most heat (or
        cooling) its box can give under the heating-airflow cap, so the start
        time adapts to the building, the weather and how far zones have drifted.
        """
        p = self.p
        lo = self.comfort[0] + p["margin_heat"]
        hi = self.comfort[1] - p["margin_cool"]
        th = self.theta
        s_heat = 0.7 * t_ret + 0.3 * oat
        dis = min(p["discharge_max"], s_heat + p["reheat_eff"] * (p["water_heat"] - s_heat))
        t = temps.copy()
        need = (t < lo) | (t > hi)
        if not np.any(need):
            return 0.0
        steps = np.zeros(self.nz)
        for k in range(int(p["opt_start_max_h"] * 12)):
            heat = t < lo
            cool = t > hi
            if not np.any(heat | cool):
                break
            q = np.where(heat, p["f_heat_max"] * maxflow * (dis - t),
                         np.where(cool, maxflow * (p["sat_min"] - t), 0.0)) * C_AIR / 1000.0
            t = t + th[:, 0] * (t - 295.0) + th[:, 1] * q + th[:, 2]
            steps += (heat | cool)
        # One extra step for the actuation delay, then a safety factor.
        return (float(np.max(steps)) + 1.0) / 12.0 * p["opt_start_safety"]

    def _heat_rate(self, temps, maxflow, oat, t_ret, tw) -> np.ndarray:
        """Per-zone heating rate (K per step) at the recovery airflow cap.

        From the zone's identified model: the heat the box can deliver at the
        cap, times the zone gain, minus the zone's own drift.
        """
        p = self.p
        s_heat = 0.7 * t_ret + 0.3 * oat
        dis = min(p["discharge_max"], s_heat + p["reheat_eff"] * (max(tw, s_heat) - s_heat))
        q = p["f_heat_rec"] * maxflow * np.maximum(dis - temps, 0.0) * C_AIR / 1000.0
        if p["mass_model"] and p["m2_rate"]:
            rate = self._m2_step(temps, self.tm, q, oat, 0.0) - temps + self.dhat
        else:
            th = self.theta
            rate = th[:, 0] * (temps - 295.0) + th[:, 1] * q + th[:, 2] + self.dhat
        return np.clip(rate, 0.01, p["glide_rate_max"] / 12.0)

    def _coil_roots(self, plans, tw) -> dict | None:
        """sqrt(bar) at which each open reheat coil reaches its planned discharge (None: no pressure does).

        The coil closes the share water capacity / air capacity (at most 1) of the gap between the
        water and the air entering it, and an open valve passes Kv sqrt(dP) m3/h, so the coil that
        needs the most water sets the pump pressure.
        """
        p = self.p
        roots = {}
        for mem, plan in plans:
            s = plan["s"]
            gap = tw - s
            for j in np.flatnonzero(plan["reheat"]):
                if gap <= 0.5:
                    return None
                e = (plan["dis"][j] - s) / gap
                if e >= 0.98:
                    return None
                w_cap = p["dp_margin"] * e * plan["flow"][j] * C_AIR          # W/K the water must carry
                roots[int(mem[j])] = w_cap * 3600.0 / (p["dp_kv"] * 1000.0 * 4180.0)
        return roots

    def _cool_rate(self, temps, maxflow, oat=None) -> np.ndarray:
        """Per-zone cooling rate (K per step, positive) at the pull-down airflow.

        From the zone's identified model, with the coldest supply air at
        cool_rec_frac of the box maximum, minus the zone's own drift.
        """
        p = self.p
        q = p["cool_rec_frac"] * maxflow * np.minimum(p["sat_min"] - temps, 0.0) * C_AIR / 1000.0
        if p["mass_model"] and p["m2_rate"] and oat is not None:
            rate = -(self._m2_step(temps, self.tm, q, oat, 0.0) - temps + self.dhat)
        else:
            th = self.theta
            rate = -(th[:, 0] * (temps - 295.0) + th[:, 1] * q + th[:, 2] + self.dhat)
        return np.clip(rate, 0.01, p["cool_rate_max"] / 12.0)

    # ---------------------------------------------------------------- control
    def get_action(self, obs: np.ndarray) -> dict[str, np.ndarray]:
        p = self.p
        obs = np.asarray(obs, dtype=np.float64)
        temps = obs[self.z_t] * self.t_std + self.t_mean
        if p["glide_learn"] and self.prev_t is not None:
            # The step that just ended carried the heat commanded two steps ago;
            # learn from zones that were at full effort in both commands.
            sus = self._full & self._full2
            if np.any(sus):
                b_l = p["learn_beta"]
                obs_rate = np.clip(temps - self.prev_t, 0.0, p["glide_rate_max"] / 12.0)
                self.rec_rate = np.where(sus, (1 - b_l) * self.rec_rate + b_l * obs_rate, self.rec_rate)
        self._identify(temps, obs)
        oat = float(obs[self.oat_idx]) if self.oat_idx is not None else 290.0
        t_ret = float(np.mean(temps))
        tw_now = float(obs[self.water_obs]) if self.water_obs is not None else p["water_heat"]
        maxflow = np.where(self.z_maxflow_idx >= 0, obs[np.maximum(self.z_maxflow_idx, 0)], 2.0)
        maxflow = np.maximum(maxflow, 1e-3)
        hour, day = self._clock(obs)
        if self.cm_now is not None:
            self._calibrate_schedule(obs[self.cm_now] > 0.5, hour)
        h2c = self._hours_to_comfort(hour, day)
        if self.cm_now is not None:
            if obs[self.cm_now] > 0.5:
                h2c = 0.0
            elif h2c == 0.0:
                h2c = 99.0
        if (p["empty_day"] or p["empty_pm"]) and self.occ_obs is not None:
            h2c = self._empty_day(obs, h2c, hour, day)
        lead = p["lead_h"]
        if p["opt_start"] and 0.0 < h2c < 24.0:
            lead = max(lead, self._recovery_hours(temps, maxflow, oat, t_ret))
        occupied_mode = h2c <= lead
        if occupied_mode:
            if p["risk_margin"]:
                m_h, m_c = self._risk_margins()
            else:
                m_h = np.full(self.nz, p["margin_heat"])
                m_c = np.full(self.nz, p["margin_cool"])
            lo = self.comfort[0] + m_h
            hi = self.comfort[1] - m_c
        else:
            lo = np.full(self.nz, self.eco[0] + p["guard"])
            hi = np.full(self.nz, self.eco[1] - p["guard"])
        # 24-hour mean outside temperature (heating season or not).
        self.oat_avg = oat if self.oat_avg is None else self.oat_avg + (oat - self.oat_avg) / 288.0
        glide = bool(p["night_glide"]) and h2c > 0.0 and self.oat_avg < p["glide_oat"]
        if glide:
            # Heating side only (the cooling side keeps the band above): until
            # comfort time a zone may float down to a low floor, but never below
            # the temperature from which it can still reach its comfort target
            # in time at the rate it can really heat. This is the energy-optimal
            # start for a zone that loses heat to the outside: float, then
            # recover at full rate, just in time, zone by zone.
            lo = np.full(self.nz, self.eco[0] + p["glide_floor"])
            if h2c < 24.0 and p["glide_roll"] and p["mass_model"]:
                # Start each zone's recovery when a rollout of its own model
                # (slab included) at the recovery airflow needs about all the
                # time left; once started, it continues until comfort time.
                target = self.comfort[0] + p["margin_heat"] + p["aim_inside"]
                steps_left = max((h2c - p["glide_lead"]) * 12.0, 0.0)
                need = self._roll_steps(temps, maxflow, oat, t_ret, tw_now, target, steps_left)
                self._roll_on |= need >= p["roll_safety"] * steps_left
                lo = np.where(self._roll_on, target, lo)
            elif h2c < 24.0:
                target = self.comfort[0] + p["margin_heat"] + p["aim_inside"]
                rate = self._heat_rate(temps, maxflow, oat, t_ret, tw_now)
                if p["glide_learn"]:
                    rate = np.minimum(rate, self.rec_rate)
                # Two steps for the delay; glide_lead hours to warm the mass too.
                steps_left = max((h2c - p["glide_lead"]) * 12.0 - 2.0, 0.0)
                lo = np.maximum(lo, np.minimum(target - p["glide_safety"] * rate * steps_left, target))
        else:
            self._roll_on[:] = False
        self._unocc = glide
        # Outside air alone can bring the zones to their target: cooling is free.
        free = bool(p["cool_free"]) and oat < self.comfort[1] - p["margin_cool"] - p["aim_inside"] - p["cool_free_dt"]
        if p["cool_guard"] and h2c == 0.0:
            b_o = p["cool_guard_beta"]
            self.over = (1 - b_o) * self.over + b_o * np.maximum(temps - self.comfort[1], 0.0)
        if p["cool_glide"] and h2c > 0.0 and self.oat_avg > p["cool_glide_oat"] and not free:
            hi_keep = hi
            # Cooling side: until comfort time a zone may float up to a high
            # ceiling, but never above the temperature from which it can still
            # be pulled down to its comfort target in time at the rate it can
            # really cool. Less heat leaks in through a warmer envelope.
            hi = np.full(self.nz, self.eco[1] + p["cool_ceiling"])
            if h2c < 24.0:
                target = self.comfort[1] - p["margin_cool"] - p["aim_inside"]
                rate = self._cool_rate(temps, maxflow, oat)
                steps_left = max((h2c - p["glide_lead"]) * 12.0 - 2.0, 0.0)
                hi = np.minimum(hi, np.maximum(target + p["cool_safety"] * rate * steps_left, target))
            if p["cool_guard"]:
                hi = np.where(self.over > p["cool_guard_max"], hi_keep, hi)
        if p["precool"] and 0.0 < h2c <= p["precool_h"] and self.oat_avg > p["precool_oat"]:
            hi = np.minimum(hi, self.comfort[1] - p["margin_cool"] - p["precool_k"])

        cmv = float(obs[self.cm_now] > 0.5) if self.cm_now is not None else float(h2c == 0.0)
        if p["mass_model"]:
            # The slab barely moves in one step; internal gains as they are now.
            self._tm1 = self.tm + (temps - self.tm) / p["mass_n"]
            self._cmv, self._oat = cmv, oat
            t1 = self._m2_step(temps, self.tm, self.prev_q, oat, cmv) + self.dhat
            if not p["delay_comp"]:
                t1 = temps.copy()
            t2_free = self._m2_step(t1, self._tm1, 0.0, oat, cmv) + self.dhat
        else:
            # One-step delay: T[k+1] is already decided by the heat in the pipe.
            if p["delay_comp"]:
                t1 = self._predict(temps, self.prev_q)
            else:
                # Ablation: plan as if heat acted within the same step.
                t1 = temps.copy()
            # With no heat from now on, where would the zone be at k+2?
            t2_free = self._predict(t1, np.zeros(self.nz))
        need_heat = t2_free < lo
        need_cool = t2_free > hi
        aim = np.where(need_heat, lo + p["aim_inside"], np.where(need_cool, hi - p["aim_inside"], t2_free))
        goal = t2_free + p["damping"] * (aim - t2_free)
        # Only in comfort time: outside it a zone below its floor costs nothing and the droop saves energy.
        of = p["offset_free"] if h2c == 0.0 else 0
        if of == 1:
            # Damp only the move from where the zone is going (t1), not the heat that holds it there. Damping the
            # whole gap from the free trajectory leaves a steady droop of about (1 - damping) / damping times the
            # zone's loss per step: large in high-loss zones in deep cold (docs/STRESS_TEST.md, building 7 in Duluth).
            base = np.where(need_heat, np.minimum(t1, aim), np.where(need_cool, np.maximum(t1, aim), t2_free))
            goal = base + p["damping"] * (aim - base)
        elif of == 2:
            # The droop is allowed only down to the band edge: the goal is never below a damped move from
            # min(t1, lo) (above max(t1, hi) when cooling). Mild loads change nothing; large ones no longer push
            # the zone out of its band.
            b_h = np.minimum(t1, lo)
            b_c = np.maximum(t1, hi)
            goal = np.where(need_heat, np.maximum(goal, b_h + p["damping"] * (aim - b_h)),
                            np.where(need_cool, np.minimum(goal, b_c + p["damping"] * (aim - b_c)), goal))
        elif of == 3:
            # Only a goal outside the comfort band itself is raised (lowered) to just inside it: the margins
            # (margin_heat, margin_cool) still absorb the droop under mild loads, as tuned.
            c_lo = np.minimum(self.comfort[0] + p["aim_inside"], aim)
            c_hi = np.maximum(self.comfort[1] - p["aim_inside"], aim)
            goal = np.where(need_heat, np.maximum(goal, c_lo), np.where(need_cool, np.minimum(goal, c_hi), goal))
        g = self._gain()
        q_star_kw = np.where(need_heat | need_cool, (goal - t2_free) / g, 0.0)
        # Safety net, independent of the model: a zone well outside its band
        # gets the most heat or cooling the box can give.
        far_cold = temps < lo - p["safety_k"]
        far_warm = temps > hi + p["safety_k"]
        if p["safety_pred"]:
            # Without this the net fires on a zone the heat already in the pipe
            # is about to bring back, and full effort then overshoots (v8).
            if p["safety_pred"] == 1:
                far_cold = far_cold & (t1 < lo - p["safety_k"])
            far_warm = far_warm & (t1 > hi + p["safety_k"])
        self._far_cold = far_cold
        # Zones already below their band get a higher heating-airflow cap.
        self._boost = temps < lo - p["boost_k"]
        need_heat = need_heat | far_cold
        need_cool = (need_cool | far_warm) & ~far_cold
        q_star_kw = np.where(far_cold, 1e3, np.where(far_warm, -1e3, q_star_kw))
        # Heat in kW -> m3/s * K for the airflow planning below.
        q_star = q_star_kw * 1000.0 / C_AIR
        temps_plan = t1

        cont = np.zeros(self.n_cont, dtype=np.float64)
        disc = np.zeros(self.n_disc, dtype=np.int32)
        flow_cmd = np.zeros(self.nz)
        q_plan = np.zeros(self.nz)
        dis_plan = np.zeros(self.nz)
        reheat_on = np.zeros(self.nz, dtype=bool)
        any_heat = False
        tw = float(obs[self.water_obs]) if self.water_obs is not None else p["water_heat"]
        plans = []

        for a, mem in enumerate(self.ahu_members):
            if not len(mem):
                continue
            nh, nc = need_heat[mem], need_cool[mem]
            active = bool(np.any(nh) or np.any(nc))
            disc[a] = 1 if active else 0
            if not active:
                cont[self.press_idx[a]] = -1.0
                cont[self.temp_idx[a]] = 1.0
                cont[self.recirc_idx[a]] = 1.0
                for zi in mem:
                    if self.z_damper[zi] >= 0:
                        cont[self.z_damper[zi]] = 2 * p["f_min"] - 1
                    if self.z_reheat[zi] >= 0:
                        cont[self.z_reheat[zi]] = -1.0
                continue

            mixed_max_recirc = 0.7 * t_ret + 0.3 * oat
            if np.any(nc):
                if p["sat_econ"]:
                    top = min(mixed_max_recirc, p["sat_econ_max"])
                    cands = list(np.arange(p["sat_min"], top + 1e-6, p["sat_econ_step"])) or [p["sat_min"]]
                else:
                    zc = mem[nc]
                    s_need = float(np.min(temps_plan[zc] + q_star[zc] / maxflow[zc]))
                    cands = [min(max(s_need, p["sat_min"]), mixed_max_recirc)]
            else:
                cands = [None]
            best = None
            for sat_c in cands:
                plan = self._plan_ahu(mem, sat_c, temps_plan, t1, q_star, need_heat, need_cool,
                                      maxflow, oat, t_ret, tw, lo)
                if best is None or plan["cost"] < best["cost"]:
                    best = plan
            any_heat = any_heat or best["any_heat"]
            plans.append((mem, best))
            reheat_on[mem] = best["reheat"]
            flow_cmd[mem] = best["flow"]
            dis_plan[mem] = best["dis"]
            q_plan[mem] = best["flow"] * (best["dis"] - temps_plan[mem]) * C_AIR / 1000.0
            self.prev_s[a] = best["s"]
            cont[self.press_idx[a]] = 2 * best["pfrac"] - 1
            cont[self.temp_idx[a]] = 2 * (best["sat_sp"] - 285.0) / 20.0 - 1
            cont[self.recirc_idx[a]] = 2 * best["r"] - 1
            for j, zi in enumerate(mem):
                if self.z_damper[zi] >= 0:
                    cont[self.z_damper[zi]] = 2 * best["dampers"][j] - 1
                if self.z_reheat[zi] >= 0:
                    cont[self.z_reheat[zi]] = 1.0 if best["reheat"][j] else -1.0

        self._no_heat = 0 if any_heat else self._no_heat + 1
        if self.water_idx:
            idle = not any_heat and self._no_heat >= p["water_idle_h"] * 12.0
            tw_sp = p["water_idle"] if idle else p["water_heat"]
            cont[self.water_idx[0]] = 2 * (tw_sp - 310.0) / 40.0 - 1
        if self.dp_idx is not None:
            if p["dp_reset"] and any_heat:
                roots = self._coil_roots(plans, tw)
                if roots is None:
                    dp_bar = p["dp_max_bar"]
                else:
                    dp_bar = min(max(p["dp_min_bar"], max(roots.values(), default=0.0) ** 2), p["dp_max_bar"])
                    if p["dp_reset"] == 2:
                        for zi, root in roots.items():
                            if self.z_reheat[zi] >= 0:
                                v = min(1.0, max(p["dp_valve_min"], root / math.sqrt(dp_bar)))
                                cont[self.z_reheat[zi]] = 2.0 * v - 1.0
                cont[self.dp_idx] = 2.0 * dp_bar / p["dp_max_bar"] - 1.0
            else:
                cont[self.dp_idx] = p["dp_heat"] if any_heat else -1.0
        if self.pump_disc >= self.n_ahu:
            disc[self.pump_disc] = 1 if any_heat else 0

        if p["glide_learn"]:
            s_heat = 0.7 * t_ret + 0.3 * oat
            dis_rec = min(p["discharge_max"], s_heat + p["reheat_eff"] * (max(tw, s_heat) - s_heat))
            q_cap = p["f_heat_rec"] * maxflow * np.maximum(dis_rec - temps_plan, 0.0) * C_AIR / 1000.0
            self._full2 = self._full
            self._full = glide & (q_cap > 0.5) & (q_plan >= p["learn_full"] * q_cap)
        self.prev_t = temps
        self.prev_oat, self.prev_cm = oat, cmv
        self.prev_q2 = self.prev_q
        self.prev_q = q_plan
        self.prev_flow_cmd = flow_cmd
        self.prev_ahu_on = disc[: self.n_ahu].astype(bool)
        self.prev_dis = dis_plan
        self.step += 1
        return {"continuous_action": np.clip(cont, -1, 1).astype(np.float32),
                "discrete_action": disc}


def _z_upper(r: np.ndarray) -> np.ndarray:
    """z such that P(N(0,1) > z) = r (Abramowitz and Stegun 26.2.23)."""
    r = np.asarray(r, dtype=float)
    q = np.where(r < 0.5, r, 1 - r)
    t = np.sqrt(-2.0 * np.log(q))
    z = t - (2.515517 + 0.802853 * t + 0.010328 * t * t) / (
        1 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t ** 3)
    return np.where(r < 0.5, z, -z)


def _num(name: str) -> int:
    digits = "".join(ch for ch in name if ch.isdigit())
    return int(digits) if digits else 0
