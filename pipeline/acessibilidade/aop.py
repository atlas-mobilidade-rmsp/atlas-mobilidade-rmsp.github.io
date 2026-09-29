"""F6 — acessibilidade 2019 do Projeto Acesso a Oportunidades (IPEA/aopdata) agregada às unidades do atlas.

Cobertura: só São Paulo (tp, auto, a pé) e Guarulhos (auto, a pé). Hexágonos H3 (res. 9) -> unidade pelo centroide do
hexágono; média ponderada pela população de 2010 do próprio AOP (Censo 2010: vintage diferente da acessibilidade 2019).
Medidas: cma30/60/90 = empregos (CMATT) acessíveis em 30/60/90 min; cma60_saude, cma60_escola (equipamentos); tmi_saude,
tmi_escola = tempo mínimo (min) ao equipamento mais próximo. Unidades sem hexágono AOP ficam sem linha (nunca zero).
Saída: data/processed/acessibilidade/acess_2019.parquet e acess_decil_2019.parquet (por decil de renda dos hexágonos).
"""
import numpy as np
import pandas as pd
import geopandas as gpd

from pipeline.base import GEO
from pipeline.fontes import PROCESSED, REPO_ROOT

RAW = REPO_ROOT / "data" / "raw_aop"
TMP = GEO / "_tmp"
MODOS = {"tp": "public_transport", "auto": "car", "ape": "walk"}
MUNIS = {"spo": ("Sao_Paulo", ["public_transport", "car", "walk"]), "gua": ("Guarulhos", ["car", "walk"])}
COBERTURA_MIN, COBERTURA_MAX = 0.90, 1.25        # razão > 1,25: denominador censitário interpolado instável
MEDIDAS = {"cma30": "CMATT30", "cma60": "CMATT60", "cma90": "CMATT90", "cma60_saude": "CMAST60", "cma60_escola": "CMAET60",
           "tmi_saude": "TMIST", "tmi_escola": "TMIET"}


def _hex() -> gpd.GeoDataFrame:
    g = pd.concat([gpd.read_file(RAW / f"hex_grid_{m}.gpkg") for m in MUNIS], ignore_index=True)
    pop = pd.concat([pd.read_csv(RAW / f"population_2010_{m}.csv") for m in MUNIS], ignore_index=True)[["id_hex", "P001", "R003"]]
    g = g.merge(pop, on="id_hex", how="left")
    g["P001"] = g.P001.fillna(0)
    g = g.to_crs(31983)
    g["geometry"] = g.geometry.centroid
    return g[["id_hex", "P001", "R003", "geometry"]]


def _acesso() -> pd.DataFrame:
    partes = []
    for m, (_, modos) in MUNIS.items():
        for modo in modos:
            arq = RAW / f"access_2019_{modo}_{m}.csv"
            cols = [c for c in ["id_hex", "peak", *MEDIDAS.values()] if c in pd.read_csv(arq, nrows=0).columns]   # a pé/carro não têm todas as janelas
            d = pd.read_csv(arq, usecols=cols)
            d = d[d.peak == d.peak.max()]          # pico da manhã quando existe (tp, auto); a pé só tem um
            d["modo"] = {v: k for k, v in MODOS.items()}[modo]
            partes.append(d.drop(columns="peak"))
    a = pd.concat(partes, ignore_index=True)
    return a.replace([np.inf, -np.inf], np.nan)


def _camadas() -> dict[str, gpd.GeoDataFrame]:
    out = {}
    for arq, chave in (("amc146", ("amc146", 0)), ("amc75", ("amc75", 0)), ("muni", ("muni", 0)), ("sub", ("sub", 0)), ("zonas_2023", ("zona", 2023))):
        g = gpd.read_file(TMP / f"{arq}.geojson")[["codigo", "geometry"]]
        out[chave] = g
    return out


def agrega() -> tuple[pd.DataFrame, pd.DataFrame]:
    h, a = _hex(), _acesso()
    linhas, decis = [], []
    for (nivel, ed), camada in _camadas().items():
        j = gpd.sjoin(h, camada, predicate="within", how="inner")[["id_hex", "codigo", "P001", "R003"]]
        m = j.merge(a, on="id_hex")
        for modo, g in m.groupby("modo"):
            for nome, col in MEDIDAS.items():
                if col not in g or g[col].notna().sum() == 0:
                    continue
                v = g.dropna(subset=[col])
                w = v.groupby("codigo").apply(lambda x: pd.Series({"valor": np.average(x[col], weights=x.P001) if x.P001.sum() > 0 else x[col].mean(),
                                                                    "pop_hex": x.P001.sum(), "n_hex": len(x)}), include_groups=False).reset_index()
                w.insert(0, "medida", nome); w.insert(0, "modo", modo); w.insert(0, "edicao", ed); w.insert(0, "nivel", nivel)
                linhas.append(w)
    for modo, g in a.merge(h, on="id_hex").groupby("modo"):
        for nome, col in MEDIDAS.items():
            if col not in g or g[col].notna().sum() == 0:
                continue
            v = g.dropna(subset=[col, "R003"])
            d = v.groupby("R003").apply(lambda x: pd.Series({"valor": np.average(x[col], weights=x.P001) if x.P001.sum() > 0 else np.nan, "pop_hex": x.P001.sum()}), include_groups=False).reset_index()
            d.insert(0, "medida", nome); d.insert(0, "modo", modo)
            decis.append(d.rename(columns={"R003": "decil"}))
    u = pd.concat(linhas, ignore_index=True).dropna(subset=["valor"])
    # cobertura: população 2010 dos hexágonos AOP / população 2010 da unidade (Censo interpolado); só unidades >= 90 % cobertas
    c = pd.read_parquet(PROCESSED / "censo" / "censo_por_unidade.parquet")
    c = c[c.ano_censo == 2010][["nivel", "edicao", "codigo", "pop_total"]]
    u = u.merge(c, on=["nivel", "edicao", "codigo"], how="left")
    u["cobertura"] = u.pop_hex / u.pop_total
    u = u[(u.cobertura >= COBERTURA_MIN) & (u.cobertura <= COBERTURA_MAX)].drop(columns="pop_total")
    return u, pd.concat(decis, ignore_index=True)


def rodar() -> None:
    d = PROCESSED / "acessibilidade"; d.mkdir(exist_ok=True)
    u, dec = agrega()
    u.to_parquet(d / "acess_2019.parquet", index=False); dec.to_parquet(d / "acess_decil_2019.parquet", index=False)
    print("acess_2019:", len(u), u.groupby(["nivel", "modo"]).codigo.nunique().unstack().to_string())
    q = dec[(dec.medida == "cma60") & (dec.modo == "tp") & dec.decil.isin([1, 10])].set_index("decil").valor
    print("TP SP: empregos em 60 min — decil 1:", round(q.get(1, np.nan)), "| decil 10:", round(q.get(10, np.nan)))


if __name__ == "__main__":
    rodar()
