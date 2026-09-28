"""Caminhos do laboratório `metrosp`. O atlas LÊ de lá; nunca copia microdado bruto para este repo."""
import os
from pathlib import Path

METROSP_ROOT = Path(os.environ.get(
    "METROSP_ROOT", Path(__file__).resolve().parents[2] / "metrosp")).resolve()

SERIE_DB = METROSP_ROOT / "data/serie_historica/od_serie_1977_2023.duckdb"
ZONAS_GPKG = METROSP_ROOT / "data/processed/zonas_od.gpkg"
ZONA_PARA_AMC = METROSP_ROOT / "data/processed/zona_para_amc.csv"
CENSO_DB = METROSP_ROOT / "data/censo/censo_setores_rmsp.duckdb"
REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = REPO_ROOT / "data/processed"


def verificar() -> None:
    faltam = [p for p in (SERIE_DB, ZONAS_GPKG, ZONA_PARA_AMC, CENSO_DB) if not p.exists()]
    if faltam:
        raise FileNotFoundError(
            "Defina METROSP_ROOT para o laboratório metrosp. Ausentes:\n" + "\n".join(map(str, faltam)))


if __name__ == "__main__":
    verificar()
    print("ok:", METROSP_ROOT)
