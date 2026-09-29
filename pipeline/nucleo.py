"""F2 — indicadores, fluxos, perfis e fluxos_dim por edição e nível. Saída: data/processed/<ano>/*.parquet.

Todo agregado traz `n` (amostral) e, quando ponderado, `cv` e `precisao` (precisao_regras.py).
"""
import numpy as np
import pandas as pd

from pipeline import precisao_regras as R
from pipeline.base import GEO, NIVEIS, conectar, niveis_da_edicao, preparar
from pipeline.edicoes import ANOS, MIN_N_CELULA, MIN_N_DETALHE
from pipeline.fontes import PROCESSED

CV, PREC = R.sql_cv("w"), R.sql_precisao


def unidades_validas(ano: int, nivel: str) -> pd.DataFrame:
    u = pd.read_parquet(GEO / "unidades_ref_geo.parquet")
    u = u[(u.nivel == nivel) & (u.edicao == (ano if nivel == "zona" else 0))]
    return u[["codigo"]].assign(ok=1)


def _cv_prec(df: pd.DataFrame, cvcol="cv", ncol="n") -> pd.DataFrame:
    df["precisao"] = [R.precisao(int(n), None if pd.isna(c) else float(c)) for n, c in zip(df[ncol], df[cvcol])]
    return df


def indicadores(con, ano: int, nivel: str) -> pd.DataFrame:
    h, t, e = f"u_home_{nivel}", f"u_trab_{nivel}", f"u_esc_{nivel}"
    q = f"""
    with pop as (select {h} as codigo, sum(fe_pess) pop, sum(fe_pess) filter (where idade>=15) pop_15m,
                   count(*) n_pess, {CV.replace('w','fe_pess')} as cv_pop,
                   sum(fe_pess) filter (where cond_ativ=1) ocupados_res,
                   sum(fe_pess) filter (where cond_ativ=5) estudantes_res
                 from pessoa where ano={ano} and {h} is not null group by 1),
    dom as (select {h} as codigo, sum(fe_dom) dom from domicilio where ano={ano} and {h} is not null group by 1),
    fam as (select d.{h} as codigo, sum(f.fe_fam) familias, sum(f.qt_auto*f.fe_fam) autos,
                   sum(f.renda_fa_r2023*f.fe_fam)/nullif(sum(f.fe_fam) filter (where f.renda_fa_r2023 is not null),0) renda_fa_media_r2023,
                   sum(f.renda_fa_sm*f.fe_fam)/nullif(sum(f.fe_fam) filter (where f.renda_fa_sm is not null),0) renda_fa_media_sm
            from od.familias f join domicilio d using (ano,id_dom) where f.ano={ano} and d.{h} is not null group by 1),
    viag as (select {h} as codigo, sum(fe_via) viagens, count(*) n_viag, {CV.replace('w','fe_via')} as cv_viagens,
                 sum(fe_via) filter (where modo_agreg=1) viag_coletivo, sum(fe_via) filter (where modo_agreg=2) viag_individual,
                 sum(fe_via) filter (where modo_agreg=3) viag_bici, sum(fe_via) filter (where modo_agreg=4) viag_ape,
                 sum(fe_via) filter (where modo_agreg=4 and duracao<=15) viag_ape_ate15
             from viagem_h where ano={ano} and {h} is not null group by 1),
    mov as (select {h} as codigo, sum(fe_pess) filter (where idade>=15 and id_pess in (select id_pess from viagem where ano={ano})) mov15
            from pessoa where ano={ano} and {h} is not null group by 1),
    trab as (select {h} as codigo, sum(fe_via) v_trab, sum(fe_via*duracao)/nullif(sum(fe_via),0) tempo_med_trab,
                 sum(fe_via*duracao) filter (where modo_agreg=1)/nullif(sum(fe_via) filter (where modo_agreg=1),0) tempo_med_trab_coletivo,
                 sum(fe_via*duracao) filter (where modo_agreg=2)/nullif(sum(fe_via) filter (where modo_agreg=2),0) tempo_med_trab_individual,
                 sum(fe_via) filter (where modo_agreg=1)/nullif(sum(fe_via),0) pct_coletivo_trab,
                 sum(fe_via) filter (where duracao>60)/nullif(sum(fe_via),0) pct_trab_mais60min, count(*) n_trab
             from viagem_h where ano={ano} and motivo_d in (1,2,3) and motivo_o=8 and {h} is not null and duracao is not null group by 1),
    emp as (select {t} as codigo, sum(fe_pess) empregos_od from pessoa where ano={ano} and cond_ativ=1 and {t} is not null group by 1),
    mat as (select {e} as codigo, sum(fe_pess) matriculas_od from pessoa where ano={ano} and {e} is not null group by 1),
    atr as (select u_d_{nivel} as codigo, sum(fe_via) atracao from viagem where ano={ano} and motivo_d<>8 and u_d_{nivel} is not null group by 1)
    select pop.codigo, pop, pop_15m, dom, familias, 100.0*autos/nullif(pop,0) autos_100hab, renda_fa_media_r2023, renda_fa_media_sm,
           viagens, viag_coletivo, viag_individual, viag_bici, viag_ape, viagens/nullif(pop,0) ind_mob,
           (viag_coletivo+viag_individual)/nullif(pop,0) ind_mob_motor, 1 - mov15/nullif(pop_15m,0) imob_15m,
           ocupados_res, estudantes_res, empregos_od, matriculas_od, viagens producao, atracao,
           atracao/nullif(viagens,0) razao_ap, (atracao-viagens)/nullif(atracao+viagens,0) ief,
           empregos_od-ocupados_res saldo_pend, empregos_od/nullif(ocupados_res,0) jobs_housing,
           tempo_med_trab, tempo_med_trab_coletivo, tempo_med_trab_individual, pct_coletivo_trab,
           viag_ape_ate15/nullif(viagens,0) pct_ape_ate15, pct_trab_mais60min, n_pess, n_viag, n_trab, cv_viagens, cv_pop
    from pop left join dom using(codigo) left join fam using(codigo) left join viag using(codigo) left join mov using(codigo)
      left join trab using(codigo) left join emp using(codigo) left join mat using(codigo) left join atr using(codigo)"""
    df = con.execute(q).df()
    df = df.merge(unidades_validas(ano, nivel), on="codigo").drop(columns="ok")
    df["cv"] = df["cv_viagens"]
    df["n"] = df["n_viag"].fillna(0).astype(int)
    df = _cv_prec(df)
    # medidas de tempo/percentual só com n_trab >= piso de detalhe (P3)
    fraco = df.n_trab.fillna(0) < MIN_N_DETALHE
    for c in ("tempo_med_trab", "tempo_med_trab_coletivo", "tempo_med_trab_individual", "pct_coletivo_trab", "pct_trab_mais60min"):
        df.loc[fraco, c] = np.nan
    df.insert(0, "nivel", nivel)
    df.insert(0, "ano", ano)
    return df


def _tabela_fluxo(con, ano: int, nivel: str, tipo: str) -> str:
    o, d = f"u_home_{nivel}", f"u_d_{nivel}"
    if tipo == "casa_trab":
        return f"""select u_home_{nivel} o, u_trab_{nivel} d, fe_pess w, 0 as modo, cast(null as int) as dur
                   from pessoa where ano={ano} and cond_ativ=1 and u_home_{nivel} is not null and u_trab_{nivel} is not null"""
    filt = {"todas": "true", "trabalho": "motivo_d in (1,2,3)", "estudo": "motivo_d = 4"}[tipo]
    return f"""select u_o_{nivel} o, u_d_{nivel} d, fe_via w, modo_agreg as modo, duracao as dur
               from viagem where ano={ano} and {filt} and u_o_{nivel} is not null and u_d_{nivel} is not null"""


def fluxos(con, ano: int, nivel: str, tipo: str) -> pd.DataFrame:
    src = _tabela_fluxo(con, ano, nivel, tipo)
    q = f"""
    with t as ({src}),
    agg as (select o origem, d destino, sum(w) total, count(*) n, {CV} cv,
              sum(w) filter (where modo=1)/sum(w) pct_coletivo, sum(w) filter (where modo=2)/sum(w) pct_individual,
              sum(w) filter (where modo in (3,4))/sum(w) pct_ativo
            from t group by 1,2),
    med as (select origem, destino, min(dur) filter (where cum >= tot/2.0) dur_mediana from (
              select o origem, d destino, dur, sum(w) over (partition by o,d order by dur rows unbounded preceding) cum,
                     sum(w) over (partition by o,d) tot from t where dur is not null) group by 1,2)
    select * from agg left join med using (origem, destino)"""
    df = con.execute(q).df()
    rev = df[["origem", "destino", "total"]].rename(columns={"origem": "destino", "destino": "origem", "total": "total_rev"})
    df = df.merge(rev, on=["origem", "destino"], how="left")
    tr = df.total_rev.fillna(0)
    df["ief_par"] = np.where(df.total + tr > 0, (df.total - tr) / (df.total + tr), np.nan)
    df = df.drop(columns="total_rev")
    v = unidades_validas(ano, nivel)["codigo"]
    df = df[df.origem.isin(v) & df.destino.isin(v)]
    c = pd.read_parquet(GEO / "centroides.parquet")
    c = c[(c.nivel == nivel) & (c.edicao == (ano if nivel == "zona" else 0))].set_index("codigo")[["x", "y"]]
    xo, xd = c.reindex(df.origem), c.reindex(df.destino)
    df["dist_km"] = np.hypot(xo.x.values - xd.x.values, xo.y.values - xd.y.values) / 1000
    df["n"] = df["n"].astype(int)
    df = _cv_prec(df)
    piso = R.min_n_fluxo(nivel)
    publicado = df[df.n >= piso].copy()
    detalhe_fraco = publicado.n < MIN_N_DETALHE                                  # P3
    for c_ in ("dur_mediana", "pct_coletivo", "pct_individual", "pct_ativo"):
        publicado.loc[detalhe_fraco, c_] = np.nan
    cobertura = pd.DataFrame([dict(ano=ano, nivel=nivel, tipo=tipo, total_todos=df.total.sum(),
                                   total_publicado=publicado.total.sum(), pares_todos=len(df), pares_publicados=len(publicado))])
    publicado.insert(0, "tipo", tipo)
    publicado.insert(0, "nivel", nivel)
    publicado.insert(0, "ano", ano)
    return publicado, cobertura


def rodar(anos=ANOS, niveis=NIVEIS) -> None:
    con = conectar()
    preparar(con)
    for ano in anos:
        pasta = PROCESSED / str(ano)
        pasta.mkdir(parents=True, exist_ok=True)
        ind = pd.concat([indicadores(con, ano, n) for n in niveis_da_edicao(ano, niveis)], ignore_index=True)
        ind.to_parquet(pasta / "indicadores.parquet", index=False)
        cobs = []
        for n in niveis_da_edicao(ano, niveis):
            fl = []
            for tipo in ("todas", "trabalho", "estudo", "casa_trab"):
                f, cb = fluxos(con, ano, n, tipo)
                fl.append(f)
                cobs.append(cb)
            pd.concat(fl, ignore_index=True).to_parquet(pasta / f"fluxos_{n}.parquet", index=False)
        pd.concat(cobs, ignore_index=True).to_parquet(pasta / "cobertura_fluxos.parquet", index=False)
        print(ano, "ok", len(ind), "indicadores")


if __name__ == "__main__":
    rodar()
