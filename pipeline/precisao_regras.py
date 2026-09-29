"""Regras de precisão P1–P6 (confiabilidade estatística, não sigilo).

Análogo do disclosure_rules.py da referência, mas o microdado da OD é público: o piso amostral serve
para não publicar estimativas instáveis, e `n` exato pode ser divulgado. Fonte única dos limiares.

P1  célula (categoria) só com n >= MIN_N_CELULA; abaixo, absorvida no residual `outros` (totais preservados).
P2  fluxos de zona só com n >= MIN_N_ZONA; AMC/sub/muni publicam n >= MIN_N_CELULA com selo `precisao`.
P3  fluxos_dim, medianas e percentuais de fluxo só com n >= MIN_N_DETALHE.
P4  cv = 100*sqrt(sum w^2)/sum w * sqrt(deff); classes CV_BOA / CV_CAUTELA (IBGE). v1: deff = DEFF_V1 (=1).
P5  coerência hierárquica: soma das células + residual = total; zona -> amc -> muni fecha.
P6  comparabilidade: flags por edição (edicoes.py) -> comparabilidade.json.
"""
from pipeline.edicoes import CV_BOA, CV_CAUTELA, MIN_N_CELULA, MIN_N_DETALHE, MIN_N_ZONA

DEFF_V1 = 1.0
NIVEIS = ("zona", "amc146", "amc75", "sub", "muni")
PRECISOES = ("boa", "cautela", "baixa", "sem_estimativa")

# colunas que nunca podem aparecer (identificam domicílio/pessoa)
COLUNAS_PROIBIDAS = {"id_dom", "id_fam", "id_pess", "id_viag"}


def min_n_fluxo(nivel: str) -> int:
    return MIN_N_ZONA if nivel == "zona" else MIN_N_CELULA


def sql_cv(w: str = "fe", deff: float = DEFF_V1) -> str:
    """CV aproximado (%) de um total ponderado; agregar com GROUP BY."""
    return f"100.0 * sqrt(sum({w} * {w})) / nullif(sum({w}), 0) * sqrt({deff})"


def sql_precisao(n: str = "n", cv: str = "cv") -> str:
    return (f"CASE WHEN {n} < {MIN_N_CELULA} OR {cv} IS NULL THEN 'sem_estimativa' "
            f"WHEN {cv} <= {CV_BOA} THEN 'boa' WHEN {cv} <= {CV_CAUTELA} THEN 'cautela' ELSE 'baixa' END")


def precisao(n: int, cv: float | None) -> str:
    if n < MIN_N_CELULA or cv is None:
        return "sem_estimativa"
    return "boa" if cv <= CV_BOA else "cautela" if cv <= CV_CAUTELA else "baixa"
