#!/usr/bin/env bash
# Round-1 rule: a changed policy is run on the round-1 set too and labelled post hoc.
# v8 = the round-2 frozen file and parameters (results/heldout2/RUN_INFO.json).
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
C=e8dbcd3163f2d0e4ce9006b02ed7067a5f5927bd
$PY -m sb.run --policy D:/SmartBuildings_data/frozen/zonal_$C.py:TransferPolicy \
  --scenarios /d/SmartBuildings_data/heldout/scenarios --out /d/SmartBuildings_data/results/heldout/v8_posthoc \
  --steps 8640 --workers ${WORKERS:-1} --components --kwargs "$(cat docs/preregistration2/V8_PARAMS.json)" 2>&1 | grep -v -i warn
