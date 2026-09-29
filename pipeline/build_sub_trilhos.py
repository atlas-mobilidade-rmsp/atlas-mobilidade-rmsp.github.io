"""F1 (cont.): nível `sub` (32 subprefeituras de SP + 38 municípios) e camada de trilhos.

Fonte: GeoSampa WFS (subprefeitura, linha_metro, linha_trem, estacao_*), baixados por geo/fetch_geosampa.sh
em data/geo/raw/. Achado de encaixe (docs/DECISOES.md): zonas 1997–2023 encaixam >= 98,6 % da área na
subprefeitura dominante; AMC-146 só 65 % e zonas 1977/1987 <= 83 % -> `sub` vale só para 1997+ e fica fora da série.
"""
import geopandas as gpd
import pandas as pd

from pipeline.build_geo import GEO, TMP, centroides, setores_pontos
from pipeline.fontes import PROCESSED, ZONAS_GPKG

RAW = PROCESSED.parent / "geo/raw"
ANOS_SUB = (1997, 2007, 2017, 2023)


def sub_layer() -> gpd.GeoDataFrame:
    s = gpd.read_file(RAW / "subprefeitura.geojson").to_crs(31983)
    s = s.assign(codigo="SP-" + s.cd_subprefeitura.astype(str).str.zfill(2), nome=s.nm_subprefeitura.str.title(),
                 muni_ibge="3550308")[["codigo", "nome", "muni_ibge", "geometry"]]
    m = gpd.read_file(TMP / "muni.geojson")
    m = m[m.nome != "São Paulo"].assign(muni_ibge=lambda d: d.codigo)[["codigo", "nome", "muni_ibge", "geometry"]]
    return pd.concat([s, m], ignore_index=True).pipe(gpd.GeoDataFrame, crs=31983)


def zona_para_sub(sub: gpd.GeoDataFrame) -> pd.DataFrame:
    """Subprefeitura/município dominante por sobreposição de área, para cada zona 1997+."""
    linhas = []
    for ano in ANOS_SUB:
        z = gpd.read_file(ZONAS_GPKG, layer=f"zonas_{ano}")
        z["codigo"] = z.zona_id.astype(str)
        z["a"] = z.geometry.area
        ov = gpd.overlay(z[["codigo", "a", "geometry"]], sub[["codigo", "geometry"]].rename(columns={"codigo": "sub"}),
                         how="intersection", keep_geom_type=False)
        ov["ar"] = ov.area
        b = ov.sort_values("ar", ascending=False).drop_duplicates("codigo")
        b["encaixe"] = b.ar / b.a
        linhas.append(b.assign(ano=ano)[["ano", "codigo", "sub", "encaixe"]].rename(columns={"codigo": "zona"}))
    return pd.concat(linhas, ignore_index=True)


def trilhos() -> gpd.GeoDataFrame:
    partes = []
    for arq, modo in (("linha_metro", "metro"), ("linha_trem", "trem")):
        g = gpd.read_file(RAW / f"{arq}.geojson").to_crs(31983)
        g["modo"] = modo
        g["linha"] = g.get("nm_linha_metro_trem", "")
        g["empresa"] = g.get("nm_empresa_metro_trem", "")
        partes.append(g[["modo", "linha", "empresa", "geometry"]])
    return pd.concat(partes, ignore_index=True).pipe(gpd.GeoDataFrame, crs=31983)


def estacoes() -> gpd.GeoDataFrame:
    partes = []
    for arq, modo in (("estacao_metro", "metro"), ("estacao_trem", "trem")):
        g = gpd.read_file(RAW / f"{arq}.geojson").to_crs(31983)
        g["modo"], g["nome"], g["linha"] = modo, g["nm_estacao_metro_trem"], g["nm_linha_metro_trem"]
        g["situacao"] = g["tx_situacao_metro_trem"]
        partes.append(g[["modo", "nome", "linha", "situacao", "geometry"]])
    return pd.concat(partes, ignore_index=True).pipe(gpd.GeoDataFrame, crs=31983)


def main() -> None:
    sub = sub_layer()
    sub.to_file(TMP / "sub.geojson", driver="GeoJSON")
    zs = zona_para_sub(sub)
    zs.to_parquet(GEO / "zona_para_sub.parquet", index=False)
    c = pd.read_parquet(GEO / "centroides.parquet")
    c = c[c.nivel != "sub"]
    cs = centroides({"sub": sub[["codigo", "geometry"]]}, setores_pontos())
    pd.concat([c, cs], ignore_index=True).to_parquet(GEO / "centroides.parquet", index=False)
    u = pd.read_parquet(GEO / "unidades_ref_geo.parquet")
    u = u[u.nivel != "sub"]
    us = pd.DataFrame(dict(nivel="sub", edicao=0, codigo=sub.codigo, nome=sub.nome, muni_ibge=sub.muni_ibge,
                           area_km2=sub.geometry.area / 1e6))
    pd.concat([u, us], ignore_index=True).to_parquet(GEO / "unidades_ref_geo.parquet", index=False)
    t = trilhos()
    t.to_file(TMP / "contexto_trilhos.geojson", driver="GeoJSON")
    e = estacoes()
    e.to_file(TMP / "contexto_estacoes.geojson", driver="GeoJSON")
    print("sub:", len(sub), "| zonas->sub:", zs.groupby("ano").encaixe.agg(["size", "mean", lambda s: (s < 0.9).sum()]).round(3).to_dict("index"))
    print("trilhos:", len(t), "estacoes:", len(e))


if __name__ == "__main__":
    main()
