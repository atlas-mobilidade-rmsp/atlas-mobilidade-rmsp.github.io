#!/bin/sh
# Baixa do GeoSampa (Prefeitura de SP, WFS público) subprefeituras, linhas e estações de metrô/trem
# em EPSG:31983 -> data/geo/raw/. Dado geográfico público (sem microdado). Licença: ver GeoSampa.
set -e
cd "$(dirname "$0")/.."
mkdir -p data/geo/raw
for l in subprefeitura linha_metro linha_trem estacao_metro estacao_trem; do
  curl -sf -m 120 "http://wfs.geosampa.prefeitura.sp.gov.br/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=geoportal:$l&outputFormat=application/json&srsName=EPSG:31983" -o "data/geo/raw/$l.geojson"
  echo "$l ok"
done
