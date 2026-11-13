#!/usr/bin/env bash
# Sequential dev variants: tag|kwargs per line on stdin.
cd "$(dirname "$0")/.."
while IFS='|' read -r tag kw; do
  [ -z "$tag" ] && continue
  echo "== $tag $kw"
  bash sb/dev.sh policies/zonal.py:TransferPolicy "$tag" "$kw" | grep SCORE
done
