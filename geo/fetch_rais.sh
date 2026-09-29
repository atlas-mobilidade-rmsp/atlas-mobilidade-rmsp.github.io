#!/bin/sh
# Baixa do MTE/PDET a RAIS pública (vínculos, UF SP) de 2007, 2017 e 2023 -> data/raw_rais/ (ignorado pelo git; ~2,2 GB).
# Depois: python -m pipeline.rais  (extrai um ano por vez, agrega e apaga o extraído; precisa de py7zr e ~10 GB livres).
set -e
cd "$(dirname "$0")/.."
mkdir -p data/raw_rais
B=ftp://ftp.mtps.gov.br/pdet/microdados/RAIS
get() { [ -s "data/raw_rais/$2" ] || curl -sS -C - "$B/$1" -o "data/raw_rais/$2"; echo "$2 ok"; }
get 2023/RAIS_VINC_PUB_SP.7z RAIS_VINC_PUB_SP_2023.7z
get 2017/SP2017.7z SP2017.7z
get 2007/SP2007.7z SP2007.7z
