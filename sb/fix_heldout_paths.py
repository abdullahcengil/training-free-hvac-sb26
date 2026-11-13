"""Fix Windows path separators in the held-out scenario configs.

The starter kit's scenario generator writes absolute Windows paths with
backslashes into config.gin, and gin reads "\\b" in "...\\building_7001" as a
backspace, so the first held-out run crashed before any step was simulated
(16 Oct 2026). This script replaces backslashes with forward slashes on the
path lines only, and records the old and new SHA-256 of every file.

    python -m sb.fix_heldout_paths D:/SmartBuildings_data/heldout
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

PATH_KEYS = ("floor_plan_filepath", "zone_map_filepath", "metrics_path", "weather_csv_path")


def main(root: str) -> None:
    root = Path(root)
    lines = []
    for cfg in sorted((root / "scenarios").glob("*/*/config.gin")):
        old = cfg.read_bytes()
        text = old.decode("utf-8")
        out = []
        changed = 0
        for line in text.splitlines(keepends=True):
            key = line.split("=", 1)[0].strip()
            if key in PATH_KEYS and "\\" in line:
                line = re.sub(r"\\", "/", line)
                changed += 1
            out.append(line)
        new = "".join(out).encode("utf-8")
        cfg.write_bytes(new)
        rel = f"{cfg.parent.parent.name}/{cfg.parent.name}/config.gin"
        lines.append(f"{hashlib.sha256(old).hexdigest()} -> {hashlib.sha256(new).hexdigest()}  "
                     f"{rel}  ({changed} path lines)")
    (root / "MANIFEST_PATHFIX.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
