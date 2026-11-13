#!/usr/bin/env bash
# When the boiler-setback screen has its four results, stop list 3 (its remaining screens are superseded)
# and start the cooling-glide refinements (2 workers).
cd "$(dirname "$0")/.."
R=/d/SmartBuildings_data/results/dev11_8640
until [ $(ls $R/v11c_wi/*.json 2>/dev/null | wc -l) -ge 4 ]; do sleep 20; done
for pid in $(powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*jobs_v11c_3.json*' } | ForEach-Object { \$_.ProcessId }"); do taskkill //F //PID $pid; done
for pid in $(powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*spawn_main*' -and \$_.ParentProcessId -eq 940 } | ForEach-Object { \$_.ProcessId }"); do taskkill //F //PID $pid; done
sleep 5
/d/SmartBuildings_data/starter-kit/.venv/Scripts/python -m sb.jobs sb/jobs_v11b_5.json --workers 2 2>&1 | grep --line-buffered -v -i warn
