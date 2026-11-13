"""Build the per-zone learned setback variant (docs/ADAPT_START.md): the frozen v16 file plus one option, glide_adapt.

Each zone has a setback level a in [0, 1]: level 1 uses glide_safety / glide_floor as given, level 0 uses ga_gs0 /
ga_gf0, linear between. After the first ga_h hours of each comfort period, a zone whose mean deficit below the comfort
band exceeded ga_tol drops by ga_down; otherwise it rises by ga_up. With glide_adapt 0 every new line is skipped
(known-answer check K1); with ga_init 1 and no steps the level stays 1 and the given settings are used exactly (K2).

    python -m sb.make_v17ad D:/SmartBuildings_data/frozen/zonal_v16f.py policies/zonal_v17ad.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPL = [
    ("    glide_oat=400.0,       # K: glide only while the 24-hour mean outside temperature is below this\n",
     "    glide_oat=400.0,       # K: glide only while the 24-hour mean outside temperature is below this\n"
     "    glide_adapt=0,         # 1: each zone learns its setback level from its own morning comfort deficits\n"
     "                           # (docs/ADAPT_START.md); 0: v16 exactly\n"
     "    ga_gs0=0.6606,         # glide_safety at level 0 (v16)\n"
     "    ga_gf0=-16.0,          # glide_floor at level 0 (v16)\n"
     "    ga_h=3.0,              # hours of comfort time over which the morning deficit is measured\n"
     "    ga_tol=0.02,           # K, mean deficit below the comfort band that counts as a missed morning\n"
     "    ga_down=0.5,           # level drop after a missed morning\n"
     "    ga_up=0.25,            # level rise after a clean morning\n"
     "    ga_init=0.5,           # starting level\n"),
    ("        self._roll_on = np.zeros(self.nz, dtype=bool)   # zones whose recovery has started tonight\n",
     "        self._roll_on = np.zeros(self.nz, dtype=bool)   # zones whose recovery has started tonight\n"
     "        self._ga_a = np.full(self.nz, float(self.p[\"ga_init\"]))   # setback level per zone (glide_adapt)\n"
     "        self._ga_n = 0                                  # steps into the current comfort period\n"
     "        self._ga_d = np.zeros(self.nz)                  # summed deficit below the comfort band\n"),
    ("        lead = p[\"lead_h\"]\n",
     "        if p[\"glide_adapt\"]:\n"
     "            # Score this morning per zone: mean K below the comfort band over the first ga_h hours.\n"
     "            if h2c == 0.0:\n"
     "                self._ga_n += 1\n"
     "                m = int(round(p[\"ga_h\"] * 12))\n"
     "                if self._ga_n <= m:\n"
     "                    self._ga_d = self._ga_d + np.maximum(self.comfort[0] - temps, 0.0)\n"
     "                if self._ga_n == m:\n"
     "                    bad = self._ga_d / m > p[\"ga_tol\"]\n"
     "                    self._ga_a = np.clip(np.where(bad, self._ga_a - p[\"ga_down\"], self._ga_a + p[\"ga_up\"]),\n"
     "                                         0.0, 1.0)\n"
     "            else:\n"
     "                self._ga_n = 0\n"
     "                self._ga_d = np.zeros(self.nz)\n"
     "        lead = p[\"lead_h\"]\n"),
    ("            lo = np.full(self.nz, self.eco[0] + p[\"glide_floor\"])\n",
     "            if p[\"glide_adapt\"]:\n"
     "                # Level 1: the given settings exactly; level 0: v16's.\n"
     "                gs = p[\"glide_safety\"] - (1.0 - self._ga_a) * (p[\"glide_safety\"] - p[\"ga_gs0\"])\n"
     "                gf = p[\"glide_floor\"] - (1.0 - self._ga_a) * (p[\"glide_floor\"] - p[\"ga_gf0\"])\n"
     "                lo = self.eco[0] + gf\n"
     "            else:\n"
     "                gs = p[\"glide_safety\"]\n"
     "                lo = np.full(self.nz, self.eco[0] + p[\"glide_floor\"])\n"),
    ("                lo = np.maximum(lo, np.minimum(target - p[\"glide_safety\"] * rate * steps_left, target))\n",
     "                lo = np.maximum(lo, np.minimum(target - gs * rate * steps_left, target))\n"),
]


def build(src: Path, dst: Path) -> None:
    text = src.read_bytes().decode("utf-8")
    crlf = "\r\n" in text
    text = text.replace("\r\n", "\n")
    for old, new in REPL:
        c = text.count(old)
        if c != 1:
            raise SystemExit(f"expected 1 occurrence, found {c}: {old.strip()[:70]}")
        text = text.replace(old, new)
    if crlf:
        text = text.replace("\n", "\r\n")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(text.encode("utf-8"))
    print("wrote", dst)


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
