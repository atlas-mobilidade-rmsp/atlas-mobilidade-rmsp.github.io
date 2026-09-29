"""meta.json e comparabilidade.json (P6)."""
import json

import pandas as pd

from pipeline import precisao_regras as R
from pipeline.edicoes import ANOS, CV_BOA, CV_CAUTELA, EDICOES, MIN_N_CELULA, MIN_N_DETALHE, MIN_N_ZONA
from pipeline.fontes import PROCESSED

NIVEIS_ROTULO = {"zona": "Zona OD", "amc146": "AMC (1987–2023, 146)", "amc75": "AMC (1977–2023, 75)",
                 "sub": "Subprefeitura / município", "muni": "Município"}


def comparabilidade() -> dict:
    return {str(a): {
        "area_parcial": e.area_parcial, "amc146": e.amc146, "amc75": e.amc75, "sub": a >= 1997,
        "coordenadas": "coords" in e.recursos, "raca": "raca" in e.recursos, "hibrido": "hibrido" in e.recursos,
        "app": "app" in e.recursos, "pandemia": "pandemia" in e.recursos, "grau_ins_5": "sem_grau_ins_5" not in e.recursos,
    } for a, e in EDICOES.items()}


def main() -> None:
    (PROCESSED / "comparabilidade.json").write_text(json.dumps(comparabilidade(), indent=1, ensure_ascii=False))
    maior = {}
    for n in R.NIVEIS:
        m = 0
        for a in ANOS:
            f = PROCESSED / str(a) / f"fluxos_{n}.parquet"
            if f.exists():
                m = max(m, float(pd.read_parquet(f, columns=["total"]).total.max()))
        maior[n] = m
    meta = {"versao_dados": "0.1.0", "edicoes": list(ANOS), "niveis": list(R.NIVEIS), "rotulos": {"niveis": NIVEIS_ROTULO},
            "precisao": {"min_n_celula": MIN_N_CELULA, "min_n_zona": MIN_N_ZONA, "min_n_detalhe": MIN_N_DETALHE,
                         "cv_boa": CV_BOA, "cv_cautela": CV_CAUTELA, "deff": R.DEFF_V1},
            "maior_fluxo": maior,
            "fontes": ["Pesquisa Origem e Destino — Metrô-SP (1977, 1987, 1997, 2007, 2017, 2023)",
                       "IBGE — Censo Demográfico 2022 (setores, CNEFE)", "GeoSampa — Prefeitura de São Paulo"],
            "citacao": "Sobreira, D. P. Atlas da Mobilidade na RMSP (1977–2023)."}
    (PROCESSED / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print("meta.json e comparabilidade.json gravados")


if __name__ == "__main__":
    main()
