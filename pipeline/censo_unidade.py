"""F4 — censo 1970–2022 e CNEFE 2022 agregados por unidade (todos os níveis).

Fonte: `nucleo_por_zona` e `cnefe_por_zona` do laboratório (já interpolados para cada zoneamento OD e para as AMC).
amc146/amc75 vêm direto (zoneamento amc_8723/amc_7723); muni e sub somam as zonas de 2023 (zona -> unidade dominante);
zona = a própria zona do zoneamento `edicao`. Contagens e totais somam; percentuais são recalculados pós-agregação.
Saída: data/processed/censo/censo_por_unidade.parquet e cnefe/cnefe_por_unidade.parquet.
"""
import duckdb
import pandas as pd

from pipeline.base import GEO
from pipeline.fontes import CENSO_DB, PROCESSED

SOMAVEIS = ["pop_total", "pop_homens", "pop_mulheres", "pop_0_14", "pop_15_59", "pop_60m", "pop_15m", "pop_15m_alfab", "dom_pp",
            "moradores_dpp", "dom_agua_rede", "dom_esgoto_rede", "dom_lixo_coletado", "dom_proprio", "dom_alugado", "resp_com_renda", "resp_renda_total_nominal"]


def _nucleo(con) -> pd.DataFrame:
    return con.execute("select * from nucleo_por_zona").df()


def _mapa_zona_unidade() -> pd.DataFrame:
    u = pd.read_parquet(GEO / "unidades_ref_geo.parquet")
    z = u[(u.nivel == "zona") & (u.edicao == 2023)][["codigo", "muni_ibge"]].rename(columns={"codigo": "zona"})
    s = pd.read_parquet(GEO / "zona_para_sub.parquet")
    s = s[s.ano == 2023][["zona", "sub"]].astype({"zona": str})
    return z.merge(s, on="zona", how="left")


def indicadores(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["densidade_hab_km2"] = d.pop_total / d.area_km2 if "area_km2" in d else None
    d["pct_0_14"] = 100 * d.pop_0_14 / d.pop_total
    d["pct_60m"] = 100 * d.pop_60m / d.pop_total
    d["taxa_alfab_15m"] = 100 * d.pop_15m_alfab / d.pop_15m
    d["moradores_por_dom"] = d.moradores_dpp / d.dom_pp
    d["pct_dom_agua_rede"] = 100 * d.dom_agua_rede / d.dom_pp
    d["pct_dom_esgoto_rede"] = 100 * d.dom_esgoto_rede / d.dom_pp
    d["pct_dom_proprio"] = 100 * d.dom_proprio / d.dom_pp
    d["renda_resp_r2023"] = d.resp_renda_total_nominal / d.resp_com_renda
    return d


def censo_por_unidade() -> pd.DataFrame:
    con = duckdb.connect(str(CENSO_DB), read_only=True)
    n = _nucleo(con)
    n["zona"] = n.zona.astype(str)
    partes = []
    for zoneamento, nivel in (("amc_8723", "amc146"), ("amc_7723", "amc75")):
        p = n[n.zoneamento == zoneamento].rename(columns={"zona": "codigo"}).assign(nivel=nivel, edicao=0)
        partes.append(p)
    for ano in ("1977", "1987", "1997", "2007", "2017", "2023"):
        partes.append(n[n.zoneamento == ano].rename(columns={"zona": "codigo"}).assign(nivel="zona", edicao=int(ano)))
    z23 = n[n.zoneamento == "2023"].merge(_mapa_zona_unidade(), on="zona", how="left")
    for col, nivel in (("muni_ibge", "muni"), ("sub", "sub")):
        g = z23.dropna(subset=[col]).groupby([col, "ano_censo"], as_index=False)[SOMAVEIS].sum().rename(columns={col: "codigo"})
        partes.append(g.assign(nivel=nivel, edicao=0))
    df = pd.concat(partes, ignore_index=True)
    u = pd.read_parquet(GEO / "unidades_ref_geo.parquet")[["nivel", "edicao", "codigo", "area_km2"]]
    df = df.merge(u, on=["nivel", "edicao", "codigo"], how="left")
    df = indicadores(df)
    cols = ["nivel", "edicao", "codigo", "ano_censo", "pop_total", "densidade_hab_km2", "pct_0_14", "pct_60m", "taxa_alfab_15m", "dom_pp",
            "moradores_por_dom", "pct_dom_agua_rede", "pct_dom_esgoto_rede", "pct_dom_proprio", "renda_resp_r2023"]
    return df[cols].sort_values(["nivel", "edicao", "codigo", "ano_censo"])


def cnefe_por_unidade() -> pd.DataFrame:
    con = duckdb.connect(str(CENSO_DB), read_only=True)
    c = con.execute("select * from cnefe_por_zona").df()
    c["zona"] = c.zona.astype(str)
    cols = ["grupo", "subgrupo", "motivo_od", "gera_viagens"]
    val = ["n_enderecos", "n_multiplo_ate_10", "n_multiplo_mais_10", "n_multiplo_desconhecido"]
    partes = []
    for zoneamento, nivel in (("amc_8723", "amc146"), ("amc_7723", "amc75")):
        partes.append(c[c.zoneamento == zoneamento].rename(columns={"zona": "codigo"}).assign(nivel=nivel, edicao=0))
    for ano in ("1977", "1987", "1997", "2007", "2017", "2023"):
        partes.append(c[c.zoneamento == ano].rename(columns={"zona": "codigo"}).assign(nivel="zona", edicao=int(ano)))
    z23 = c[c.zoneamento == "2023"].merge(_mapa_zona_unidade(), on="zona", how="left")
    for col, nivel in (("muni_ibge", "muni"), ("sub", "sub")):
        g = z23.dropna(subset=[col]).groupby([col] + cols, as_index=False, dropna=False)[val].sum().rename(columns={col: "codigo"})
        partes.append(g.assign(nivel=nivel, edicao=0))
    df = pd.concat(partes, ignore_index=True)
    return df[["nivel", "edicao", "codigo", *cols, *val]]


def rodar() -> None:
    (PROCESSED / "censo").mkdir(exist_ok=True); (PROCESSED / "cnefe").mkdir(exist_ok=True)
    a = censo_por_unidade(); a.to_parquet(PROCESSED / "censo" / "censo_por_unidade.parquet", index=False)
    b = cnefe_por_unidade(); b.to_parquet(PROCESSED / "cnefe" / "cnefe_por_unidade.parquet", index=False)
    print("censo_por_unidade", len(a), "| cnefe_por_unidade", len(b))
    print(a[(a.nivel == "muni")].groupby("ano_censo").pop_total.sum().round(0).to_dict())


if __name__ == "__main__":
    rodar()
