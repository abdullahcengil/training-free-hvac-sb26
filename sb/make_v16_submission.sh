#!/bin/bash
# Only after round 7 (docs/PREREGISTRATION_7.md) passes: v16 = chm, the cool-hold file (zonal_v16dev_ch.py, built by
# sb/make_v16ch.py from frozen/zonal_v14f.py) with V15_PARAMS plus cool_hold 2 and margin_heat 0.30 (docs/CHATTER.md).
# The policy file is copied into frozen/ (zonal_v16f.py) unchanged. The notebook check runs 576 steps of a cold
# full-size development building.
#     bash sb/make_v16_submission.sh
set -e
cd .
PY=D:/SmartBuildings_data/starter-kit/.venv/Scripts/python
cp D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py frozen/zonal_v16f.py
cp D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py D:/SmartBuildings_data/frozen/zonal_v16f.py
$PY - <<'PYEOF'
import json
from pathlib import Path
kw = json.loads(Path("submission/V15_PARAMS.json").read_text())
kw.update({"cool_hold": 2, "margin_heat": 0.30})
Path("submission/V16_PARAMS.json").write_text(json.dumps(kw, indent=1))
print("V16_PARAMS:", kw)
PYEOF
sha256sum frozen/zonal_v16f.py D:/SmartBuildings_data/frozen/zonal_v16f.py D:/SmartBuildings_data/frozen/zonal_v16dev_ch.py
$PY -m sb.make_notebook --policy D:/SmartBuildings_data/frozen/zonal_v16f.py --params "$(cat submission/V16_PARAMS.json)" \
  --out submission/zonal_v16_submission.ipynb
$PY -m sb.nbcheck --notebook submission/zonal_v16_submission.ipynb --policy D:/SmartBuildings_data/frozen/zonal_v16f.py \
  --params submission/V16_PARAMS.json --scenario D:/SmartBuildings_data/bigdev/scenarios/building_7001/chicago_jan15 \
  --steps 576
