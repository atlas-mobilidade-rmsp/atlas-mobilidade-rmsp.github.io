"""Edições da Pesquisa Origem e Destino (Metrô-SP) e recursos disponíveis em cada uma."""
from dataclasses import dataclass, field

# Piso amostral / precisão (ver docs/DECISOES.md, P1–P6)
MIN_N_CELULA, MIN_N_ZONA, MIN_N_DETALHE = 5, 10, 30
CV_BOA, CV_CAUTELA = 15, 30


@dataclass(frozen=True)
class Edicao:
    ano: int
    n_zonas: int
    area_parcial: bool = False          # 1977: só ~41 % da área da RMSP (~95 % da população)
    amc146: bool = True                 # AMC 1987–2023
    amc75: bool = True                  # AMC 1977–2023
    recursos: frozenset = field(default_factory=frozenset)


_COORD = {"coords"}
EDICOES: dict[int, Edicao] = {
    1977: Edicao(1977, 0, area_parcial=True, amc146=False),
    1987: Edicao(1987, 0, amc75=True),
    1997: Edicao(1997, 0, recursos=frozenset({"sem_grau_ins_5"})),
    2007: Edicao(2007, 0, recursos=frozenset(_COORD)),
    2017: Edicao(2017, 0, recursos=frozenset(_COORD)),
    2023: Edicao(2023, 0, recursos=frozenset(_COORD | {"raca", "hibrido", "app", "pandemia"})),
}
ANOS = tuple(EDICOES)  # n_zonas preenchido por build_meta a partir de zonas_od.gpkg (243–527)


def tem(ano: int, recurso: str) -> bool:
    return recurso in EDICOES[ano].recursos
