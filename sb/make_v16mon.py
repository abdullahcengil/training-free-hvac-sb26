"""Build the first-work-day variant (docs/MONDAY.md): the frozen v16 file plus mon_mode and its settings.

mon_mode 0 (default) leaves v16 unchanged (known-answer check). 1: when nobody has been in the building for more than
mon_idle_h hours (a weekend or a holiday), the night before the next comfort period and that whole comfort period use
mon_safety, mon_floor and mon_margin in place of glide_safety, glide_floor and margin_heat.

    python -m sb.make_v16mon D:/SmartBuildings_data/frozen/zonal_v16f.py policies/zonal_v16mon.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPL = [
    ("    glide_oat=400.0,       # K: glide only while the 24-hour mean outside temperature is below this\n",
     "    glide_oat=400.0,       # K: glide only while the 24-hour mean outside temperature is below this\n"
     "    mon_mode=0,            # 1: other glide and margin settings after a weekend or holiday (docs/MONDAY.md)\n"
     "    mon_idle_h=24.0,       # hours without anybody in that make the next comfort period a first work day\n"
     "    mon_safety=0.6606,     # glide_safety for that night and day\n"
     "    mon_floor=-16.0,       # glide_floor for that night and day\n"
     "    mon_margin=0.3,        # margin_heat for that night and day\n"),
    ("        self.prev_ahu_on = np.zeros(self.n_ahu, dtype=bool)\n",
     "        self.prev_ahu_on = np.zeros(self.n_ahu, dtype=bool)\n"
     "        self._last_occ = None\n"
     "        self._mon = True\n"),
    ("        if (p[\"empty_day\"] or p[\"empty_pm\"]) and self.occ_obs is not None:\n"
     "            h2c = self._empty_day(obs, h2c, hour, day)\n",
     "        if (p[\"empty_day\"] or p[\"empty_pm\"]) and self.occ_obs is not None:\n"
     "            h2c = self._empty_day(obs, h2c, hour, day)\n"
     "        if p[\"mon_mode\"] and self.occ_obs is not None:\n"
     "            if float(obs[self.occ_obs]) > self.occ_zero + 1e-3:\n"
     "                self._last_occ = self.step\n"
     "            idle_h = 99.0 if self._last_occ is None else (self.step - self._last_occ) / 12.0\n"
     "            if h2c > 0.0:\n"
     "                self._mon = idle_h > p[\"mon_idle_h\"]\n"
     "            if self._mon:\n"
     "                p = dict(p, glide_safety=p[\"mon_safety\"], glide_floor=p[\"mon_floor\"],\n"
     "                         margin_heat=p[\"mon_margin\"])\n"),
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
