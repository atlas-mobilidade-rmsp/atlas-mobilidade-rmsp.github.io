"""F5 — catálogo de perguntas: valida pipeline/perguntas/*.yaml (JSON Schema), calcula os valores citados no
achado a partir de data/processed (nunca microdado), renderiza o texto e grava data/processed/perguntas.json.

Um valor é um objeto {fonte, ..., fmt}: 
  fonte=sistema  {medida, categoria, ed, univ}          -> serie/sistema_serie.parquet
  fonte=ind      {nivel, codigo, ed, campo}              -> <ed>/indicadores.parquet
  fonte=grav     {nivel, codigo, ed, campo}              -> <ed>/gravitacional.parquet
  fonte=topshare {nivel, ed, campo, n}                   -> parcela das n maiores unidades no total do campo
  fonte=params   {nivel, ed, imped, caminho}             -> serie/gravitacional_params.json
  fonte=censo    {ano_censo, campo, nivel}              -> média ponderada por população de censo_por_unidade (nivel muni)
  fonte=aop_decil {modo, medida, decil}                  -> acessibilidade/acess_decil_2019.parquet
  fonte=aop_unidade {nivel, codigo, modo, medida}        -> acessibilidade/acess_2019.parquet
  fonte=rais     {ano, campo, codigo?}                   -> rais/rais_muni.parquet (sem codigo: soma dos municípios do atlas)
  fonte=expr     {op: ratio|diff|pct_change|mult, a, b}  -> combina outros valores do mesmo achado
fmt: int | dec1 | dec2 | pct0 | pct1 (valor em fração -> %) | pp1 (pontos percentuais)
"""
import json
import sys
from functools import lru_cache

import jsonschema
import pandas as pd
import yaml

from pipeline.fontes import PROCESSED, REPO_ROOT

DIR = REPO_ROOT / "pipeline" / "perguntas"
SCHEMA = json.loads((REPO_ROOT / "pipeline" / "perguntas_schema.json").read_text())


@lru_cache(None)
def _sis() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "serie" / "sistema_serie.parquet")


@lru_cache(None)
def _tab(ed: int, nome: str) -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / str(ed) / f"{nome}.parquet")


@lru_cache(None)
def _params() -> dict:
    return json.loads((PROCESSED / "serie" / "gravitacional_params.json").read_text())["edicoes"]


def _get(d: dict, caminho):
    for k in (caminho if isinstance(caminho, list) else caminho.split(".")):
        d = d[k]
    return d


def calcula(v: dict, ja: dict) -> float:
    f = v["fonte"]
    if f == "sistema":
        s = _sis()
        r = s[(s.medida == v["medida"]) & (s.categoria == v["categoria"]) & (s.edicao == v["ed"]) & (s.universo == v.get("univ", "edicao"))]
        if len(r) != 1:
            raise KeyError(f"sistema: {len(r)} linhas para {v}")
        return float(r.valor.iloc[0])
    if f in ("ind", "grav"):
        t = _tab(v["ed"], "indicadores" if f == "ind" else "gravitacional")
        r = t[(t.nivel == v["nivel"]) & (t.codigo == str(v["codigo"]))]
        if len(r) != 1:
            raise KeyError(f"{f}: {len(r)} linhas para {v}")
        return float(r[v["campo"]].iloc[0])
    if f == "topshare":
        t = _tab(v["ed"], "indicadores"); t = t[t.nivel == v["nivel"]][v["campo"]].dropna().sort_values(ascending=False)
        return float(t.head(v["n"]).sum() / t.sum())
    if f == "params":
        return float(_get(_params()[str(v["ed"])][v["nivel"]][v["imped"]], v["caminho"]))
    if f == "aop_decil":
        d = pd.read_parquet(PROCESSED / "acessibilidade" / "acess_decil_2019.parquet")
        r = d[(d.modo == v["modo"]) & (d.medida == v["medida"]) & (d.decil == v["decil"])]
        if len(r) != 1:
            raise KeyError(f"aop_decil: {len(r)} linhas para {v}")
        return float(r.valor.iloc[0])
    if f == "aop_unidade":
        d = pd.read_parquet(PROCESSED / "acessibilidade" / "acess_2019.parquet")
        r = d[(d.nivel == v["nivel"]) & (d.codigo == str(v["codigo"])) & (d.modo == v["modo"]) & (d.medida == v["medida"])]
        if len(r) != 1:
            raise KeyError(f"aop_unidade: {len(r)} linhas para {v}")
        return float(r.valor.iloc[0])
    if f == "rais":
        d = pd.read_parquet(PROCESSED / "rais" / "rais_muni.parquet")
        d = d[d.ano == v["ano"]]
        if "codigo" in v:
            r = d[d.codigo == str(v["codigo"])]
            if len(r) != 1:
                raise KeyError(f"rais: {len(r)} linhas para {v}")
            return float(r[v["campo"]].iloc[0])
        return float(d[v["campo"]].sum())
    if f == "censo":
        c = pd.read_parquet(PROCESSED / "censo" / "censo_por_unidade.parquet")
        c = c[(c.nivel == v.get("nivel", "muni")) & (c.ano_censo == v["ano_censo"])].dropna(subset=[v["campo"]])
        return float((c[v["campo"]] * c.pop_total).sum() / c.pop_total.sum())
    if f == "expr":
        a, b = ja(v["a"]), ja(v["b"])
        return {"ratio": a / b, "diff": a - b, "pct_change": (a / b - 1), "mult": a * b}[v["op"]]
    raise ValueError(f"fonte desconhecida: {f}")


def formata(x: float, fmt: str) -> str:
    def br(s): return s.replace(",", "X").replace(".", ",").replace("X", ".")
    return br({"int": f"{x:,.0f}", "dec1": f"{x:,.1f}", "dec2": f"{x:,.2f}", "pct0": f"{100 * x:,.0f}%", "pct1": f"{100 * x:,.1f}%",
               "pp1": f"{100 * x:,.1f}", "abs_pct0": f"{100 * abs(x):,.0f}%", "mi1": f"{x / 1e6:,.1f}"}[fmt])


def renderiza(p: dict) -> dict:
    defs, memo, txt = p["achado"]["valores"], {}, {}

    def ja(nome):          # resolve sob demanda (expr pode citar valores definidos depois)
        if nome not in memo:
            memo[nome] = calcula(defs[nome], ja)
        return memo[nome]
    for nome, v in defs.items():
        txt[nome] = formata(ja(nome), v.get("fmt", "dec2"))
    ja_ = memo
    texto = p["achado"]["texto"].format(**txt)
    return {**p, "achado": {"texto": texto, "texto_template": p["achado"]["texto"], "valores": {k: {**v, "valor": ja_[k]} for k, v in p["achado"]["valores"].items()}}}


def main() -> int:
    saida, erros = [], []
    for f in sorted(DIR.glob("*.yaml")):
        p = yaml.safe_load(f.read_text())
        try:
            jsonschema.validate(p, SCHEMA)
            saida.append(renderiza(p) if p["status"] != "aguarda_dados" or p["achado"]["valores"] else p)
        except Exception as e:
            erros.append(f"{f.name}: {type(e).__name__}: {str(e)[:200]}")
    if erros:
        print("ERROS:\n  " + "\n  ".join(erros)); return 1
    saida.sort(key=lambda x: x["id"])
    ids = [p["id"] for p in saida]
    assert len(ids) == len(set(ids)), "ids duplicados"
    (PROCESSED / "perguntas.json").write_text(json.dumps(saida, indent=1, ensure_ascii=False))
    print(f"perguntas.json: {len(saida)} perguntas", {s: sum(p['status'] == s for p in saida) for s in ('respondida', 'parcial', 'aguarda_dados')})
    return 0


if __name__ == "__main__":
    sys.exit(main())
