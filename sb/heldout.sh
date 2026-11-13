#!/usr/bin/env bash
# Pre-registered held-out run (docs/PREREGISTRATION.md): the frozen zonal
# controller (its defaults at the current commit) and the four baselines on the
# 12 held-out scenarios, full 30-day episodes. Run once.
set -e
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/heldout/scenarios
OUT=/d/SmartBuildings_data/results/heldout
mkdir -p $OUT
if [ -n "$(git status --porcelain policies/zonal.py)" ]; then
  echo "policies/zonal.py has uncommitted changes; commit before the held-out run" >&2
  exit 1
fi
COMMIT=$(git rev-parse HEAD)
echo "{\"commit\": \"$COMMIT\", \"started\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_INFO.json
for pol in "policies/zonal.py:TransferPolicy|zonal" "baseline:pid_water|pid_water" "baseline:pid|pid" "baseline:fixed_setpoint|fixed_setpoint" "baseline:bang_bang|bang_bang"; do
  spec=${pol%%|*}; tag=${pol##*|}
  echo "== $tag"
  $PY -m sb.run --policy "$spec" --scenarios $SC --out $OUT/$tag --steps 8640 --workers ${WORKERS:-3} --components 2>&1 | grep -v -i warn
done
echo "{\"commit\": \"$COMMIT\", \"finished\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > $OUT/RUN_DONE.json
