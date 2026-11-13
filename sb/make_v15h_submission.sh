#!/bin/bash
# After the v15 deep-cold screen and its regression checks pass (docs/V15COLD.md): parameters, frozen file, notebook,
# and the notebook check on a full-size deep-cold scenario whose first two days include comfort time with large rooms
# below the band (where the new options act).
#     bash sb/make_v15h_submission.sh hpz
set -e
cd .
PY=D:/SmartBuildings_data/starter-kit/.venv/Scripts/python
CAND=$1
$PY - "$CAND" <<'PYEOF'
import json, sys
from pathlib import Path
kw = json.loads(Path("submission/V14_PARAMS.json").read_text())
kw.update(json.loads(Path("docs/v15cold_candidates.json").read_text())[sys.argv[1]])
Path("submission/V15_PARAMS.json").write_text(json.dumps(kw, indent=1))
print("V15_PARAMS:", kw)
PYEOF
[ -f D:/SmartBuildings_data/frozen/zonal_v15f.py ] || cp D:/SmartBuildings_data/frozen/zonal_v15dev_h.py D:/SmartBuildings_data/frozen/zonal_v15f.py
sha256sum D:/SmartBuildings_data/frozen/zonal_v15dev_h.py D:/SmartBuildings_data/frozen/zonal_v15f.py
$PY -m sb.make_notebook --policy D:/SmartBuildings_data/frozen/zonal_v15f.py --params "$(cat submission/V15_PARAMS.json)" \
  --out submission/zonal_v15_submission.ipynb
$PY -m sb.nbcheck --notebook submission/zonal_v15_submission.ipynb --policy D:/SmartBuildings_data/frozen/zonal_v15f.py \
  --params submission/V15_PARAMS.json --scenario D:/SmartBuildings_data/coldsize/full/scenarios/building_7407/fairbanks_nov21 --steps 576
