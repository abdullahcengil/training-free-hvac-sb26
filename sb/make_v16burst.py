"""Build the air-handler skip variant (docs/BURST.md): the frozen v16 file plus two options, skip_ahu and skip_k.

skip_ahu 0 (default) leaves v16 unchanged (known-answer check). 1: in comfort time, an air handler whose only requests
are for heat skips one step (fan off, so no outside air reaches its idle zones) when every zone that asked for heat
stays at least skip_k above the comfort band's lower edge at k+2 without it; never two skips in a row. 2: the same
for air handlers whose only requests are for cooling (below the upper edge), and for mixed ones when both hold.

    python -m sb.make_v16burst D:/SmartBuildings_data/frozen/zonal_v16f.py policies/zonal_v16burst.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPL = [
    ("    glide_oat=400.0,       # K: glide only while the 24-hour mean outside temperature is below this\n",
     "    glide_oat=400.0,       # K: glide only while the 24-hour mean outside temperature is below this\n"
     "    skip_ahu=0,            # 1/2: skip a step of an air handler whose zones can wait (docs/BURST.md); 0: off\n"
     "    skip_k=0.05,           # K inside the comfort band the waiting zones must stay at k+2\n"),
    ("        self.prev_ahu_on = np.zeros(self.n_ahu, dtype=bool)\n",
     "        self.prev_ahu_on = np.zeros(self.n_ahu, dtype=bool)\n"
     "        self._skipped = np.zeros(self.n_ahu, dtype=bool)\n"),
    ("            active = bool(np.any(nh) or np.any(nc))\n"
     "            disc[a] = 1 if active else 0\n",
     "            active = bool(np.any(nh) or np.any(nc))\n"
     "            if active and p[\"skip_ahu\"] and h2c == 0.0 and not self._skipped[a]:\n"
     "                hz, cz = mem[nh], mem[nc]\n"
     "                ok_h = (not len(hz)) or bool(np.all(t2_free[hz] >= self.comfort[0] + p[\"skip_k\"])\n"
     "                                             and not np.any(self._far_cold[hz]))\n"
     "                if p[\"skip_ahu\"] == 1:\n"
     "                    ok_c = not len(cz)\n"
     "                else:\n"
     "                    ok_c = (not len(cz)) or bool(np.all(t2_free[cz] <= self.comfort[1] - p[\"skip_k\"]))\n"
     "                if ok_h and ok_c:\n"
     "                    active = False\n"
     "                    self._skipped[a] = True\n"
     "            else:\n"
     "                self._skipped[a] = False\n"
     "            disc[a] = 1 if active else 0\n"),
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
