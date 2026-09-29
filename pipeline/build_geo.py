"""F1 — geo: GeoJSON (EPSG:31983, metros) por nível + centroides ponderados por domicílios (Censo 2022).

Saída em data/processed/geo/_tmp/*.geojson (ignorado) e centroides.parquet + unidades_ref_geo.parquet.
O TopoJSON final é gerado por geo/build.sh (mapshaper). Dado geográfico público, sem microdado.
"""
import duckdb
import geopandas as gpd
import pandas as pd
from shapely import wkb

from pipeline.fontes import CENSO_DB, PROCESSED, ZONAS_GPKG, verificar

GEO = PROCESSED / "geo"
TMP = GEO / "_tmp"
ANOS = (1977, 1987, 1997, 2007, 2017, 2023)


def setores_pontos() -> gpd.GeoDataFrame:
    """Ponto representativo de cada setor 2022 (interno ao polígono) com peso = domicílios (v0002)."""
    con = duckdb.connect(str(CENSO_DB), read_only=True)
    df = con.execute("""select s.cd_setor, s.cd_mun, s.nm_mun, coalesce(s.v0002,0) as w,
                        ST_AsWKB(m.geom) as g from setores_2022 s join malha_2022 m using(cd_setor)""").df()
    geoms = [wkb.loads(bytes(b)) for b in df.pop("g")]
    return gpd.GeoDataFrame(df, geometry=geoms, crs=31983)


def muni_layer(gs: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    m = gs.dissolve(by=["cd_mun", "nm_mun"], as_index=False, aggfunc={"w": "sum"})
    m["nivel"], m["codigo"] = "muni", m["cd_mun"].astype(str)
    m["nome"] = m["nm_mun"]
    m["geometry"] = m.geometry.buffer(0)
    return m[["nivel", "codigo", "nome", "geometry"]]


def centroides(camadas: dict[str, gpd.GeoDataFrame], pts: gpd.GeoDataFrame) -> pd.DataFrame:
    """Média ponderada dos pontos de setor dentro de cada unidade; fallback: ponto representativo."""
    p = pts.copy()
    p["geometry"] = p.geometry.representative_point()
    p["x_"], p["y_"] = p.geometry.x, p.geometry.y
    saida = []
    for chave, g in camadas.items():
        g = g[["codigo", "geometry"]].reset_index(drop=True)
        j = gpd.sjoin(p[["w", "x_", "y_", "geometry"]], g, predicate="within", how="inner")
        j["wx"], j["wy"] = j.w * j.x_, j.w * j.y_
        a = j.groupby("codigo").agg(w=("w", "sum"), wx=("wx", "sum"), wy=("wy", "sum")).reset_index()
        a["x"], a["y"] = a.wx / a.w, a.wy / a.w
        base = g.merge(a[["codigo", "w", "x", "y"]], on="codigo", how="left")
        rp = base.geometry.representative_point()
        sem = base.x.isna() | (base.w <= 0)
        base.loc[sem, "x"], base.loc[sem, "y"] = rp[sem].x, rp[sem].y
        base["fonte_centroide"] = "domicilios_2022"
        base.loc[sem, "fonte_centroide"] = "ponto_representativo"
        base["nivel"] = chave.split(":")[0]
        base["edicao"] = int(chave.split(":")[1]) if ":" in chave else 0
        gg = gpd.GeoSeries(gpd.points_from_xy(base.x, base.y), crs=31983).to_crs(4326)
        base["lon"], base["lat"] = gg.x, gg.y
        saida.append(base[["nivel", "edicao", "codigo", "lon", "lat", "x", "y", "w", "fonte_centroide"]]
                     .rename(columns={"w": "domicilios_2022"}))
    return pd.concat(saida, ignore_index=True)


def main() -> None:
    verificar()
    TMP.mkdir(parents=True, exist_ok=True)
    pts = setores_pontos()
    camadas = {}
    for ano in ANOS:
        z = gpd.read_file(ZONAS_GPKG, layer=f"zonas_{ano}")
        z["codigo"] = z["zona_id"].astype(str)
        z["nome"] = z["zona_nome"]
        z["geometry"] = z.geometry.buffer(0)
        camadas[f"zona:{ano}"] = z[["codigo", "nome", "municipio_nome", "geometry"]]
        z[["codigo", "nome", "municipio_nome", "geometry"]].to_file(TMP / f"zonas_{ano}.geojson", driver="GeoJSON")
    for nome, col in (("amc_8723", "amc146"), ("amc_7723", "amc75")):
        a = gpd.read_file(ZONAS_GPKG, layer=nome)
        a["codigo"] = a[nome].astype(str)
        a["nome"] = "AMC " + a["codigo"]
        a["geometry"] = a.geometry.buffer(0)
        camadas[f"{col}"] = a[["codigo", "nome", "geometry"]]
        a[["codigo", "nome", "geometry"]].to_file(TMP / f"{col}.geojson", driver="GeoJSON")
    mu = muni_layer(pts)
    camadas["muni"] = mu
    mu[["codigo", "nome", "geometry"]].to_file(TMP / "muni.geojson", driver="GeoJSON")
    c = centroides(camadas, pts)
    c.to_parquet(GEO / "centroides.parquet", index=False)
    unidades_ref().to_parquet(GEO / "unidades_ref_geo.parquet", index=False)
    print(c.groupby(["nivel", "edicao"]).agg(n=("codigo", "size"), sem_dom=("fonte_centroide", lambda s: (s != "domicilios_2022").sum())))



def unidades_ref() -> pd.DataFrame:
    """nivel, edicao, codigo, nome, muni_ibge, amc_8723, amc_7723, area_km2, na_area_1977."""
    import unicodedata
    from pipeline.fontes import ZONA_PARA_AMC
    ALIAS = {"SAO BERNARDO": "SAO BERNARDO DO CAMPO", "SALOSOPOLIS": "SALESOPOLIS", "SANTANA DO PARNAIBA": "SANTANA DE PARNAIBA",
             "PIRAPORA BOM JESUS": "PIRAPORA DO BOM JESUS", "EMBU": "EMBU DAS ARTES", "EMBU GUACU": "EMBU-GUACU",
             "BIRITIBA-MIRIM": "BIRITIBA MIRIM"}
    def norm(s):
        t = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper().strip()
        return ALIAS.get(t, t)
    mu = gpd.read_file(TMP / "muni.geojson")
    ibge = {norm(n): c for c, n in zip(mu.codigo, mu.nome)}
    ibge = {**ibge, **{k: v for k, v in ibge.items()}}
    amc = pd.read_csv(ZONA_PARA_AMC, dtype=str)
    linhas = []
    for ano in ANOS:
        z = gpd.read_file(TMP / f"zonas_{ano}.geojson")
        m = amc[amc.ano == str(ano)].set_index("zona")
        for cod, nome, mn, geom in zip(z.codigo, z.nome, z.municipio_nome, z.geometry):
            linhas.append(dict(nivel="zona", edicao=ano, codigo=cod, nome=nome, muni_ibge=ibge.get(norm(mn)),
                               amc_8723=m.amc_8723.get(cod), amc_7723=m.amc_7723.get(cod), area_km2=geom.area / 1e6))
    for nivel, arq in (("amc146", "amc146"), ("amc75", "amc75"), ("muni", "muni")):
        g = gpd.read_file(TMP / f"{arq}.geojson")
        for cod, nome, geom in zip(g.codigo, g.nome, g.geometry):
            linhas.append(dict(nivel=nivel, edicao=0, codigo=cod, nome=nome, area_km2=geom.area / 1e6, muni_ibge=cod if nivel == "muni" else None))
    u = pd.DataFrame(linhas)
    a75 = set(gpd.read_file(TMP / "amc75.geojson").codigo)
    # nome legível das AMC: "AMC n · município dominante" (por área das zonas de 2023)
    z23 = u[(u.nivel == "zona") & (u.edicao == 2023)]
    nm_muni = dict(zip(mu.codigo, mu.nome))
    for nivel, col in (("amc146", "amc_8723"), ("amc75", "amc_7723")):
        dom = (z23.dropna(subset=[col]).groupby([col, "muni_ibge"]).area_km2.sum().reset_index()
               .sort_values("area_km2", ascending=False).drop_duplicates(col).set_index(col).muni_ibge)
        maior_zona = z23.dropna(subset=[col]).sort_values("area_km2", ascending=False).drop_duplicates(col).set_index(col).nome
        m = u.nivel == nivel

        def rot(c):
            mn = nm_muni.get(dom.get(c), "")
            return f"AMC {c} · {maior_zona.get(c, '')} ({mn})" if mn == "São Paulo" else f"AMC {c} · {mn}"
        u.loc[m, "nome"] = [rot(c) for c in u.loc[m, "codigo"]]
    u["na_area_1977"] = (u.nivel == "amc75") | (u.amc_7723.isin(a75))
    return u


if __name__ == "__main__":
    main()
