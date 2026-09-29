"""F6 — emprego formal (RAIS pública, MTE) por município de trabalho, divisão CNAE 2.0 e ano.

Fonte: microdados públicos de vínculos da RAIS, UF SP (FTP ftp.mtps.gov.br/pdet/microdados/RAIS/<ano>), em data/raw_rais
(gitignored). Anos: 2007, 2017, 2023. O arquivo extraído tem 5–9 GB, por isso lemos em blocos e o extraído é apagado ao fim.
Unidade: município de TRABALHO (Mun Trab), não de residência. Conta vínculos ativos em 31/12. Só municípios inteiros: o
microdado público não traz endereço do estabelecimento (o campo de distrito só existe para o município de SP e vem quase
sempre "9999"), então a RAIS não desce a zona/área de ponderação.
Saídas: data/interim/rais/rais_mun_cnae.parquet (estado: ano, mun6, divisao, vinculos, rem_soma, rem_n; intermediário) e
data/processed/rais/rais_muni.parquet (municípios do atlas: total, remuneração média em SM, parcela por grupo setorial e razão RAIS/OD).
"""
import re
import sys
import unicodedata

import pandas as pd
import py7zr

from pipeline.fontes import PROCESSED, REPO_ROOT

RAW = REPO_ROOT / "data" / "raw_rais"
TMP = RAW / "tmp"
ARQUIVOS = {2007: "SP2007.7z", 2017: "SP2017.7z", 2023: "RAIS_VINC_PUB_SP_2023.7z"}
INTERIM = REPO_ROOT / "data" / "interim" / "rais" / "rais_mun_cnae.parquet"   # estado inteiro; não é publicado
SAIDA = PROCESSED / "rais" / "rais_muni.parquet"                              # só municípios do atlas, cruzado com a OD
ENC = "latin1"


def _norm(c: str) -> str:
    c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", c).strip()


def _acha(cols: list[str], *padroes: str) -> str:
    """Primeira coluna cujo nome normalizado bate com o primeiro padrão que tiver correspondência."""
    for p in padroes:
        for c in cols:
            if re.fullmatch(p, _norm(c)):
                return c
    raise KeyError(f"coluna não encontrada: {padroes} em {cols}")


def agrega_arquivo(caminho, ano: int) -> pd.DataFrame:
    with open(caminho, encoding=ENC) as f:
        sep = ";" if ";" in f.readline() else ","          # 2007 e 2017 usam ';'; 2023 usa ',' com ponto decimal
    cols = pd.read_csv(caminho, sep=sep, encoding=ENC, nrows=0).columns.tolist()
    sfx = r"( codigo)?"
    nomes = {
        _acha(cols, r"mun trab" + sfx, r"municipio trab" + sfx): "mun_trab",
        _acha(cols, r"municipio" + sfx): "mun_estab",
        _acha(cols, r"(ind )?vinculo ativo 31 12" + sfx): "ativo",
        _acha(cols, r"cnae 2 0 classe" + sfx): "cnae",
        _acha(cols, r"vl rem(un)? media sm"): "rem_a",
        _acha(cols, r"vl rem(un)? media nom"): "rem_b",
    }
    partes = []
    for ch in pd.read_csv(caminho, sep=sep, encoding=ENC, usecols=list(nomes), dtype=str, chunksize=2_000_000):
        ch = ch.rename(columns=nomes)                  # usecols devolve na ordem do arquivo: renomear por nome, nunca por posição
        ch = ch[ch.ativo.str.strip() == "1"].copy()
        mt = ch.mun_trab.str.strip().str.zfill(6)
        me = ch.mun_estab.str.strip().str.zfill(6)
        valido = mt.str.fullmatch(r"\d{6}") & ~mt.isin(["999999", "000000"])   # "0000-1" (2007) e 999999 (2023) = não informado
        ch["mun6"] = mt.where(valido, me)             # município de trabalho quando informado; senão o do estabelecimento
        ch["divisao"] = ch.cnae.str.strip().str.zfill(5).str[:2]
        num = {k: pd.to_numeric(ch[k].str.strip().str.replace(",", ".", regex=False), errors="coerce") for k in ("rem_a", "rem_b")}
        # em 2023 há blocos de registros com "Nom" e "(SM)" trocados; o SM é sempre o menor dos dois (R$ nominal = SM x 380..1320)
        r = pd.concat(num, axis=1).where(lambda d: d > 0).min(axis=1)
        ch["rem"] = r.where(r > 0)                    # 0 = sem remuneração declarada (ignorado, não zero real)
        g = ch.groupby(["mun6", "divisao"]).agg(vinculos=("ativo", "size"), rem_soma=("rem", "sum"), rem_n=("rem", "count"))
        partes.append(g)
    d = pd.concat(partes).groupby(level=[0, 1]).sum().reset_index()
    d.insert(0, "ano", ano)
    return d


def main(anos: list[int] | None = None) -> None:
    anos = anos or list(ARQUIVOS)
    INTERIM.parent.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    partes = [pd.read_parquet(INTERIM)] if INTERIM.exists() else []
    partes = [p[~p.ano.isin(anos)] for p in partes]
    for ano in anos:
        with py7zr.SevenZipFile(RAW / ARQUIVOS[ano]) as z:
            nomes = z.getnames()
            z.extractall(TMP)
        arq = TMP / nomes[0]
        try:
            d = agrega_arquivo(arq, ano)
        finally:
            arq.unlink(missing_ok=True)
        print(ano, len(d), "linhas;", int(d.vinculos.sum()), "vínculos ativos", flush=True)
        partes.append(d)
    pd.concat(partes, ignore_index=True).to_parquet(INTERIM, index=False)
    rodar_muni()


# CNAE 2.0, divisões -> grupos setoriais (agro fica só no total)
GRUPOS = {"industria": [(5, 33), (35, 39)], "construcao": [(41, 43)], "comercio": [(45, 47)], "servicos": [(49, 82), (90, 99)],
          "adm_publica_edu_saude": [(84, 88)]}
ANOS_OD = (2007, 2017, 2023)


def _grupo(div: pd.Series) -> pd.Series:
    n = pd.to_numeric(div, errors="coerce")
    g = pd.Series(pd.NA, index=div.index, dtype="object")
    for nome, faixas in GRUPOS.items():
        for lo, hi in faixas:
            g[(n >= lo) & (n <= hi)] = nome
    return g


def rodar_muni() -> None:
    """Município do atlas (7 dígitos IBGE) x ano: vínculos, remuneração média (SM), parcela por grupo, razão RAIS/OD."""
    d = pd.read_parquet(INTERIM)
    ref = pd.read_parquet(PROCESSED / "censo" / "censo_por_unidade.parquet")
    ref = ref[ref.nivel == "muni"].drop_duplicates("codigo")[["codigo"]]
    ref["mun6"] = ref.codigo.str[:6]
    d = d.merge(ref, on="mun6", how="inner")
    d["grupo"] = _grupo(d.divisao)
    tot = d.groupby(["ano", "codigo"]).agg(vinculos=("vinculos", "sum"), rem_soma=("rem_soma", "sum"), rem_n=("rem_n", "sum"))
    tot["rem_media_sm"] = tot.rem_soma / tot.rem_n
    g = d.dropna(subset=["grupo"]).pivot_table(index=["ano", "codigo"], columns="grupo", values="vinculos", aggfunc="sum", fill_value=0)
    for c in GRUPOS:
        tot["pct_" + c] = (g[c] / tot.vinculos).reindex(tot.index) if c in g else float("nan")
    tot = tot.drop(columns=["rem_soma", "rem_n"]).reset_index()
    tot["ano"] = tot.ano.astype(int)
    od = [pd.read_parquet(PROCESSED / str(a) / "indicadores.parquet").query("nivel == 'muni'")[["codigo", "empregos_od"]].assign(ano=a) for a in ANOS_OD]
    tot = tot.merge(pd.concat(od), on=["ano", "codigo"], how="left")
    tot["razao_rais_od"] = tot.vinculos / tot.empregos_od
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    tot.to_parquet(SAIDA, index=False)
    print("rais_muni:", len(tot), "linhas;", tot.groupby("ano").codigo.nunique().to_dict(), "municípios por ano")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or None)
