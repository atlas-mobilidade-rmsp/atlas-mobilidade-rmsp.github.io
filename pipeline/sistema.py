"""F4 — indicadores de sistema por edição (RMSP inteira), em dois universos: `edicao` (área pesquisada) e
`area1977` (só residentes na área comparável de 1977, AMC-75). Saída: <ano>/sistema.parquet (formato longo)."""
import pandas as pd

from pipeline.base import conectar, preparar
from pipeline.edicoes import ANOS, MIN_N_CELULA
from pipeline.fontes import PROCESSED

UNIVERSOS = {"edicao": "true", "area1977": "u_home_amc75 is not null"}


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
