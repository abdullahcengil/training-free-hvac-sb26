"""Build the size-gate candidate file (docs/SIZEGATE.md): the frozen v14/v15 file (frozen/zonal_v14f.py) plus the
size_gate option, nothing else.

With size_gate 0 (the default) every expression computes exactly what v15 computes (the margin and glide safety are
read into locals first), so the file must give v15's actions bit for bit; sb.make_v16sz --check runs both on the
first 576 steps of a training scenario and compares every reward term.

    python -m sb.make_v16sz frozen/zonal_v14f.py D:/SmartBuildings_data/frozen/zonal_v16dev_sz.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PARAM_OLD = ("    offset_free=0,         # 1: damp only the move from the next predicted temperature, not the heat that "
             "holds the\n"
             "                           # zone (no steady droop under large losses or gains; stress test, 23 Oct)\n")
PARAM_NEW = PARAM_OLD + (
    "    size_gate=0,           # 1: once a day, if the median zone's identified 1/g (heat per kelvin of room air: the\n"
    "                           # room's size as the controller sees it) is above sg_thr, heat a little less: energy\n"
    "                           # is normalised per air handler and comfort per person (docs/SIZEGATE.md)\n"
    "    sg_thr=5.0,            # K^-1 kW step; shipped training buildings: medians 3.4-3.8 after two days\n"
    "    sg_after=288,          # steps before the first check (the zone models need a day of data)\n"
    "    sg_margin_heat=0.30,   # margin_heat while the gate is on\n"
    "    sg_glide_safety=0.80,  # glide_safety while the gate is on\n")
INIT_OLD = "        self.over = np.zeros(self.nz)   # smoothed occupied overshoot above the comfort band, K (v10)\n"
INIT_NEW = INIT_OLD + (
    "        self._sg_n = 0                  # steps seen (size_gate)\n"
    "        self._sg_on = False             # the building looks large to its own zone models (size_gate)\n")
IDENT_OLD = "        self._identify(temps, obs)\n"
IDENT_NEW = IDENT_OLD + (
    "        if p[\"size_gate\"] and p[\"mass_model\"]:\n"
    "            # Checked once a day, so the settings change at most daily (the check falls at the same clock time).\n"
    "            self._sg_n += 1\n"
    "            if self._sg_n >= p[\"sg_after\"] and self._sg_n % 288 == 0:\n"
    "                inv_g = 1.0 / np.maximum(self.theta2[:, 1], 1e-6)\n"
    "                self._sg_on = bool(np.median(inv_g) > p[\"sg_thr\"])\n"
    "        m_heat = p[\"sg_margin_heat\"] if self._sg_on else p[\"margin_heat\"]\n"
    "        g_safe = p[\"sg_glide_safety\"] if self._sg_on else p[\"glide_safety\"]\n")
SUBS = [
    ('                m_h = np.full(self.nz, p["margin_heat"])\n',
     '                m_h = np.full(self.nz, m_heat)\n', 1),
    ('                target = self.comfort[0] + p["margin_heat"] + p["aim_inside"]\n',
     '                target = self.comfort[0] + m_heat + p["aim_inside"]\n', 2),
    ('                lo = np.maximum(lo, np.minimum(target - p["glide_safety"] * rate * steps_left, target))\n',
     '                lo = np.maximum(lo, np.minimum(target - g_safe * rate * steps_left, target))\n', 1),
]


def build(src: Path, dst: Path) -> None:
    text = src.read_bytes().decode("utf-8")
    crlf = "\r\n" in text
    text = text.replace("\r\n", "\n")
    for old, new, n in [(PARAM_OLD, PARAM_NEW, 1), (INIT_OLD, INIT_NEW, 1), (IDENT_OLD, IDENT_NEW, 1), *SUBS]:
        c = text.count(old)
        if c != n:
            raise SystemExit(f"expected {n} occurrence(s), found {c}: {old.strip()[:70]}")
        text = text.replace(old, new)
    if crlf:
        text = text.replace("\n", "\r\n")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(text.encode("utf-8"))
    print("wrote", dst)


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
