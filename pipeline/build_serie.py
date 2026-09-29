"""F4 — série histórica a partir SÓ de data/processed (nunca microdado).

serie/unidades_serie.parquet : (nivel amc75|amc146|muni, codigo, edicao, indicadores da edição + gravitacional)
serie/sistema_serie.parquet  : (edicao, universo, medida, categoria, valor, n) + parâmetros gravitacionais e Gini de Hansen
serie/comparabilidade.json   : reexporta P6 (já em data/processed/comparabilidade.json)
"""
import json

import numpy as np
import pandas as pd

from pipeline.edicoes import ANOS
from pipeline.fontes import PROCESSED

NIVEIS = ("amc75", "amc146", "muni")


def gini(v: np.ndarray, w: np.ndarray) -> float:
    o = np.argsort(v); v, w = v[o], w[o]
    cw, cv = np.cumsum(w) / w.sum(), np.cumsum(v * w) / (v * w).sum()
    return float(1 - np.sum((cw[1:] - cw[:-1]) * (cv[1:] + cv[:-1])) - cw[0] * cv[0])


def unidades_serie() -> pd.DataFrame:
    partes = []
    for a in ANOS:
        ind = pd.read_parquet(PROCESSED / str(a) / "indicadores.parquet")
        ind = ind[ind.nivel.isin(NIVEIS)]
        g = pd.read_parquet(PROCESSED / str(a) / "gravitacional.parquet")
        g = g.drop(columns=["jobs_housing_od"]).rename(columns={"empregos_od": "empregos_od_grav", "ocupados_od": "ocupados_od_grav"})
        m = ind.merge(g, on=["nivel", "codigo"], how="left").rename(columns={"ano": "edicao"})
        partes.append(m.assign(edicao=a))
    return pd.concat(partes, ignore_index=True)


def sistema_serie() -> pd.DataFrame:
    s = pd.concat([pd.read_parquet(PROCESSED / str(a) / "sistema.parquet") for a in ANOS], ignore_index=True).rename(columns={"ano": "edicao"})
    params = json.loads((PROCESSED / "serie" / "gravitacional_params.json").read_text())["edicoes"]
    extra = []
    for a in ANOS:
        p = params[str(a)].get("amc75") or params[str(a)]["muni"]
        for imp in ("dist_km", "tempo_min"):
            r = p[imp]
            extra += [(a, "area1977", f"beta_{imp}", "exp", r["exp"]["parametro"], p["n_pares_obs"]),
                      (a, "area1977", f"gamma_{imp}", "pow", r["pow"]["parametro"], p["n_pares_obs"]),
                      (a, "area1977", f"mtl_{imp}", "obs", r["mtl_obs"], p["n_pares_obs"]),
                      (a, "area1977", f"excesso_{imp}", "amc75", r.get("excesso", np.nan), p["n_pares_obs"]),
                      (a, "area1977", f"utilizacao_{imp}", "amc75", r.get("utilizacao_capacidade", np.nan), p["n_pares_obs"])]
        inc = p["dist_km"].get("incl_domicilio")
        if inc:
            extra += [(a, "area1977", "beta_dist_km_incl", "exp", inc["beta"], p["n_pares_obs"]), (a, "area1977", "mtl_dist_km_incl", "obs", inc["mtl_obs"], p["n_pares_obs"]),
                      (a, "area1977", "excesso_dist_km_incl", "amc75", inc["excesso"], p["n_pares_obs"]), (a, "area1977", "autocont_sistema_incl", "amc75", inc["autocont_sistema"], p["n_pares_obs"])]
        if "autocont_sistema" in p["dist_km"]:
            extra.append((a, "area1977", "autocont_sistema", "amc75", p["dist_km"]["autocont_sistema"], p["n_pares_obs"]))
        g = pd.read_parquet(PROCESSED / str(a) / "gravitacional.parquet")
        g = g[g.nivel == "amc75"]
        pop = pd.read_parquet(PROCESSED / str(a) / "indicadores.parquet")
        pop = pop[pop.nivel == "amc75"].set_index("codigo")["pop"]
        w = g.codigo.map(pop).fillna(0).values
        extra.append((a, "area1977", "gini_hansen_emp", "amc75", gini(g.hansen_emp_exp_dist_km.values, w), len(g)))
    e = pd.DataFrame(extra, columns=["edicao", "universo", "medida", "categoria", "valor", "n"])
    e["precisao"] = "ok"
    return pd.concat([s, e], ignore_index=True)


def rodar() -> None:
    d = PROCESSED / "serie"
    d.mkdir(exist_ok=True)
    u = unidades_serie(); u.to_parquet(d / "unidades_serie.parquet", index=False)
    s = sistema_serie(); s.to_parquet(d / "sistema_serie.parquet", index=False)
    (d / "comparabilidade.json").write_text((PROCESSED / "comparabilidade.json").read_text())
    print("unidades_serie", len(u), "sistema_serie", len(s))
    q = s[(s.medida == "ind_mob") & (s.universo == "edicao") & s.categoria.isin(["q1", "q5"])].pivot(index="edicao", columns="categoria", values="valor").round(2)
    print(q.to_string())


if __name__ == "__main__":
    rodar()
