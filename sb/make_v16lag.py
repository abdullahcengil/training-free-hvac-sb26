"""Build the measured-delay variant (docs/LAG_SETTING.md): the frozen v16 file plus one option, extra_lag, nothing else.

v16 assumes the reading delay its probe found in this simulator (one step). A real building may have more. With
extra_lag = d the controller (1) learns each zone from the heat commanded d steps further back, and (2) rolls its zone
model forward d steps from the stale reading, through the heat it has already sent, before planning as before.
With extra_lag 0 (the default) every new line is skipped, so the file gives v16's actions bit for bit (checked on the
first 288 steps of a round-7 building).

    python -m sb.make_v16lag frozen/zonal_v16f.py D:/SmartBuildings_data/frozen/zonal_v16lag.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPL = [
    ("    delay_comp=1,          # ablation switch: 0 ignores the one-step delay\n",
     "    delay_comp=1,          # ablation switch: 0 ignores the one-step delay\n"
     "    extra_lag=0,           # reading delay beyond the one step found in this simulator, in steps (set from a\n"
     "                           # probe on site; docs/LAG_SETTING.md). 0: v16 exactly\n"),
    ("        self.prev_q2 = np.zeros(self.nz)   # heat applied during the step before\n",
     "        self.prev_q2 = np.zeros(self.nz)   # heat applied during the step before\n"
     "        self._qhist = [np.zeros(self.nz) for _ in range(self.p[\"extra_lag\"] + 2)]  # heat, newest first\n"),
    ("            phi = np.stack([self.prev_t - tm_prev, self.prev_q2, np.ones(self.nz),\n",
     "            q_id = self._qhist[1 + p[\"extra_lag\"]] if p[\"extra_lag\"] else self.prev_q2\n"
     "            phi = np.stack([self.prev_t - tm_prev, q_id, np.ones(self.nz),\n"),
    ("        oat = float(obs[self.oat_idx]) if self.oat_idx is not None else 290.0\n"
     "        t_ret = float(np.mean(temps))\n",
     "        oat = float(obs[self.oat_idx]) if self.oat_idx is not None else 290.0\n"
     "        raw_t = temps\n"
     "        if p[\"extra_lag\"]:\n"
     "            # The reading is extra_lag steps older than v16 assumes: bring it to now through the heat already\n"
     "            # sent (oldest first), with the same model and disturbance estimate the planning uses.\n"
     "            assert p[\"mass_model\"], \"extra_lag needs the mass model\"\n"
     "            tm = self.tm\n"
     "            for j in range(p[\"extra_lag\"], 0, -1):\n"
     "                t_next = self._m2_step(temps, tm, self._qhist[j], oat, self.prev_cm) + self.dhat\n"
     "                tm = tm + (temps - tm) / p[\"mass_n\"]\n"
     "                temps = t_next\n"
     "        t_ret = float(np.mean(temps))\n"),
    ("        self.prev_t = temps\n"
     "        self.prev_oat, self.prev_cm = oat, cmv\n",
     "        self.prev_t = raw_t\n"
     "        self.prev_oat, self.prev_cm = oat, cmv\n"
     "        self._qhist = [q_plan] + self._qhist[:-1]\n"),
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
