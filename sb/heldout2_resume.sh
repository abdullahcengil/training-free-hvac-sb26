#!/usr/bin/env bash
# Round 2, deviation 3 (docs/DEVIATIONS.md): resume the baselines after the
# machine shut down. RUN_INFO.json is left as written at the start; sb.run
# skips every scenario that already has a result.
cd "$(dirname "$0")/.."
PY=/d/SmartBuildings_data/starter-kit/.venv/Scripts/python
SC=/d/SmartBuildings_data/heldout2/scenarios
OUT=/d/SmartBuildings_data/results/heldout2
for b in pid_water pid fixed_setpoint bang_bang; do
  echo "== $b"
  $PY -m sb.run --policy "baseline:$b" --scenarios $SC --out $OUT/$b --steps 8640 --workers ${WORKERS:-3} --components 2>&1 | grep -v -i warn
done
C=$(python -c "import json;print(json.load(open('$OUT/RUN_INFO.json'))['commit'])" 2>/dev/null || echo unknown)
echo "{\"commit\": \"$C\", \"finished\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"resumed_after_shutdown\": true}" > $OUT/RUN_DONE.json
