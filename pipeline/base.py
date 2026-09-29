"""Tabelas-base em DuckDB (memória): pessoas/viagens com a unidade territorial de cada ponta em todos os níveis.

Lê a série harmonizada do laboratório (fontes.SERIE_DB); nunca escreve microdado.
Colunas de unidade (VARCHAR): u_home_<nivel>, u_trab_<nivel>, u_esc_<nivel>, u_o_<nivel>, u_d_<nivel>.
Códigos: zona = zona OD do ano; amc146/amc75 = AMC; muni = IBGE (0 -> NULL); sub = SP-nn/IBGE via zona_para_sub (1997+).
"""
import duckdb
import pandas as pd

from pipeline.fontes import PROCESSED, SERIE_DB

GEO = PROCESSED / "geo"
NIVEIS = ("zona", "amc146", "amc75", "sub", "muni")


def _u(expr_zona, expr_a146, expr_a75, expr_muni, sub_alias):
    return {
        "zona": f"cast({expr_zona} as varchar)",
        "amc146": f"cast({expr_a146} as varchar)",
        "amc75": f"cast({expr_a75} as varchar)",
        "muni": f"cast(nullif({expr_muni},0) as varchar)",
        "sub": f"{sub_alias}.sub",
    }


def conectar() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"attach '{SERIE_DB}' as od (read_only)")
    zs = pd.read_parquet(GEO / "zona_para_sub.parquet")
    zs["zona"] = zs["zona"].astype("int16")
    con.register("zsub_df", zs)
    con.execute("create table zsub as select cast(ano as smallint) ano, cast(zona as smallint) zona, sub from zsub_df")

    # renda familiar per capita r2023 -> quintil ponderado por pessoa, por ano
    con.execute("""create table pess as
      select p.ano, p.id_pess, p.id_dom, p.id_fam, p.fe_pess, p.idade, p.sexo, p.grau_ins_4, p.cond_ativ, p.setor_ativ,
             f.renda_fa_r2023 / nullif(f.n_pessoas,0) as rpc,
             d.zona as z_home, d.dom_amc_8723 as a146_home, d.dom_amc_7723 as a75_home, d.muni_ibge as m_home,
             p.zona_trab1 as z_trab, p.trab1_amc_8723 as a146_trab, p.trab1_amc_7723 as a75_trab, p.muni_trab1_ibge as m_trab,
             p.zona_esc as z_esc, p.esc_amc_8723 as a146_esc, p.esc_amc_7723 as a75_esc, p.muni_esc_ibge as m_esc
      from od.pessoas p join od.domicilios d using (ano, id_dom) left join od.familias f using (ano, id_dom, id_fam)""")
    con.execute("""create table pess_q as
        select * exclude (cum, tot), least(5, 1 + cast(floor(5 * (cum - fe_pess / 2) / tot) as int)) as quintil from (
          select *, sum(fe_pess) over (partition by ano order by rpc, id_pess) as cum,
                 sum(fe_pess) over (partition by ano) as tot from pess where rpc is not null)
        union all by name select *, cast(null as int) as quintil from pess where rpc is null""")
    con.execute("drop table pess; alter table pess_q rename to pess")
    return con


def cols_pessoa() -> str:
    hs = {}
    for papel, (z, a1, a7, m) in {"home": ("z_home", "a146_home", "a75_home", "m_home"),
                                   "trab": ("z_trab", "a146_trab", "a75_trab", "m_trab"),
                                   "esc": ("z_esc", "a146_esc", "a75_esc", "m_esc")}.items():
        sub = f"s_{papel}"
        for nv, e in _u(f"p.{z}", f"p.{a1}", f"p.{a7}", f"p.{m}", sub).items():
            hs[f"u_{papel}_{nv}"] = e
    return ", ".join(f"{e} as {k}" for k, e in hs.items())


def preparar(con) -> None:
    con.execute(f"""create table pessoa as select p.*, {cols_pessoa()} from pess p
      left join zsub s_home on s_home.ano = p.ano and s_home.zona = p.z_home
      left join zsub s_trab on s_trab.ano = p.ano and s_trab.zona = p.z_trab
      left join zsub s_esc  on s_esc.ano  = p.ano and s_esc.zona  = p.z_esc""")
    dm = _u("d.zona", "d.dom_amc_8723", "d.dom_amc_7723", "d.muni_ibge", "sh")
    con.execute(f"""create table domicilio as select d.ano, d.id_dom, d.fe_dom, {", ".join(f"{e} as u_home_{k}" for k, e in dm.items())}
        from od.domicilios d left join zsub sh on sh.ano = d.ano and sh.zona = d.zona""")
    o = _u("v.zona_o", "v.o_amc_8723", "v.o_amc_7723", "v.muni_o_ibge", "so")
    d = _u("v.zona_d", "v.d_amc_8723", "v.d_amc_7723", "v.muni_d_ibge", "sd")
    cols = ", ".join([f"{e} as u_o_{k}" for k, e in o.items()] + [f"{e} as u_d_{k}" for k, e in d.items()])
    con.execute(f"""create table viagem as select v.ano, v.id_pess, v.id_dom, v.fe_via, v.motivo_o, v.motivo_d,
        v.modoprin, v.modo_agreg, v.h_saida, v.duracao, {cols}
        from od.viagens v left join zsub so on so.ano = v.ano and so.zona = v.zona_o
                          left join zsub sd on sd.ano = v.ano and sd.zona = v.zona_d""")
    # unidade de residência do viajante na tabela de viagens
    hcols = ", ".join(f"p.u_home_{n} as u_home_{n}" for n in NIVEIS)
    con.execute(f"""create table viagem_h as select v.*, {hcols}, p.sexo, p.idade, p.quintil, p.grau_ins_4, p.setor_ativ, p.cond_ativ
        from viagem v join pessoa p on p.ano = v.ano and p.id_pess = v.id_pess""")


def niveis_da_edicao(ano: int, niveis=NIVEIS) -> list[str]:
    """amc146 só existe em 1987+; sub só em 1997+ (docs/DECISOES.md)."""
    return [n for n in niveis if not (n == "amc146" and ano < 1987) and not (n == "sub" and ano < 1997)]
