"""F2 — perfis da população por unidade e perfil do fluxo (formato longo), com P1 (residual `outros`) e P3."""
import pandas as pd

from pipeline import precisao_regras as R
from pipeline.base import NIVEIS, conectar, niveis_da_edicao, preparar
from pipeline.edicoes import ANOS, MIN_N_CELULA, MIN_N_DETALHE
from pipeline.fontes import PROCESSED
from pipeline.nucleo import unidades_validas

ID = "case when idade<15 then '00-14' when idade<30 then '15-29' when idade<45 then '30-44' when idade<60 then '45-59' else '60+' end"
DIM_PESSOA = {
    "sexo": "case sexo when 1 then 'masculino' when 2 then 'feminino' end",
    "idade": ID,
    "renda_q": "coalesce('q'||cast(quintil as varchar), 'nd')",
    "escolaridade": "case grau_ins_4 when 1 then 'fund_incompleto' when 2 then 'fund_completo' when 3 then 'medio' when 4 then 'superior' end",
    "setor": "case setor_ativ when 1 then 'agricola' when 2 then 'construcao' when 3 then 'industria' when 4 then 'comercio' when 5 then 'servicos' end",
}
DIM_VIAGEM = {
    **{k: DIM_PESSOA[k] for k in ("sexo", "idade", "renda_q", "escolaridade")},
    "modo": "case modo_agreg when 1 then 'coletivo' when 2 then 'individual' when 3 then 'bicicleta' when 4 then 'a_pe' end",
    "motivo": "case when motivo_d in (1,2,3) then 'trabalho' when motivo_d=4 then 'educacao' when motivo_d=5 then 'compras' "
              "when motivo_d=6 then 'saude' when motivo_d=7 then 'lazer' when motivo_d=8 then 'residencia' else 'outros' end",
    "hora_saida": "case when h_saida<6 then '00-05' when h_saida<9 then '06-08' when h_saida<16 then '09-15' when h_saida<20 then '16-19' else '20-23' end",
    "duracao_faixa": "case when duracao<=15 then '0-15' when duracao<=30 then '16-30' when duracao<=60 then '31-60' when duracao<=90 then '61-90' else '90+' end",
}


def absorve_residual(df: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    """P1: categorias com n < MIN_N_CELULA viram `outros` (soma de valor e n), preservando o total da dimensão."""
    fraco = df.n < MIN_N_CELULA
    df = df.copy()
    df.loc[fraco, "categoria"] = "outros"
    return df.groupby(chaves + ["categoria"], as_index=False).agg(valor=("valor", "sum"), n=("n", "sum"))


def perfis(con, ano: int, nivel: str) -> pd.DataFrame:
    saida = []
    for papel, col, filt in (("residente", f"u_home_{nivel}", "true"), ("trabalha_aqui", f"u_trab_{nivel}", "cond_ativ=1"),
                             ("estuda_aqui", f"u_esc_{nivel}", "true")):
        for dim, expr in DIM_PESSOA.items():
            if dim == "setor" and papel != "trabalha_aqui":
                continue
            q = f"""select {col} as codigo, {expr} as categoria, sum(fe_pess) valor, count(*) n from pessoa
                    where ano={ano} and {col} is not null and {filt} group by 1,2"""
            d = con.execute(q).df().dropna(subset=["categoria"])
            d["papel"], d["dimensao"] = papel, dim
            saida.append(d)
    df = pd.concat(saida, ignore_index=True)
    df = df.merge(unidades_validas(ano, nivel), on="codigo").drop(columns="ok")
    fr = []
    for (papel, dim, cod), g in df.groupby(["papel", "dimensao", "codigo"]):
        r = absorve_residual(g.assign(papel=papel, dimensao=dim, codigo=cod), ["papel", "dimensao", "codigo"])
        fr.append(r)
    out = pd.concat(fr, ignore_index=True)
    out.insert(0, "nivel", nivel)
    out.insert(0, "ano", ano)
    return out


def fluxos_dim(con, ano: int, nivel: str) -> pd.DataFrame:
    """Perfil do fluxo para pares com n >= MIN_N_DETALHE (P3), tipos todas/trabalho/estudo (viagens) e casa_trab (pessoas)."""
    fl = pd.read_parquet(PROCESSED / str(ano) / f"fluxos_{nivel}.parquet")
    saida = []
    for tipo in ("todas", "trabalho", "estudo", "casa_trab"):
        pares = fl[(fl.tipo == tipo) & (fl.n >= MIN_N_DETALHE)][["origem", "destino"]]
        if pares.empty:
            continue
        con.register("pares_", pares)
        if tipo == "casa_trab":
            base = (f"select u_home_{nivel} o, u_trab_{nivel} d, fe_pess w, * from pessoa where ano={ano} and cond_ativ=1", DIM_PESSOA)
        else:
            filt = {"todas": "true", "trabalho": "motivo_d in (1,2,3)", "estudo": "motivo_d = 4"}[tipo]
            base = (f"select u_o_{nivel} o, u_d_{nivel} d, fe_via w, * from viagem_h where ano={ano} and {filt}", DIM_VIAGEM)
        for dim, expr in base[1].items():
            if dim == "setor" and tipo not in ("trabalho", "casa_trab"):
                continue
            q = f"""select b.o origem, b.d destino, {expr} categoria, sum(b.w) valor, count(*) n
                    from ({base[0]}) b join pares_ p on p.origem=b.o and p.destino=b.d group by 1,2,3"""
            d = con.execute(q).df().dropna(subset=["categoria"])
            d["tipo"], d["dimensao"] = tipo, dim
            saida.append(d)
    if not saida:
        return pd.DataFrame()
    df = pd.concat(saida, ignore_index=True)
    # P3: atributo ausente (ex.: renda/escolaridade não informadas) pode deixar o perfil com n < piso de detalhe
    df = df[df.groupby(["tipo", "dimensao", "origem", "destino"]).n.transform("sum") >= MIN_N_DETALHE]
    fr = []
    for (tipo, dim, o, dst), g in df.groupby(["tipo", "dimensao", "origem", "destino"]):
        fr.append(absorve_residual(g.assign(tipo=tipo, dimensao=dim, origem=o, destino=dst), ["tipo", "dimensao", "origem", "destino"]))
    out = pd.concat(fr, ignore_index=True)
    out.insert(0, "nivel", nivel)
    out.insert(0, "ano", ano)
    return out


def rodar(anos=ANOS, niveis=NIVEIS) -> None:
    con = conectar()
    preparar(con)
    for ano in anos:
        pasta = PROCESSED / str(ano)
        ns = niveis_da_edicao(ano, niveis)
        pd.concat([perfis(con, ano, n) for n in ns], ignore_index=True).to_parquet(pasta / "perfis.parquet", index=False)
        fd = pd.concat([fluxos_dim(con, ano, n) for n in ns if n != "zona"], ignore_index=True)
        fd.to_parquet(pasta / "fluxos_dim.parquet", index=False)
        print(ano, "perfis/fluxos_dim ok", len(fd))


if __name__ == "__main__":
    rodar()
