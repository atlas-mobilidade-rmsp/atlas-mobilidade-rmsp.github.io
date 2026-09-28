# Atlas da Mobilidade na RMSP

Atlas web orientado a perguntas sobre a Pesquisa Origem e Destino (Metrô-SP), 1977–2023. Ver `docs/PLANO.md`.

    export METROSP_ROOT=../metrosp
    python pipeline/fontes.py && python -m pytest
    cd web && npm install && npm test
