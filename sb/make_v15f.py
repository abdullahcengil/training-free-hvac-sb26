"""Build the v15 candidate policy file: the frozen v14 file (zonal_v14f.py) plus two options, nothing else.

- glide_sus 1 (docs/BIGDEV.md, candidate A): the night glide and the cooling glide use the slower of the zone's
  one-step rate and its slab-limited sustained rate whenever the target lies beyond the air's quasi-steady
  temperature relative to the slab (large rooms on a 2 m3/s box, full-size buildings).
- glide_h (candidate D): hours before comfort time from which the glide floors follow the zone's rate (v14: 24).
Defaults keep v14 bit for bit. The gain bound (candidate B) is the existing m2_lo parameter.

    python -m sb.make_v15f D:/SmartBuildings_data/frozen/zonal_v14f.py D:/SmartBuildings_data/frozen/zonal_v15dev_a.py
"""

from __future__ import annotations

import sys
from pathlib import Path

EDITS = [
    # Parameters.
    ("    glide_safety=0.7,      # fraction of the identified heating rate the glide path assumes\n",
     "    glide_safety=0.7,      # fraction of the identified heating rate the glide path assumes\n"
     "    glide_sus=0,           # 1: the glide paths assume the slower of the one-step rate and the slab-limited\n"
     "                           # sustained rate when the target lies beyond the air's quasi-steady temperature\n"
     "                           # (large rooms on the same box; full-size buildings, docs/BIGDEV.md)\n"
     "    glide_h=24.0,          # hours before comfort time from which the glide floors follow the zone's rate\n"),
    # Heating rate: slab-limited when the target is beyond the quasi-steady air temperature.
    ("            rate = th[:, 0] * (temps - 295.0) + th[:, 1] * q + th[:, 2] + self.dhat\n"
     "        return np.clip(rate, 0.01, p[\"glide_rate_max\"] / 12.0)\n",
     "            rate = th[:, 0] * (temps - 295.0) + th[:, 1] * q + th[:, 2] + self.dhat\n"
     "        if p[\"glide_sus\"] and p[\"mass_model\"]:\n"
     "            target = self.comfort[0] + p[\"margin_heat\"] + p[\"aim_inside\"]\n"
     "            q_t = p[\"f_heat_rec\"] * maxflow * max(dis - target, 0.0) * C_AIR / 1000.0\n"
     "            rate = np.minimum(rate, self._sus_rate(q_t, oat, target, 1.0))\n"
     "        return np.clip(rate, 0.01, p[\"glide_rate_max\"] / 12.0)\n"),
    # Cooling rate: the same rule with the pull-down airflow.
    ("            rate = -(th[:, 0] * (temps - 295.0) + th[:, 1] * q + th[:, 2] + self.dhat)\n"
     "        return np.clip(rate, 0.01, p[\"cool_rate_max\"] / 12.0)\n",
     "            rate = -(th[:, 0] * (temps - 295.0) + th[:, 1] * q + th[:, 2] + self.dhat)\n"
     "        if p[\"glide_sus\"] and p[\"mass_model\"] and oat is not None:\n"
     "            target = self.comfort[1] - p[\"margin_cool\"] - p[\"aim_inside\"]\n"
     "            q_t = p[\"cool_rec_frac\"] * maxflow * min(p[\"sat_min\"] - target, 0.0) * C_AIR / 1000.0\n"
     "            rate = np.minimum(rate, self._sus_rate(q_t, oat, target, -1.0))\n"
     "        return np.clip(rate, 0.01, p[\"cool_rate_max\"] / 12.0)\n"
     "\n"
     "    def _sus_rate(self, q_t, oat, target, sign) -> np.ndarray:\n"
     "        \"\"\"Slab-limited rate (K/step, positive towards the target) for zones the fast air dynamics cannot take there.\n"
     "\n"
     "        Under constant heat q the mass model's air settles at T_eq = T_m + (g q + c + b (T_oa - T_m) + dhat) /\n"
     "        (lam + b) above the slab; the slab then follows the air with a lag of mass_n steps and the air follows the\n"
     "        slab by lam / (lam + b). Where the target lies beyond T_eq, that is the rate at which the zone can get\n"
     "        there; elsewhere the one-step rate stands (returned as +inf here). sign: +1 heating, -1 cooling.\n"
     "        \"\"\"\n"
     "        th = self.theta2\n"
     "        lam = np.maximum(-th[:, 0], 1e-3)\n"
     "        b = th[:, 3]\n"
     "        d_eq = (th[:, 1] * q_t + th[:, 2] + b * (oat - self.tm) + self.dhat) / (lam + b)\n"
     "        beyond = sign * (target - (self.tm + d_eq)) > 0.0\n"
     "        sus = sign * lam / (lam + b) * d_eq / self.p[\"mass_n\"]\n"
     "        return np.where(beyond, sus, np.inf)\n"),
    # Glide horizons (heating: roll and plain branches; cooling).
    ("            if h2c < 24.0 and p[\"glide_roll\"] and p[\"mass_model\"]:\n",
     "            if h2c < p[\"glide_h\"] and p[\"glide_roll\"] and p[\"mass_model\"]:\n"),
    ("            elif h2c < 24.0:\n                target = self.comfort[0] + p[\"margin_heat\"] + p[\"aim_inside\"]\n",
     "            elif h2c < p[\"glide_h\"]:\n                target = self.comfort[0] + p[\"margin_heat\"] + p[\"aim_inside\"]\n"),
    ("            if h2c < 24.0:\n                target = self.comfort[1] - p[\"margin_cool\"] - p[\"aim_inside\"]\n",
     "            if h2c < p[\"glide_h\"]:\n                target = self.comfort[1] - p[\"margin_cool\"] - p[\"aim_inside\"]\n"),
]


def main(src: str, dst: str) -> None:
    s = Path(src).read_text(encoding="utf-8")
    for old, new in EDITS:
        assert s.count(old) == 1, old
        s = s.replace(old, new)
    assert not Path(dst).exists(), f"{dst} exists"
    Path(dst).write_text(s, encoding="utf-8")
    print("wrote", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
