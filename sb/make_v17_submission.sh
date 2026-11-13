#!/bin/bash
# Only after round 8 (docs/PREREGISTRATION_8.md) passes: v17 = sp1, the frozen v16 file (frozen/zonal_v16f.py,
# unchanged) with V16_PARAMS plus safety_pred 1 (docs/HEATNET.md). The notebook check runs 576 steps of a cold
# full-size development building (it is a simulation: run it only while fewer than three others run).
#     bash sb/make_v17_submission.sh
set -e
cd .
PY=D:/SmartBuildings_data/starter-kit/.venv/Scripts/python
$PY - <<'PYEOF'
import json
from pathlib import Path
kw = json.loads(Path("submission/V16_PARAMS.json").read_text())
kw.update({"safety_pred": 1})
Path("submission/V17_PARAMS.json").write_text(json.dumps(kw, indent=1))
print("V17_PARAMS:", kw)
PYEOF
sha256sum frozen/zonal_v16f.py D:/SmartBuildings_data/frozen/zonal_v16f.py
$PY -m sb.make_notebook --policy D:/SmartBuildings_data/frozen/zonal_v16f.py --params "$(cat submission/V17_PARAMS.json)" \
  --out submission/zonal_v17_submission.ipynb
$PY -m sb.nbcheck --notebook submission/zonal_v17_submission.ipynb --policy D:/SmartBuildings_data/frozen/zonal_v16f.py \
  --params submission/V17_PARAMS.json --scenario D:/SmartBuildings_data/bigdev/scenarios/building_7001/chicago_jan15 \
  --steps 576
