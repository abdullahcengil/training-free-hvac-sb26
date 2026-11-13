"""Build the frost-protection variant (docs/FROST.md): the frozen v16 file plus one option, frost_min.

frost_min (K): every zone's heating floor is at least this. 0 (default) leaves v16 unchanged (known-answer check K1).

    python -m sb.make_v16frost D:/SmartBuildings_data/frozen/zonal_v16f.py policies/zonal_v16frost.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPL = [
    ("    glide_oat=400.0,       # K: glide only while the 24-hour mean outside temperature is below this\n",
     "    glide_oat=400.0,       # K: glide only while the 24-hour mean outside temperature is below this\n"
     "    frost_min=0.0,         # K, lowest heating floor any zone may have (frost protection, docs/FROST.md); 0: off\n"),
    ("        self._unocc = glide\n",
     "        if p[\"frost_min\"] > 0.0:\n"
     "            lo = np.maximum(lo, p[\"frost_min\"])\n"
     "        self._unocc = glide\n"),
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
