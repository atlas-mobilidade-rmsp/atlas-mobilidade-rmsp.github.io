#!/bin/sh
# Baixa do IPEA (Projeto Acesso a Oportunidades, aopdata v1.0.0) a acessibilidade 2019 de São Paulo (transporte público,
# carro, a pé) e Guarulhos (carro, a pé) + grades hexagonais H3 -> data/raw_aop/ (ignorado pelo git; ~70 MB). Dado público.
# AOP só cobre SP e Guarulhos na RMSP; transporte público só em SP.
set -e
cd "$(dirname "$0")/.."
mkdir -p data/raw_aop
B=https://www.ipea.gov.br/geobr/aopdata/data
get() { [ -s "data/raw_aop/$(basename "$1")" ] || curl -sfL -m 600 "$B/$1" -o "data/raw_aop/$(basename "$1")"; echo "$(basename "$1") ok"; }
for m in public_transport car walk; do get access/spo/2019/$m/access_2019_${m}_spo.csv; done
for m in car walk; do get access/gua/2019/$m/access_2019_${m}_gua.csv; done
get grid/spo/hex_grid_spo.gpkg; get grid/gua/hex_grid_gua.gpkg
get population/spo/2010/population_2010_spo.csv; get population/gua/2010/population_2010_gua.csv    # população e renda (Censo 2010) por hexágono: pesos e recorte por renda
