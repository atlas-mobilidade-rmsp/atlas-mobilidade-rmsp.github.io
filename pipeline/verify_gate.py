#!/usr/bin/env python3
"""Verifica .gate_ok SEM acesso ao laboratório: o carimbo existe e o SHA-256 de cada arquivo bate. Roda no CI."""
import json
import sys

from pipeline.fontes import PROCESSED
from pipeline.gate_check import checar, sha_todos


def main() -> int:
    g = PROCESSED / ".gate_ok"
    if not g.exists():
        print("ERRO: data/processed/.gate_ok ausente — rode pipeline/gate_check.py")
        return 1
    esperado = json.loads(g.read_text())["sha256"]
    atual = sha_todos()
    dif = sorted(k for k in set(esperado) | set(atual) if esperado.get(k) != atual.get(k))
    if dif:
        print(f"ERRO: {len(dif)} arquivo(s) alterado(s)/adicionado(s)/removido(s) após o gate:", *dif[:10], sep="\n  ")
        return 1
    erros = checar()
    if erros:
        print("ERRO: checagens P1–P6 falharam:", *erros, sep="\n  ")
        return 1
    print("gate verificado:", len(atual), "arquivos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
