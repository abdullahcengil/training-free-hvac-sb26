"""Cold-start test only, never submitted (docs/COLD_START.md): the frozen v16 file, loaded unchanged (its hash is
checked), restarted at one given step. At that step the whole policy object is re-created: the five numbers of every
zone return to their priors, the covariance to its start value, the disturbance estimate to zero, the slab node to the
next reading, and everything the controller remembers (heat in the pipe, schedule alignment, 24-hour mean outside
temperature) to its start-up value. With cold_step -1 it never restarts and computes what v16 computes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

_F = Path(__file__).resolve().parents[1] / "frozen" / "zonal_v16f.py"
assert hashlib.sha256(_F.read_bytes()).hexdigest().startswith("af9c0d2bff35568b"), "frozen v16 file changed"
_spec = importlib.util.spec_from_file_location("zonal_v16f_base_cold", _F)
_base = importlib.util.module_from_spec(_spec)
sys.modules["zonal_v16f_base_cold"] = _base
_spec.loader.exec_module(_base)


class ColdStartPolicy(_base.TransferPolicy):
    """v16, re-created from scratch at step cold_step (counted from the start of the run)."""

    def __init__(self, building_meta_data: Mapping[str, Any], action_spec: Any, cold_step: int = -1,
                 **params: float) -> None:
        self._cold_args = (building_meta_data, action_spec, dict(params))
        self._cold_step = int(cold_step)
        self._cold_n = 0
        super().__init__(building_meta_data, action_spec, **params)

    def get_action(self, obs: np.ndarray) -> dict[str, np.ndarray]:
        if self._cold_n == self._cold_step:
            meta, spec, params = self._cold_args
            _base.TransferPolicy.__init__(self, meta, spec, **params)
        self._cold_n += 1
        return super().get_action(obs)
