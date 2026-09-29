# Decisões

1. Arquitetura idêntica ao Atlas da Migração (deck.gl cartesiano; MapLibre opcional em F8).
2. Fluxos em duas escalas: AMC/sub/muni matriz completa (n≥5, selo); zona só n≥10.
3. Aquisições v1: RAIS pública, GTFS + acessibilidade (AOP primeiro), IPEA AOP, Censo 2022 por área de ponderação.
4. Publicação em `atlas-mobilidade-rmsp/atlas-mobilidade-rmsp.github.io` (org a criar pelo autor).
5. Série do par O/D ao longo de todas as pesquisas (`pares_serie`).
6. Orquestração entre modelos (ver `CLAUDE.md`).
7. **Nível `sub` (F1).** Fonte: GeoSampa (32 subprefeituras) + 38 municípios. Encaixe por sobreposição dominante: zonas
   1997–2023 ≥ 98,6 % da área; AMC-146 só 65 % (62 AMC da capital, 15 abaixo de 90 %) e zonas 1977/1987 ≤ 83 %. O
   critério do plano (≥ 95 %) reprova a AMC → `sub` existe só para 1997+ (via `zona_para_sub.parquet`) e **fica fora da
   série histórica**, que segue em AMC-146/AMC-75/muni. As "8 regiões do Metrô" não foram adotadas (sem fonte local).
8. **Trilhos.** GeoSampa `linha_metro`/`linha_trem` + estações (inclui CPTM na RMSP; monotrilho não vem como camada
   própria; linhas em obra/projetadas ficam em `situacao`). Contexto visual, não entra em indicadores.
