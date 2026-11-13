"""Run time of each scenario in a result folder."""
import json
import sys
from pathlib import Path

for f in sorted(Path(sys.argv[1]).glob("*.json")):
    j = json.loads(f.read_text())
    print(f"{f.stem:34s} {j['seconds']:6.0f} s  score {abs(j['mean_reward']):.5f}")
