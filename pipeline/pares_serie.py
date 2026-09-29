"""F2 — pares_serie: cada par O/D (AMC-146, AMC-75, município) ao longo de todas as pesquisas, sem interpolar.

status: publicado | n_insuficiente (par com n < piso ou ausente na amostra) | nao_existia (nível inexistente na
edição) | fora_area_1977 (unidade fora da área pesquisada em 1977). share_da_* usa o total publicado da unidade
naquele tipo (aproximação: pares n < piso ficam de fora do denominador).
"""
import numpy as np
import pandas as pd

from pipeline.edicoes import ANOS, EDICOES
from pipeline.fontes import PROCESSED

NIVEIS_SERIE = {"amc75": ANOS, "amc146": tuple(a for a in ANOS if a >= 1987), "muni": ANOS}
COLS = ["total", "n", "cv", "precisao", "dur_mediana", "pct_coletivo", "pct_individual", "pct_ativo", "ief_par"]


def _presentes(nivel: str, ano: int) -> set:
    ind = pd.read_parquet(PROCESSED / str(ano) / "indicadores.parquet", columns=["nivel", "codigo", "pop"])
    return set(ind[(ind.nivel == nivel) & (ind["pop"] > 0)].codigo)


def construir() -> pd.DataFrame:
    saida = []
    for nivel, anos in NIVEIS_SERIE.items():
        fl = pd.concat([pd.read_parquet(PROCESSED / str(a) / f"fluxos_{nivel}.parquet").assign(edicao=a) for a in anos])
        fl["share_da_origem"] = fl.total / fl.groupby(["edicao", "tipo", "origem"]).total.transform("sum")
        fl["share_do_destino"] = fl.total / fl.groupby(["edicao", "tipo", "destino"]).total.transform("sum")
        pares = fl[["tipo", "origem", "destino"]].drop_duplicates()
        grade = pares.merge(pd.DataFrame({"edicao": ANOS}), how="cross")
        g = grade.merge(fl[["tipo", "origem", "destino", "edicao", *COLS, "share_da_origem", "share_do_destino"]],
                        on=["tipo", "origem", "destino", "edicao"], how="left")
        pres = {a: _presentes(nivel, a) for a in ANOS if a in anos}

        def status(r):
            if r.edicao not in anos:
                return "nao_existia"
            if not pd.isna(r.total):
                return "publicado"
            if r.origem not in pres[r.edicao] or r.destino not in pres[r.edicao]:
                return "fora_area_1977" if r.edicao == 1977 else "nao_existia"
            return "n_insuficiente"
        g["status"] = [status(r) for r in g.itertuples()]
        g.insert(0, "nivel", nivel)
        saida.append(g)
    return pd.concat(saida, ignore_index=True)


def rodar() -> None:
    df = construir()
    pasta = PROCESSED / "serie"
    pasta.mkdir(exist_ok=True)
    df.to_parquet(pasta / "pares_serie.parquet", index=False)
    print("pares_serie:", len(df), df.groupby(["nivel", "status"]).size().to_dict())


if __name__ == "__main__":
    rodar()
