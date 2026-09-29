import subprocess
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from pipeline.fontes import PROCESSED

GEO = PROCESSED / "geo"
RAIZ = Path(__file__).resolve().parents[2]


def decodifica(nome: str) -> gpd.GeoDataFrame:
    """Decodifica com topojson-client (a lib do front-end), não com GDAL."""
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "x.geojson"
        subprocess.run(["node", str(RAIZ / "geo/decode_topojson.mjs"), str(GEO / f"{nome}.topojson"), str(out)], check=True)
        return gpd.read_file(out)
ESPERADO = {"zonas_1977": 243, "zonas_1987": 254, "zonas_1997": 389, "zonas_2007": 460,
            "zonas_2017": 517, "zonas_2023": 527, "amc146": 146, "amc75": 75, "muni": 39}
CENT = {"zonas_1977": ("zona", 1977), "zonas_1987": ("zona", 1987), "zonas_1997": ("zona", 1997),
        "zonas_2007": ("zona", 2007), "zonas_2017": ("zona", 2017), "zonas_2023": ("zona", 2023),
        "amc146": ("amc146", 0), "amc75": ("amc75", 0), "muni": ("muni", 0)}


@pytest.mark.parametrize("nome,n", ESPERADO.items())
def test_camada_e_centroides(nome, n):
    g = decodifica(nome)
    assert len(g) == n
    # Autointerseções residuais (bowties de poucos m² pós-simplificação) toleradas até 1 % das
    # feições e 0,2 % da área; o que importa ao deck.gl é a triangulação (earcut) abaixo.
    assert (~g.geometry.is_valid).mean() <= 0.01
    orig = gpd.read_file(GEO / "_tmp" / f"{nome}.geojson") if (GEO / "_tmp" / f"{nome}.geojson").exists() else None
    if orig is not None:
        assert abs(g.area.sum() / orig.area.sum() - 1) < 0.002
    with tempfile.TemporaryDirectory() as d:
        gj = Path(d) / "x.geojson"
        g.to_file(gj, driver="GeoJSON")
        r = subprocess.run(["node", str(RAIZ / "geo/validate_earcut.mjs"), str(gj)], capture_output=True, text=True, check=True)
        import json
        ruins = [f for f in json.loads(r.stdout or "[]") if f["desvio_area"] > 0.05 or f["fora_do_poligono"] > 0]
        assert not ruins, ruins
    ids = set(g["codigo"].astype(str)) if "codigo" in g else set(g["id"].astype(str))
    c = pd.read_parquet(GEO / "centroides.parquet")
    nivel, ed = CENT[nome]
    cc = c[(c.nivel == nivel) & (c.edicao == ed)]
    assert set(cc.codigo) == ids and cc.codigo.is_unique


def test_metros_e_wgs_consistentes():
    m = gpd.read_file(GEO / "muni.topojson").set_crs(31983)
    w = gpd.read_file(GEO / "muni_wgs.topojson").set_crs(4326)
    assert m.total_bounds[0] > 1e5                       # metros
    assert -47.5 < w.total_bounds[0] < -45.5 and -24.5 < w.total_bounds[1] < -23    # RMSP
    a1, a2 = m.area.sum(), w.to_crs(31983).area.sum()
    assert abs(a1 - a2) / a1 < 0.005


def test_centroides_dentro_da_caixa():
    c = pd.read_parquet(GEO / "centroides.parquet")
    assert c.x.between(2e5, 5e5).all() and c.y.between(7.3e6, 7.5e6).all()
    assert (c.fonte_centroide == "domicilios_2022").mean() > 0.99


def test_unidades_ref():
    u = pd.read_parquet(GEO / "unidades_ref_geo.parquet")
    assert len(u) == 2720
    z = u[u.nivel == "zona"]
    assert z.muni_ibge.notna().all() and z.area_km2.gt(0).all()
    assert z[z.edicao >= 1987].amc_8723.notna().all()
    assert u[u.nivel == "muni"].muni_ibge.nunique() == 39


def test_sub_e_trilhos():
    c = pd.read_parquet(GEO / "centroides.parquet")
    assert (c.nivel == "sub").sum() == 70
    s = decodifica("sub")
    assert len(s) == 70 and s.codigo.str.startswith("SP-").sum() == 32
    zs = pd.read_parquet(GEO / "zona_para_sub.parquet")
    assert set(zs.ano) == {1997, 2007, 2017, 2023}
    assert zs.groupby("ano").encaixe.mean().min() > 0.98      # 1977/1987 e AMC-146 não encaixam (DECISOES.md)
    assert len(decodifica("contexto_trilhos")) >= 6 and len(decodifica("contexto_estacoes")) > 100
