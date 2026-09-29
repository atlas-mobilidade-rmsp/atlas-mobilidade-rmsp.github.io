import json

import numpy as np
import pandas as pd
import pytest

from pipeline.edicoes import ANOS
from pipeline.fontes import PROCESSED
from pipeline.gravidade import calibrar, extremos, furness, mtl
from pipeline.build_serie import gini

needs = pytest.mark.skipif(not (PROCESSED / "serie" / "gravitacional_params.json").exists(), reason="rode gravidade/build_serie")


def _caso(n=12, seed=0):
    r = np.random.default_rng(seed)
    c = r.uniform(1, 30, (n, n)); c = (c + c.T) / 2
    O = r.uniform(10, 100, n); D = r.uniform(10, 100, n); D *= O.sum() / D.sum()
    return c, O, D


def test_furness_respeita_margens():
    c, O, D = _caso()
    T = furness(np.exp(-0.1 * c), O, D)
    assert np.allclose(T.sum(1), O, rtol=1e-5) and np.allclose(T.sum(0), D, rtol=1e-5)


def test_calibracao_reproduz_mtl():
    c, O, D = _caso()
    alvo = mtl(furness(np.exp(-0.2 * c), O, D), c)
    p, M = calibrar(c, O, D, alvo, "exp")
    assert abs(mtl(M, c) / alvo - 1) < 1e-3 and abs(p - 0.2) < 0.02


def test_excesso_limites():
    c, O, D = _caso(8)
    tmin, tmax = extremos(c, O, D)
    obs = furness(np.exp(-0.15 * c), O, D)
    assert mtl(tmin, c) <= mtl(obs, c) <= mtl(tmax, c)


def test_gini_igualdade_e_extremo():
    assert gini(np.ones(10), np.ones(10)) == pytest.approx(0, abs=1e-9)
    assert gini(np.array([0.0, 0, 0, 10]), np.ones(4)) > 0.7


@needs
def test_params_gravitacionais():
    p = json.loads((PROCESSED / "serie" / "gravitacional_params.json").read_text())["edicoes"]
    for a in ANOS:
        for nivel, r in p[str(a)].items():
            for imp in ("dist_km", "tempo_min"):
                x = r[imp]
                assert abs(x["exp"]["mtl_modelo"] / x["mtl_obs"] - 1) < 0.01, (a, nivel, imp)     # ±1 %
                if "t_min" in x:
                    assert x["t_min"] <= x["mtl_obs"] <= x["t_max"] and 0 <= x["excesso"] <= 1
                    assert 0 <= x["utilizacao_capacidade"] <= 1


@needs
@pytest.mark.parametrize("ano", ANOS)
def test_gravitacional_tabela(ano):
    g = pd.read_parquet(PROCESSED / str(ano) / "gravitacional.parquet")
    assert g.autocont.between(0, 1).all() and g.hansen_emp_exp_dist_km.ge(0).all()
    ind = pd.read_parquet(PROCESSED / str(ano) / "indicadores.parquet")
    a = ind[ind.nivel == "amc75"].set_index("codigo")
    b = g[g.nivel == "amc75"].set_index("codigo")
    # empregos do modelo ≈ empregos do indicador (mesma definição; só diferem pelos sem local de trabalho)
    assert abs(b.empregos_od.sum() / a.empregos_od.sum() - 1) < 0.03


@needs
def test_censo_e_cnefe():
    c = pd.read_parquet(PROCESSED / "censo" / "censo_por_unidade.parquet")
    tot = c[c.nivel == "muni"].groupby("ano_censo").pop_total.sum() / 1e6
    ref = {1970: 8.14, 1980: 12.59, 1991: 15.44, 2000: 17.88, 2010: 19.68, 2022: 20.73}
    for k, v in ref.items():
        assert abs(tot[k] / v - 1) < 0.005
    e = pd.read_parquet(PROCESSED / "cnefe" / "cnefe_por_unidade.parquet")
    a, m = e[e.nivel == "amc146"].n_enderecos.sum(), e[e.nivel == "muni"].n_enderecos.sum()
    assert abs(a / m - 1) < 0.02


@needs
def test_serie_sistema_e_unidades():
    s = pd.read_parquet(PROCESSED / "serie" / "sistema_serie.parquet")
    q = s[(s.medida == "ind_mob") & (s.universo == "edicao")].pivot(index="edicao", columns="categoria", values="valor")
    assert q.loc[1977, "q5"] > q.loc[1977, "q1"] and q.loc[2023, "q5"] / q.loc[2023, "q1"] < q.loc[1977, "q5"] / q.loc[1977, "q1"]   # compressão
    m = s[(s.medida == "divisao_modal") & (s.universo == "edicao")].groupby("edicao").valor.sum()
    assert np.allclose(m, 1, atol=1e-6)
    u = pd.read_parquet(PROCESSED / "serie" / "unidades_serie.parquet")
    assert set(u.nivel) == {"amc75", "amc146", "muni"} and u.edicao.nunique() == 6


def test_perguntas_json():
    import jsonschema
    from pipeline.build_perguntas import SCHEMA
    ps = json.loads((PROCESSED / "perguntas.json").read_text())
    assert len(ps) >= 20 and len({p["id"] for p in ps}) == len(ps)
    for p in ps:
        jsonschema.validate({k: v for k, v in p.items()}, {**SCHEMA, "properties": {**SCHEMA["properties"], "achado": {"type": "object"}}})
        assert "{" not in p["achado"]["texto"], p["slug"]            # nenhum placeholder sem resolver
        if p["status"] != "aguarda_dados":
            assert p["achado"]["valores"] and all(v["valor"] == v["valor"] for v in p["achado"]["valores"].values())


def test_aop_acessibilidade():
    u = pd.read_parquet(PROCESSED / "acessibilidade" / "acess_2019.parquet")
    assert u.cobertura.between(0.9, 1.25).all()
    assert set(u[u.nivel == "muni"].codigo) <= {"3550308", "3518800"}
    p = u[(u.nivel == "amc146") & (u.modo == "tp")].pivot_table(index="codigo", columns="medida", values="valor")
    assert (p.cma30 <= p.cma60 + 1e-6).all() and (p.cma60 <= p.cma90 + 1e-6).all()          # janelas cumulativas monotônicas
    d = pd.read_parquet(PROCESSED / "acessibilidade" / "acess_decil_2019.parquet")
    tp = d[(d.modo == "tp") & (d.medida == "cma60")].set_index("decil").valor
    assert tp.loc[10] > tp.loc[1]                                                             # ricos alcançam mais empregos por TP
