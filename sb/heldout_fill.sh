#!/usr/bin/env bash
# Deviation 2 (docs/DEVIATIONS.md): re-run only the held-out jobs that crashed
# out of memory, with the frozen policy file exported from the commit recorded
# in RUN_INFO.json. sb.run skips every scenario that already has a result.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/heldout/scenarios
OUT=/d/SmartBuildings_data/results/heldout
C=ad5946615c746745a243560ae3a681eaf7d19618
POLICY=D:/SmartBuildings_data/frozen/zonal_$C.py:TransferPolicy
for tag in "$@"; do
  case $tag in
    zonal) spec=$POLICY ;;
    *) spec=baseline:$tag ;;
  esac
  echo "== fill $tag"
  $PY -m sb.run --policy "$spec" --scenarios $SC --out $OUT/$tag --steps 8640 --workers ${WORKERS:-1} --components 2>&1 | grep -v -i warn
done
