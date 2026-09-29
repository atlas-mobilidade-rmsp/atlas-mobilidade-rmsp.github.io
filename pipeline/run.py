"""Orquestra o pipeline completo: geo -> nucleo -> perfis -> pares_serie -> meta -> gate.

Uso: python -m pipeline.run [etapa ...]   (etapas: geo nucleo perfis serie meta gate; padrão: nucleo..gate)
Requer METROSP_ROOT (pipeline/fontes.py). `geo` também exige geo/fetch_geosampa.sh e geo/build.sh.
"""
import subprocess
import sys
import time

from pipeline import build_geo, build_meta, gate_check, nucleo, pares_serie, perfis
from pipeline.fontes import REPO_ROOT, verificar

ETAPAS = {
    "geo": lambda: (build_geo.main(), __import__("pipeline.build_sub_trilhos", fromlist=["main"]).main(),
                    subprocess.run(["sh", str(REPO_ROOT / "geo/build.sh")], check=True)),
    "nucleo": nucleo.rodar, "perfis": perfis.rodar, "serie": pares_serie.rodar, "meta": build_meta.main,
    "gate": lambda: sys.exit(gate_check.main()) if gate_check.main() else None,
}


def main(args: list[str]) -> None:
    verificar()
    for e in args or ["nucleo", "perfis", "serie", "meta", "gate"]:
        t = time.time()
        ETAPAS[e]()
        print(f"[{e}] {time.time() - t:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
