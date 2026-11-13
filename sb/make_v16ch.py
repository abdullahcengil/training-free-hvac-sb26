"""Build the cool-hold candidate file (docs/CHATTER.md): the frozen v14/v15 file (frozen/zonal_v14f.py) plus the
cool_hold option, nothing else.

With cool_hold 0 (the default) the new block is skipped, so the file gives v15's actions bit for bit (checked by
running both on the first 576 steps of a training scenario and comparing every reward term).

    python -m sb.make_v16ch frozen/zonal_v14f.py D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PARAM_OLD = ("    offset_free=0,         # 1: damp only the move from the next predicted temperature, not the heat that "
             "holds the\n"
             "                           # zone (no steady droop under large losses or gains; stress test, 23 Oct)\n")
PARAM_NEW = PARAM_OLD + (
    "    cool_hold=0,           # steps after a zone was last asked for heat in which it is not cooled (0: off). The\n"
    "                           # reading lags a step, and a small, fast zone that a heat pulse sent over its band falls\n"
    "                           # back by itself; cooling it then starts a heating-cooling limit cycle (docs/CHATTER.md)\n")
INIT_OLD = "        self.over = np.zeros(self.nz)   # smoothed occupied overshoot above the comfort band, K (v10)\n"
INIT_NEW = INIT_OLD + (
    "        self._since_heat = np.full(self.nz, 99)  # steps since each zone was last asked for heat (cool_hold)\n")
NET_OLD = ("        need_cool = (need_cool | far_warm) & ~far_cold\n"
           "        q_star_kw = np.where(far_cold, 1e3, np.where(far_warm, -1e3, q_star_kw))\n")
NET_NEW = ("        need_cool = (need_cool | far_warm) & ~far_cold\n"
           "        if p[\"cool_hold\"]:\n"
           "            hold = self._since_heat < p[\"cool_hold\"]\n"
           "            far_warm = far_warm & ~hold\n"
           "            need_cool = need_cool & ~hold\n"
           "            q_star_kw = np.where(hold & (q_star_kw < 0.0), 0.0, q_star_kw)\n"
           "            self._since_heat = np.where(need_heat, 0, self._since_heat + 1)\n"
           "        q_star_kw = np.where(far_cold, 1e3, np.where(far_warm, -1e3, q_star_kw))\n")


def build(src: Path, dst: Path) -> None:
    text = src.read_bytes().decode("utf-8")
    crlf = "\r\n" in text
    text = text.replace("\r\n", "\n")
    for old, new in [(PARAM_OLD, PARAM_NEW), (INIT_OLD, INIT_NEW), (NET_OLD, NET_NEW)]:
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
