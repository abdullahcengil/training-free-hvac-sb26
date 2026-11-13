#!/bin/bash
# After round 6 (docs/PREREGISTRATION_6.md) passes: v15 = the frozen v14 file with V14_PARAMS plus the empty-holiday
# rule (empty_day 1, empty_h 1.0; docs/HOLIDAY.md). No code changes, so the policy file stays zonal_v14f.py. The
# notebook check runs on a stress window whose first work day is a holiday (16 January), long enough (2 days) for the
# rule to fire at 07:00 on the holiday.
#     bash sb/make_v15hol_submission.sh
set -e
cd .
PY=D:/SmartBuildings_data/starter-kit/.venv/Scripts/python
$PY - <<'PYEOF'
import json
from pathlib import Path
kw = json.loads(Path("submission/V14_PARAMS.json").read_text())
kw.update({"empty_day": 1, "empty_h": 1.0})
Path("submission/V15_PARAMS.json").write_text(json.dumps(kw, indent=1))
print("V15_PARAMS:", kw)
PYEOF
sha256sum D:/SmartBuildings_data/frozen/zonal_v14f.py
$PY -m sb.make_notebook --policy D:/SmartBuildings_data/frozen/zonal_v14f.py --params "$(cat submission/V15_PARAMS.json)" \
  --out submission/zonal_v15_submission.ipynb
$PY -m sb.nbcheck --notebook submission/zonal_v15_submission.ipynb --policy D:/SmartBuildings_data/frozen/zonal_v14f.py \
  --params submission/V15_PARAMS.json --scenario D:/SmartBuildings_data/stress/scenarios/building_train_7/duluth_jan15 --steps 576
