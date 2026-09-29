#!/bin/sh
# Copia data/processed -> web/public/data (sem _tmp). Recusa se o gate P1–P6 não estiver verde.
set -e
cd "$(dirname "$0")/../.."
[ -f data/processed/.gate_ok ] || { echo "ERRO: data/processed/.gate_ok ausente. Rode 'python -m pipeline.gate_check'." >&2; exit 1; }
rm -rf web/public/data && mkdir -p web/public/data
for d in data/processed/*; do
  n=$(basename "$d")
  [ "$n" = "_tmp" ] && continue
  cp -R "$d" web/public/data/
done
rm -rf web/public/data/geo/_tmp
echo "Dados sincronizados ($(du -sh web/public/data | cut -f1))"
rm -f web/public/data/geo/*_wgs.topojson
