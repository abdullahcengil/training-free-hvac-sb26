#!/bin/bash
# After the v15 full check passes (docs/BIGDEV.md): parameters, frozen file, notebook, and the notebook check on a
# full-size cold scenario whose first two days include the Sunday glide (where the new option acts).
#     bash sb/make_v15_submission.sh A_sus
set -e
cd .
PY=D:/SmartBuildings_data/starter-kit/.venv/Scripts/python
CAND=$1
$PY - "$CAND" <<'PYEOF'
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from sb.make_v15_full_jobs import CANDS
kw = json.loads(Path("submission/V14_PARAMS.json").read_text())
kw.update(CANDS[sys.argv[1]])
Path("submission/V15_PARAMS.json").write_text(json.dumps(kw, indent=1))
print("V15_PARAMS:", kw)
PYEOF
[ -f D:/SmartBuildings_data/frozen/zonal_v15f.py ] || cp D:/SmartBuildings_data/frozen/zonal_v15dev_a.py D:/SmartBuildings_data/frozen/zonal_v15f.py
sha256sum D:/SmartBuildings_data/frozen/zonal_v15dev_a.py D:/SmartBuildings_data/frozen/zonal_v15f.py
$PY -m sb.make_notebook --policy D:/SmartBuildings_data/frozen/zonal_v15f.py --params "$(cat submission/V15_PARAMS.json)" \
  --out submission/zonal_v15_submission.ipynb
$PY -m sb.nbcheck --notebook submission/zonal_v15_submission.ipynb --policy D:/SmartBuildings_data/frozen/zonal_v15f.py \
  --params submission/V15_PARAMS.json --scenario D:/SmartBuildings_data/bigdev/scenarios/building_7001/chicago_jan15 --steps 576
