"""F4 — indicadores de sistema por edição (RMSP inteira), em dois universos: `edicao` (área pesquisada) e
`area1977` (só residentes na área comparável de 1977, AMC-75). Saída: <ano>/sistema.parquet (formato longo)."""
import pandas as pd

from pipeline.base import conectar, preparar
from pipeline.edicoes import ANOS, MIN_N_CELULA
from pipeline.fontes import PROCESSED

UNIVERSOS = {"edicao": "true", "area1977": "u_home_amc75 is not null"}


def extras(con, ano: int, uni: str, filtro: str) -> list:
    """Medidas para as perguntas (F5): por quintil, sexo, idade; modos emergentes; pico; pobreza de tempo."""
    L = []
    q = "coalesce('q'||cast(quintil as varchar),'nd')"
    # divisão modal por quintil: coletivo e individual motorizado (% das viagens)
    r = con.execute(f"""select {q} c, sum(fe_via) filter (where modo_agreg=1)/sum(fe_via) col, sum(fe_via) filter (where modo_agreg=2)/sum(fe_via) ind,
        sum(fe_via) filter (where modo_agreg=4)/sum(fe_via) ape, count(*) n from viagem_h where ano={ano} and {filtro} group by 1""").df()
    for x in r.itertuples():
        L += [(ano, uni, "coletivo_q", x.c, x.col, x.n), (ano, uni, "individual_q", x.c, x.ind, x.n), (ano, uni, "ape_q", x.c, x.ape, x.n)]
    # modos emergentes (modoprin: 7 táxi/aplicativo, 8 moto): % das viagens
    r = con.execute(f"""select sum(fe_via) filter (where modoprin=7)/sum(fe_via) app, sum(fe_via) filter (where modoprin=8)/sum(fe_via) moto,
        count(*) filter (where modoprin=7) n7, count(*) filter (where modoprin=8) n8 from viagem_h where ano={ano} and {filtro}""").df().iloc[0]
    L += [(ano, uni, "pct_taxi_app", "todos", r.app, int(r.n7)), (ano, uni, "pct_moto", "todos", r.moto, int(r.n8))]
    # mobilidade por sexo, imobilidade por sexo e por grupo etário
    for cat, expr in (("masculino", "sexo=1"), ("feminino", "sexo=2")):
        pop = con.execute(f"select sum(fe_pess), count(*) from pessoa where ano={ano} and {filtro} and {expr}").fetchone()
        v = con.execute(f"select sum(fe_via), count(*), sum(fe_via) filter (where motivo_d in (5,6))/sum(fe_via), sum(fe_via) filter (where motivo_d in (1,2,3))/sum(fe_via) from viagem_h where ano={ano} and {filtro} and {expr}").fetchone()
        im = con.execute(f"select sum(fe_pess) filter (where idade>=15 and id_pess not in (select id_pess from viagem where ano={ano})) / sum(fe_pess) filter (where idade>=15), count(*) filter (where idade>=15) from pessoa where ano={ano} and {filtro} and {expr}").fetchone()
        L += [(ano, uni, "ind_mob_sexo", cat, v[0] / pop[0], v[1]), (ano, uni, "cuidado_sexo", cat, v[2], v[1]), (ano, uni, "trabalho_sexo", cat, v[3], v[1]), (ano, uni, "imob_sexo", cat, im[0], im[1])]
    for cat, expr in (("15-59", "idade between 15 and 59"), ("60+", "idade>=60")):
        pop = con.execute(f"select sum(fe_pess), count(*) from pessoa where ano={ano} and {filtro} and {expr}").fetchone()
        v = con.execute(f"select sum(fe_via), count(*) from viagem_h where ano={ano} and {filtro} and {expr}").fetchone()
        im = con.execute(f"select sum(fe_pess) filter (where id_pess not in (select id_pess from viagem where ano={ano}))/sum(fe_pess) from pessoa where ano={ano} and {filtro} and {expr}").fetchone()
        L += [(ano, uni, "ind_mob_idade", cat, v[0] / pop[0], v[1]), (ano, uni, "imob_idade", cat, im[0], pop[1])]
    # trabalho em casa / sem local fixo / híbrido (% dos ocupados; 2007+, híbrido só 2023)
    if ano >= 2007:
        r = con.execute(f"""select sum(fe_pess) filter (where trab_re=1)/sum(fe_pess), sum(fe_pess) filter (where trab_re=3)/sum(fe_pess),
            sum(fe_pess) filter (where hibrido)/sum(fe_pess), count(*) from pessoa where ano={ano} and {filtro} and cond_ativ=1""").fetchone()
        L += [(ano, uni, "trab_domicilio", "todos", r[0], r[3]), (ano, uni, "sem_local_fixo", "todos", r[1], r[3])]
        if ano == 2023:
            L.append((ano, uni, "trab_hibrido", "todos", r[2], r[3]))
    # raça/cor e mudança de uso do transporte na pandemia (só 2023): grupos brancos / pretos e pardos
    if ano == 2023:
        grupos = {"branca": "raca=1", "preta_parda": "raca in (2,4)"}
        for cat, expr in grupos.items():
            pop = con.execute(f"select sum(fe_pess), count(*) from pessoa where ano={ano} and {filtro} and {expr}").fetchone()
            v = con.execute(f"select sum(fe_via), count(*), sum(fe_via) filter (where modo_agreg=1)/sum(fe_via) from viagem_h v join pessoa p using (ano, id_pess) where v.ano={ano} and {filtro.replace('u_home_amc75','v.u_home_amc75')} and {expr.replace('raca','p.raca')}").fetchone()
            im = con.execute(f"select sum(fe_pess) filter (where idade>=15 and id_pess not in (select id_pess from viagem where ano={ano}))/sum(fe_pess) filter (where idade>=15), count(*) filter (where idade>=15) from pessoa where ano={ano} and {filtro} and {expr}").fetchone()
            tt = con.execute(f"select sum(fe_via*duracao)/sum(fe_via), count(*) from viagem_h v join pessoa p using (ano, id_pess) where v.ano={ano} and {filtro.replace('u_home_amc75','v.u_home_amc75')} and {expr.replace('raca','p.raca')} and v.motivo_o=8 and v.motivo_d in (1,2,3) and v.duracao>0").fetchone()
            rq = con.execute(f"select avg(quintil) filter (where quintil is not null) from pessoa where ano={ano} and {filtro} and {expr}").fetchone()[0]
            L += [(ano, uni, "ind_mob_raca", cat, v[0] / pop[0], v[1]), (ano, uni, "imob_raca", cat, im[0], im[1]), (ano, uni, "coletivo_raca", cat, v[2], v[1]),
                  (ano, uni, "tempo_trab_raca", cat, tt[0], tt[1]), (ano, uni, "quintil_medio_raca", cat, rq, pop[1]), (ano, uni, "pop_raca", cat, pop[0], pop[1])]
        pm = con.execute(f"select sum(fe_pess) filter (where mudou_pandemia)/sum(fe_pess), count(*) from pessoa where ano={ano} and {filtro}").fetchone()
        L.append((ano, uni, "mudou_transp_pandemia", "todos", pm[0], pm[1]))
    # picos e pobreza de tempo (minutos de viagem por pessoa-dia, por quintil; só quem viaja e média geral)
    r = con.execute(f"select sum(fe_via) filter (where h_saida between 6 and 8)/sum(fe_via), sum(fe_via) filter (where h_saida between 16 and 19)/sum(fe_via), count(*) from viagem_h where ano={ano} and {filtro}").fetchone()
    L += [(ano, uni, "pico_manha", "todos", r[0], r[2]), (ano, uni, "pico_tarde", "todos", r[1], r[2])]
    r = con.execute(f"""select {q} c, sum(fe_via*duracao)/sum(fe_via) filter (where duracao is not null) m_viag, count(*) n from viagem_h where ano={ano} and {filtro} and duracao is not null group by 1""").df()
    dia = con.execute(f"""select {q} c, sum(v.t*p.fe_pess)/sum(p.fe_pess) t, count(*) n from pessoa p join (select id_pess, sum(duracao) t from viagem where ano={ano} and duracao is not null group by 1) v using(id_pess)
        where p.ano={ano} and {filtro.replace('u_home_amc75','p.u_home_amc75')} group by 1""").df()
    tot = con.execute(f"select sum(fe_pess) from pessoa where ano={ano} and {filtro}").fetchone()[0]
    for x in dia.itertuples():
        L.append((ano, uni, "tempo_diario_viajante", x.c, x.t, x.n))
    return L


def sistema(con, ano: int) -> pd.DataFrame:
    linhas = []
    for uni, filtro in UNIVERSOS.items():
        pes = con.execute(f"""select coalesce('q'||cast(quintil as varchar),'nd') q, sum(fe_pess) pop, count(*) n,
            sum(fe_pess) filter (where idade>=15) pop15,
            sum(fe_pess) filter (where idade>=15 and id_pess not in (select id_pess from viagem where ano={ano})) imob15,
            count(*) filter (where idade>=15) n15 from pessoa where ano={ano} and {filtro} group by 1""").df()
        via = con.execute(f"""select coalesce('q'||cast(quintil as varchar),'nd') q, sum(fe_via) v, count(*) n from viagem_h
            where ano={ano} and {filtro} group by 1""").df()
        m = pes.merge(via, on="q", suffixes=("", "_v"))
        for r in m.itertuples():
            linhas += [(ano, uni, "ind_mob", r.q, r.v / r.pop, r.n_v), (ano, uni, "imob_15m", r.q, r.imob15 / r.pop15, r.n15)]
        tot_p, tot_v = pes["pop"].sum(), via["v"].sum()
        linhas += [(ano, uni, "ind_mob", "todos", tot_v / tot_p, int(via.n.sum())), (ano, uni, "imob_15m", "todos", pes.imob15.sum() / pes.pop15.sum(), int(pes.n15.sum())),
                   (ano, uni, "populacao", "todos", tot_p, int(pes.n.sum())), (ano, uni, "viagens", "todos", tot_v, int(via.n.sum()))]
        modal = con.execute(f"""select modo_agreg m, sum(fe_via) v, count(*) n from viagem_h where ano={ano} and {filtro} and modo_agreg is not null group by 1""").df()
        nome = {1: "coletivo", 2: "individual", 3: "bicicleta", 4: "a_pe"}
        for r in modal.itertuples():
            linhas.append((ano, uni, "divisao_modal", nome[int(r.m)], r.v / modal.v.sum(), r.n))
        trab = con.execute(f"""select modo_agreg m, sum(fe_via*duracao)/sum(fe_via) t, count(*) n from viagem_h where ano={ano} and {filtro}
            and motivo_o=8 and motivo_d in (1,2,3) and duracao>0 group by 1""").df()
        for r in trab.itertuples():
            linhas.append((ano, uni, "tempo_trab", nome[int(r.m)], r.t, r.n))
        auto = con.execute(f"""select sum(f.qt_auto*f.fe_fam) a, count(*) n from od.familias f join domicilio d using(ano,id_dom) where f.ano={ano} and {filtro.replace('u_home_amc75','d.u_home_amc75')}""").df()
        linhas.append((ano, uni, "autos_100hab", "todos", 100 * float(auto.a[0]) / tot_p, int(auto.n[0])))
        linhas += extras(con, ano, uni, filtro)
    df = pd.DataFrame(linhas, columns=["ano", "universo", "medida", "categoria", "valor", "n"])
    df["precisao"] = ["ok" if n >= MIN_N_CELULA else "sem_estimativa" for n in df.n]
    return df


def rodar(anos=ANOS) -> None:
    con = conectar(); preparar(con)
    for a in anos:
        s = sistema(con, a)
        s.to_parquet(PROCESSED / str(a) / "sistema.parquet", index=False)
        print(a, "sistema", len(s), "| ind_mob todos:", round(s[(s.medida == "ind_mob") & (s.categoria == "todos") & (s.universo == "edicao")].valor.iloc[0], 3))


if __name__ == "__main__":
    rodar()
