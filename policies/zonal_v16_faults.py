"""Robustness test only, never submitted (docs/SENSOR_FAULTS.md): the frozen v16 file, unchanged (its hash is checked),
reading zone temperatures through faulty sensors. The true temperature still decides the comfort term.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np

_F = Path(__file__).resolve().parents[1] / "frozen" / "zonal_v16f.py"
assert hashlib.sha256(_F.read_bytes()).hexdigest().startswith("af9c0d2bff35568b"), "frozen v16 file changed"
_spec = importlib.util.spec_from_file_location("zonal_v16f_base", _F)
_base = importlib.util.module_from_spec(_spec)
sys.modules["zonal_v16f_base"] = _base
_spec.loader.exec_module(_base)


class FaultPolicy(_base.TransferPolicy):
    """v16 behind a sensor fault: none, noise (K per step), bias (K per zone), lag (extra steps), stuck (share of zones)."""

    def __init__(self, *args, fault: str = "none", level: float = 0.0, fault_seed: int = 8, **kw):
        super().__init__(*args, **kw)
        self._fault, self._level = fault, level
        self._rng = np.random.default_rng(fault_seed)
        self._bias = self._rng.normal(0.0, level, self.nz) if fault == "bias" else None
        self._stuck = self._rng.random(self.nz) < level if fault == "stuck" else None
        self._first = None
        self._queue: list[np.ndarray] = []

    def get_action(self, obs: np.ndarray) -> dict[str, np.ndarray]:
        obs = np.array(obs, dtype=np.float64)
        t = obs[self.z_t] * self.t_std + self.t_mean
        if self._fault == "noise":
            t = t + self._rng.normal(0.0, self._level, self.nz)
        elif self._fault == "bias":
            t = t + self._bias
        elif self._fault == "lag":
            self._queue.append(t.copy())
            t = self._queue[0]
            if len(self._queue) > int(self._level):
                self._queue.pop(0)
        elif self._fault == "stuck":
            if self._first is None:
                self._first = t.copy()
            t = np.where(self._stuck, self._first, t)
        obs[self.z_t] = (t - self.t_mean) / self.t_std
        return super().get_action(obs)
