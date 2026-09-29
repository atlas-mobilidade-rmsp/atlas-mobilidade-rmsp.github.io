import pandas as pd
import pytest

from pipeline.edicoes import ANOS, MIN_N_CELULA, MIN_N_DETALHE
from pipeline.fontes import PROCESSED
from pipeline.precisao_regras import min_n_fluxo, precisao, sql_cv

# totais oficiais (milhões) — docs/dicionario_serie_historica.md do laboratório
OFICIAL = {1977: (10.28, 21.30, 2.48), 1987: (14.25, 29.40, 3.32), 1997: (16.79, 31.43, 4.26),
           2007: (19.53, 38.09, 5.51), 2017: (20.82, 42.01, 6.94), 2023: (21.24, 35.66, 7.83)}
pytestmark = pytest.mark.skipif(not (PROCESSED / "2023" / "indicadores.parquet").exists(), reason="rode pipeline/nucleo.py")


@pytest.mark.parametrize("ano", ANOS)
def test_totais_oficiais(ano):
    ind = pd.read_parquet(PROCESSED / str(ano) / "indicadores.parquet")
    m = ind[ind.nivel == "muni"]
    pop, via, dom = OFICIAL[ano]
    # tolerância 0,3 % (números oficiais arredondados a 2 casas em milhões)
    assert abs(m["pop"].sum() / 1e6 / pop - 1) < 0.003
    assert abs(m["viagens"].sum() / 1e6 / via - 1) < 0.003
    assert abs(m["dom"].sum() / 1e6 / dom - 1) < 0.003


@pytest.mark.parametrize("ano", ANOS)
def test_niveis_fecham(ano):
    ind = pd.read_parquet(PROCESSED / str(ano) / "indicadores.parquet")
    for c in ("pop", "viagens"):
        t = ind.groupby("nivel")[c].sum()
        # AMC-75 cobre só a área de 1977 (menor que a RMSP inteira a partir de 1987): fica de fora da igualdade
        cheio = t.drop("amc75")
        assert (cheio.max() - cheio.min()) / cheio.max() < 0.005, (c, t.to_dict())
        if ano >= 1987:
            assert 0.95 < t["amc75"] / cheio.max() <= 1.0001


@pytest.mark.parametrize("ano", ANOS)
def test_fluxos_piso_e_ief(ano):
    for f in (PROCESSED / str(ano)).glob("fluxos_[a-z]*.parquet"):
        nivel = f.stem.split("_", 1)[1]
        if nivel == "dim":
            continue
        df = pd.read_parquet(f)
        assert (df.n >= min_n_fluxo(nivel)).all()
        assert df.ief_par.dropna().between(-1, 1).all()
        assert (df.total > 0).all()


@pytest.mark.parametrize("ano", ANOS)
def test_casa_trab_margens_coerentes(ano):
    """A matriz pendular é assimétrica por natureza (correlação de T_ij com T_ji é baixa); o que deve ser coerente é a
    correlação entre saídas e entradas por unidade (O_i x D_i) — polos de moradia e de emprego se sobrepõem."""
    df = pd.read_parquet(PROCESSED / str(ano) / "fluxos_amc75.parquet")
    d = df[df.tipo == "casa_trab"]
    o, dd = d.groupby("origem").total.sum(), d.groupby("destino").total.sum()
    idx = o.index.intersection(dd.index)
    assert pd.Series(o[idx]).corr(pd.Series(dd[idx])) > 0.7


def test_regras():
    assert precisao(3, 5) == "sem_estimativa" and precisao(10, 10) == "boa"
    assert precisao(10, 20) == "cautela" and precisao(10, 40) == "baixa"
    assert "sqrt" in sql_cv("fe")


def test_pares_serie():
    ps = pd.read_parquet(PROCESSED / "serie" / "pares_serie.parquet")
    assert set(ps.status) <= {"publicado", "n_insuficiente", "nao_existia", "fora_area_1977"}
    a146 = ps[(ps.nivel == "amc146") & (ps.edicao == 1977)]
    assert (a146.status == "nao_existia").all()
    pub = ps[ps.status == "publicado"]
    assert pub.total.notna().all() and (pub.n >= MIN_N_CELULA).all()
    # coerente com fluxos_amc146 de 2023
    f = pd.read_parquet(PROCESSED / "2023" / "fluxos_amc146.parquet")
    p23 = ps[(ps.nivel == "amc146") & (ps.edicao == 2023) & (ps.status == "publicado")]
    assert len(p23) == len(f)
    assert abs(p23.total.sum() / f.total.sum() - 1) < 1e-9
