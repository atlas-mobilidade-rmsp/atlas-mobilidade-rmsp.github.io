#!/bin/sh
# F1: GeoJSON intermediário (pipeline/build_geo.py, EPSG:31983 em metros) -> TopoJSON.
# <nome>.topojson (metros, frame cartesiano do deck.gl) e <nome>_wgs.topojson (graus).
# simplify e clean em invocações separadas (a simplificação é lazy; ver atlas da migração F9.10).
set -e
cd "$(dirname "$0")/.."
MS="web/node_modules/.bin/mapshaper"
T=data/processed/geo/_tmp
O=data/processed/geo
for f in $T/*.geojson; do
  n=$(basename "$f" .geojson)
  case "$n" in zonas_*) pct=12% ;; *) pct=20% ;; esac
  $MS -i "$f" -clean -o "$T/${n}_c.json" format=geojson 2>/dev/null
  $MS -i "$T/${n}_c.json" -simplify "$pct" keep-shapes -o "$T/${n}_s.json" format=geojson 2>/dev/null
  ${PYTHON:-python3} -m pipeline.repara_geo "$T/${n}_s.json"
  $MS -i "$T/${n}_s.json" -o "$O/$n.topojson" format=topojson id-field=codigo
  $MS -i "$T/${n}_s.json" -proj from=EPSG:31983 EPSG:4326 -o "$O/${n}_wgs.topojson" format=topojson id-field=codigo
done
du -sh $O
