#!/usr/bin/env python3
"""Gate de precisão P1–P6 sobre data/processed. Grava .gate_ok (SHA-256 de cada arquivo publicável) se tudo passar.

Uso: python pipeline/gate_check.py   (na máquina com o laboratório não é preciso: só lê data/processed)
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

from pipeline import precisao_regras as R
from pipeline.edicoes import ANOS, MIN_N_CELULA, MIN_N_DETALHE, MIN_N_ZONA
from pipeline.fontes import PROCESSED

IGNORAR = {".gate_ok"}


def arquivos(raiz: Path = PROCESSED):
    return sorted(p for p in raiz.rglob("*") if p.is_file() and p.name not in IGNORAR
                  and "_tmp" not in p.parts and not p.name.startswith(".DS_Store"))


def sha_todos(raiz: Path = PROCESSED) -> dict:
    return {str(p.relative_to(raiz)): hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos(raiz)}


def checar(raiz: Path = PROCESSED) -> list[str]:
    erros = []
    if any(p.suffix.lower() == ".csv" for p in arquivos(raiz)):
        erros.append("estrutura: há .csv em data/processed")
    for a in ANOS:
        d = raiz / str(a)
        for f in d.glob("*.parquet"):
            cols = set(pd.read_parquet(f).columns)
            if cols & R.COLUNAS_PROIBIDAS:
                erros.append(f"P0 {a}/{f.name}: colunas proibidas {cols & R.COLUNAS_PROIBIDAS}")
        for f in d.glob("fluxos_*.parquet"):
            df = pd.read_parquet(f)
            nivel = f.stem.split("_", 1)[1]
            if nivel == "dim":
                # P1: categorias != outros com n >= piso; P3: dimensão só em pares com n >= 30
                bad = df[(df.categoria != "outros") & (df.n < MIN_N_CELULA)]
                if len(bad):
                    erros.append(f"P1 {a}/{f.name}: {len(bad)} células n<{MIN_N_CELULA}")
                soma = df.groupby(["nivel", "tipo", "dimensao", "origem", "destino"]).n.sum()
                if (soma < MIN_N_DETALHE).any():
                    erros.append(f"P3 {a}/{f.name}: {(soma < MIN_N_DETALHE).sum()} perfis com n<{MIN_N_DETALHE}")
                continue
            piso = R.min_n_fluxo(nivel)
            if (df.n < piso).any():
                erros.append(f"P2 {a}/{f.name}: {(df.n < piso).sum()} pares com n<{piso}")
            if df.ief_par.dropna().abs().gt(1 + 1e-9).any():
                erros.append(f"{a}/{f.name}: ief_par fora de [-1,1]")
            det = df[df.n < MIN_N_DETALHE]
            for c in ("dur_mediana", "pct_coletivo", "pct_individual", "pct_ativo"):
                if det[c].notna().any():
                    erros.append(f"P3 {a}/{f.name}: {c} publicado com n<{MIN_N_DETALHE}")
            esperado = [R.precisao(int(n), None if pd.isna(c) else float(c)) for n, c in zip(df.n, df.cv)]
            if list(df.precisao) != esperado:
                erros.append(f"P4 {a}/{f.name}: classe de precisão inconsistente com cv")
        pf = d / "perfis.parquet"
        if pf.exists():
            p = pd.read_parquet(pf)
            if len(p[(p.categoria != "outros") & (p.n < MIN_N_CELULA)]):
                erros.append(f"P1 {a}/perfis.parquet: células n<{MIN_N_CELULA}")
        # P5: população soma igual em todos os níveis da edição (tolerância 0,5 %)
        ind = pd.read_parquet(d / "indicadores.parquet")
        tot = ind.groupby("nivel")["pop"].sum()
        cheio = tot.drop("amc75")           # AMC-75 cobre só a área de 1977
        if (cheio.max() - cheio.min()) / cheio.max() > 0.005:
            erros.append(f"P5 {a}: população difere entre níveis {tot.round(0).to_dict()}")
        # P5: perfis de sexo somam à população do nível (residual preserva o total)
        if pf.exists():
            ps = p[(p.papel == "residente") & (p.dimensao == "sexo")].groupby("nivel").valor.sum()
            for nv, v in ps.items():
                if abs(v - tot[nv]) / tot[nv] > 0.005:
                    erros.append(f"P5 {a}: perfil sexo/residente {nv} não fecha com a população")
    if not (raiz / "comparabilidade.json").exists() or not (raiz / "meta.json").exists():
        erros.append("P6: comparabilidade.json/meta.json ausentes (rode build_meta.py)")
    return erros


def main() -> int:
    erros = checar()
    if erros:
        print("GATE REPROVADO:\n  " + "\n  ".join(erros))
        return 1
    (PROCESSED / ".gate_ok").write_text(json.dumps({"versao": 1, "sha256": sha_todos()}, indent=1, sort_keys=True))
    print("gate aprovado:", len(sha_todos()), "arquivos carimbados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
