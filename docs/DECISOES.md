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
9. **F2 — núcleo.** `pipeline/{base,nucleo,perfis,pares_serie,gate_check,verify_gate}.py`. Unidades por ponta em todos os
   níveis (`base.py`); domicílios/famílias vêm das próprias tabelas (em 1977, 5,6 % do peso de domicílios não tem
   moradores listados). AMC-75 fica fora da igualdade de totais entre níveis (cobre só a área de 1977, ~98 % da pop.
   em 2023). CV v1 = aproximação por pesos com deff = 1 (F2b calibra). `sub` só 1997+; `amc146` só 1987+.
   Quintil de renda: renda familiar per capita r2023, ponderado por pessoa, por edição; sem renda → `nd`.
   Limitações abertas: `pct_hibrido/remoto/app/moto` e raça (2023) e distância/coordenadas ficam para depois
   (variáveis fora da série harmonizada); mediana ponderada de renda idem; `hansen_*`, `autocont` e gravidade são F4.
10. **F3 — web MVP.** Front-end novo e enxuto (React 19 + deck.gl `OrthographicView` + DuckDB-WASM sobre os Parquet
    publicados); reaproveitados da referência apenas `lib/fluxos.ts`, `arcos.ts`, `contraste.ts`, `format.ts` e
    `tokens.css`. Estado na URL (`ed, n, m, t, u, o, d, top, fmin, baixa, modo, tri`). `SerieDoPar` resolve zona→AMC via
    `unidades_ref_geo`; `sub` não tem série. Casa–trabalho não tem modo/duração (vem de `pessoas`). Nomes de AMC =
    "AMC n · zona dominante (município)". Bundle: 375 kB gz de JS (orçamento 600 kB).
