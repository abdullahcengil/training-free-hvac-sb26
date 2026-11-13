"""Ablation only, never submitted (docs/TRANSFER_ABLATION.md): v16 with the five numbers of each zone's model frozen
at their priors, while the per-zone disturbance estimate is still learned online. Everything else is the frozen v16
file, loaded unchanged (its hash is checked). With dist_beta 0 this policy computes what v16 with rls 0 computes (the
known-answer check of the ablation).
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


class OffsetOnlyPolicy(_base.TransferPolicy):
    """v16, but the model's five numbers stay at their priors; only the disturbance estimate adapts."""

    def _identify_m2(self, temps: np.ndarray) -> None:
        p = self.p
        if self.tm is None:
            self.tm = temps.copy()
            return
        if self.prev_t is None:
            return
        tm_prev = self.tm
        phi = np.stack([self.prev_t - tm_prev, self.prev_q2, np.ones(self.nz),
                        self.prev_oat - self.prev_t, np.full(self.nz, self.prev_cm)], axis=1)
        err = temps - self.prev_t - np.einsum("ni,ni->n", phi, self.theta2)
        if p["dist_obs"]:
            b_d = p["dist_beta"]
            self.dhat = np.clip((1 - b_d) * self.dhat + b_d * err, -p["dist_max"], p["dist_max"])
        self.tm = tm_prev + (self.prev_t - tm_prev) / p["mass_n"]
