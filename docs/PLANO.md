# Atlas da Mobilidade na RMSP — plano de implementação (v1)

## Contexto

O laboratório `metrosp` já produziu: a série OD harmonizada 1977–2023 (6 pesquisas, 975 mil viagens, `data/serie_historica/od_serie_1977_2023.duckdb`), o zoneamento compatibilizado (zonas de cada ano + AMC 146 [1987–2023] e AMC 75 [1977–2023], `data/processed/zonas_od.gpkg`, `zona_para_amc.csv`), a camada censitária 1970–2022 por zona (`data/censo/censo_setores_rmsp.duckdb`: `indicadores_por_zona`, `nucleo_por_zona`, setores completos) e a camada CNEFE 2022 classificada (`cnefe_por_zona`, 1,28 M pontos).

O objetivo agora é um **atlas web estático (GitHub Pages) orientado a perguntas**: responder às questões recorrentes da literatura de mobilidade urbana (desigualdade de mobilidade e de tempo de viagem por renda, divisão modal por classe, descompasso emprego-moradia e excesso de deslocamento, acessibilidade, exclusão social) e às emergentes (queda pós-pandemia e trabalho híbrido, aplicativos e motos, imobilidade oculta, mobilidade do cuidado e gênero, raça, proximidade/15 minutos, pobreza de tempo, envelhecimento). Modelo de referência: o próprio **Atlas da Migração Interna** do autor (`atlas-da-migracao/atlas-da-migracao.github.io`) — mesma arquitetura, mesmos tokens visuais, mesma disciplina de gate e de comparabilidade.

Decisões já tomadas com o usuário: (1) mesma arquitetura da referência; (2) fluxos em duas escalas (AMC/macro para a matriz completa; zona do ano só de/para a unidade selecionada, com piso amostral e selo de precisão); (3) aquisições da v1: RAIS pública, GTFS + acessibilidade, IPEA AOP, Censo 2022 por área de ponderação; (4) publicação em organização nova `atlas-mobilidade-rmsp`; (5) **nova funcionalidade**: selecionar um par O/D e acompanhar sua evolução em todas as pesquisas; (6) **orquestração automática entre modelos** (subagentes de modelo fixo), para custo-benefício.

Fatos empíricos que moldam o desenho (consultas já feitas, só leitura):
- Matriz zona×zona é esparsa: 2023 tem 33 k pares, mediana de 1 viagem amostral por par, 36 % do volume em pares com n<5. Na AMC-146: ~6 k pares, mediana 740 viagens expandidas, mas ~27 % do volume de trabalho em pares com n<10 → piso na AMC é n≥5 com selo, não n≥10.
- Índice de mobilidade por quintil de renda per capita: 1977 1,48 (q1) → 2,72 (q5); 2023 1,62 → 1,86 (compressão + queda pós-pandemia). Imobilidade (15+ sem viagem) 2023: 44,5 % q1 vs 33 % q5. Viagem ao trabalho: ~70 min por coletivo vs ~31 min individual desde 2007. Top-10 AMC concentram ~47 % dos locais de trabalho em todas as edições. App 3,1 % e moto 3,5 % das viagens em 2023; 2023 tem raça, trabalho híbrido/remoto (6,3 % dos ocupados) e pandemia; 2007+ têm coordenadas de origem/destino/domicílio/trabalho (100 % válidas).
- A referência usa deck.gl com `OrthographicView` cartesiano sobre TopoJSON já em metros (não MapLibre). Como tudo no metrosp está em EPSG:31983, o frame cartesiano é reutilizável sem reprojeção; MapLibre (ruas) fica opcional.

## Repositório novo: `atlas-mobilidade-rmsp/atlas-mobilidade-rmsp.github.io`

```
CLAUDE.md  README.md  CITATION.cff  LICENSE (MIT)  LICENSE-DADOS.md (CC BY 4.0)
.claude/agents/{metodologo,implementador,mecanico,auditor,revisor_dados}.md   # orquestração
.github/workflows/publicar.yml   scripts/pre-commit   .gitleaks.toml
pipeline/
  fontes.py            # METROSP_ROOT (env) -> caminhos do lab; o atlas LÊ, nunca copia microdado bruto
  edicoes.py           # 1977..2023: zoneamento, área (1977 parcial), recursos {coords, raca, hibrido, app, distancia}
  precisao_regras.py   # P1–P6 (análogo de disclosure_rules.py)
  sql/01_extract.sql 02_unidades.sql 03_indicadores.sql 04_fluxos.sql 05_perfis.sql 06_fluxos_dim.sql 07_empregos.sql 08_pares_serie.sql
  gravidade.py  excesso_pendular.py  bootstrap_cv.py  rais.py  censo_apond.py  acessibilidade/{gtfs.py,r5.py,aop.py}
  publish.py  gate_check.py  verify_gate.py  build_meta.py  build_serie.py  build_perguntas.py  build_paginas.py  run.py
  perguntas/*.yaml     # catálogo (1 arquivo por pergunta)
  tests/
geo/  build.sh (npx mapshaper)  validate_earcut.mjs  decode_topojson.mjs
data/processed/        # versionado, só via gate (.gate_ok)
  geo/  <ano>/  censo/  cnefe/  empregos/  acessibilidade/  serie/  perguntas.json  meta.json
web/  Vite + React 19 + TS; src/{map,components,db,lib,state,styles,conteudo}
docs/  METODOLOGIA.md  DECISOES.md  ANALISE.md  SEO.md  qa/
```

Todas as edições em `data/processed/<ano>/` desde o início (a referência lamenta a assimetria "2022 flat" em `docs/EDICOES.md`).

### Reuso da referência (via `gh api .../contents/<path>`)

| Copiar quase verbatim | Adaptar | Novo |
|---|---|---|
| `web/src/lib/{fluxos,arcos,espigas,escalas,contraste,format}.ts`, `styles/tokens.css`, base de `app.css`, `db/duckdb.ts`, `state/url.ts` (+ testes), componentes `Legenda`, `Busca`, `Filtro`, `EstadoDados`, `Termo`, `Tour`, `BarraPerfil`, `PiramideIdadeSexo`, `SeletorEdicoes`; `pipeline/{run,verify_gate,build_meta}.py`, infra de `build_paginas.py` (Jinja2, sitemap, JSON-LD), `publicar.yml`, pre-commit, gitleaks, `geo/validate_earcut.mjs` | `map/MapaAtlas.tsx` (sem capitais/satélite/perímetro RM; + camada de contexto, hover, indicadores), `state/store.ts`, `db/queries.ts`, `App.tsx` (modos), `PainelMunicipio→PainelUnidade`, `PainelFluxo`, `SerieCensos→SeriePesquisas`, `ResumoSerie`, `GraficosSistema`, `disclosure_rules.py→precisao_regras.py`, `edicoes.py/.ts`, `build_series.py→build_serie.py`, `geo/build.sh` | `perguntas/`, `PaginaPerguntas`, `CartaoPergunta`, `ControleFluxos` (limiar, top-N, tipo), `SerieDoPar`, `PainelAcessibilidade`, `PainelEmpregos`, `PainelGravitacional`, `PainelCenso`, `CapaRMSP`, `gravidade.py`, `excesso_pendular.py`, `bootstrap_cv.py`, `rais.py`, `aop.py`, `censo_apond.py`, `acessibilidade/` |

Descartar: módulo RM, genealogia, unidades agregadas, `capitais.ts`, satélite, `DiagramaAcordes` (opcional para matriz sub×sub).

## Níveis territoriais

`nivel ∈ {zona, amc, sub, muni}`: **zona** do ano (243–527); **amc** (146; 75 no modo 1977–2023); **sub** = 32 subprefeituras da capital + 38 municípios (AMC→subprefeitura por sobreposição dominante; se o encaixe ficar abaixo de 95 % de área, usar as 8 regiões do Metrô); **muni** (39). AMC ⊂ município, então `zona→amc→sub→muni` é hierarquia limpa a partir de 1987.

## Produtos de dados (`data/processed`)

Toda tabela traz `n` (amostral exato, microdado público) e, quando ponderada, `cv` e `precisao ∈ {boa, cautela, baixa, sem_estimativa}`.

- **geo/**: `zonas_<ano>.topojson` (+ `_utm`), `amc`, `sub`, `muni`; `centroides.parquet(nivel, codigo, lon, lat, x, y, x_merc, y_merc)` — centroide ponderado por domicílios do CNEFE; `contexto_trilhos.topojson` (metrô, trem, monotrilho) e limites municipais.
- **unidades_ref**: `nivel, codigo, nome, muni_ibge, nm_muni, sub, amc_8723, amc_7723, area_km2, na_area_1977`.
- **<ano>/indicadores** (nível × edição): `pop, pop_15m, dom, familias, autos_100hab, renda_fa_media_r2023, renda_fa_mediana_sm, viagens, viag_{coletivo,individual,bici,ape}, ind_mob, ind_mob_motor, imob_15m, ocupados_res, empregos_od (zona_trab1), estudantes_res, matriculas_od, producao, atracao, razao_ap, saldo_pend, ief, autocont, jobs_housing, tempo_med_trab{,_coletivo,_individual}, pct_coletivo_trab, pct_ape_ate15, pct_trab_mais60min, hansen_emp, hansen_pop, n_pess, n_viag, cv_viagens, precisao`; 2023 acrescenta `pct_hibrido, pct_remoto, pct_app, pct_moto, pct_pretos_pardos`.
- **<ano>/fluxos_<nivel>** (amc/sub/muni: matriz completa com n≥5; zona: só pares n≥10): `origem, destino, tipo ∈ {todas, trabalho, estudo, casa_trab}, total, n, cv, precisao, dur_mediana, pct_coletivo, pct_individual, pct_ativo, ief_par, dist_km`. `casa_trab` vem de `pessoas` (domicílio→trab1, `fe_pess`) — a matriz pendular clássica; `trabalho`/`estudo` vêm de `viagens` (motivo_d).
- **<ano>/fluxos_dim** (perfil do fluxo, formato longo, pares n≥30): `nivel, origem, destino, tipo, dimensao ∈ {sexo, idade, renda_q, escolaridade, modo, motivo, hora_saida, duracao_faixa, setor}, categoria, valor, n`.
- **<ano>/perfis** (população, longo): `nivel, codigo, papel ∈ {residente, trabalha_aqui, estuda_aqui}, dimensao, categoria, valor, n`.
- **censo/censo_por_unidade**: `nivel, codigo, ano_censo, <indicadores_por_zona>` (agrega `nucleo_por_zona` para sub/muni); **censo/apond_2022**: renda, cor/raça, escolaridade, tempo casa-trabalho por área de ponderação → unidade (interpolação por área, mesmo método do script 17).
- **cnefe/cnefe_por_unidade**: `nivel, codigo, grupo, subgrupo, motivo_od, n_enderecos, n_multiplo_*`.
- **empregos/empregos**: `nivel, codigo, ano, fonte ∈ {od_trab1, rais_vinc, rais_estab, cnefe}, setor_agreg, porte, valor, n`.
- **acessibilidade/acess_2023**: `nivel, codigo, modo ∈ {tp, ape, auto}, medida ∈ {cma30, cma45, cma60, tmi_saude, tmi_escola}, valor, hora_pico`; **aop_hex**: H3 do IPEA (SP e Guarulhos, 2017–19) + `hex→unidade` por área.
- **<ano>/gravitacional**: `codigo, hansen_emp_exp, hansen_emp_pow, hansen_pop_exp, jobs_housing, autocont, t_medio_obs, t_medio_min`; **gravitacional_params.json**: por edição × impedância × nível: `beta, mtl_obs, mtl_modelo, r2_log, t_min, t_obs, t_max, excesso, utilizacao_capacidade`.
- **serie/** (lê só `data/processed`, nunca microdados): `unidades_serie(nivel ∈ {amc75, amc146, muni}, codigo, edicao, <indicadores>)`; **`pares_serie(nivel, origem, destino, tipo, edicao, total, n, cv, precisao, dur_mediana, pct_coletivo, pct_individual, pct_ativo, ief_par, share_da_origem, share_do_destino)`** — a tabela da nova funcionalidade (par O/D ao longo de todas as pesquisas); `sistema_serie(edicao, viagens, ind_mob_q1..q5, imob_q1..q5, split modal, tempo_trab_por_modo, motorizacao, beta, excesso, gini_hansen)`; `comparabilidade.json`.
- **perguntas.json**: `[{id, slug, titulo, pergunta, tema ∈ {recorrente, emergente}, literatura[{autores, ano, titulo, doi}], indicadores[], vista{modo, edicao, nivel, metrica, tipo, filtro, unidade, origem, destino, topN}, achado{texto_template, valores{}}, comparabilidade[], dados[], status}]`.
- **meta.json**: `versao_dados, edicoes[], niveis[], rotulos{...}, precisao{min_n_celula:5, min_n_zona:10, min_n_detalhe:30, cv_boa:15, cv_cautela:30}, maior_fluxo{nivel→valor}, bounds_utm, fontes[], citacao`.

## Métodos

**Gravidade e potencial** (`gravidade.py`, numpy/scipy; AMC e sub; zona só 2007+): modelo duplamente restrito de Wilson `T_ij = A_i O_i B_j D_j f(c_ij)`, `f = exp(−βc)` (variante potência), O/D da matriz `casa_trab`; β calibrado por bissecção até `MTL_modelo = MTL_obs` (Hyman), com duas impedâncias — distância entre centroides (km) e tempo observado (mediana de `duracao` no par; pares n<10 imputados por regressão `tempo ~ dist × modo`). Diagnóstico: R² em log, erro por faixa de distância, β por edição. **Hansen**: `A_i = Σ_j E_j f(c_ij)` com β calibrado; empregos de `od_trab1` (2023 também RAIS e CNEFE, para comparar). **Excesso de deslocamento** (Hamilton 1982; White 1988; Horner 2002): `T_min`/`T_max` por problema de transporte (`scipy.optimize.linprog`), `excesso = (T_obs − T_min)/T_obs`, `utilização = (T_obs − T_min)/(T_max − T_min)`, com aviso de MAUP. **Estrutura**: `jobs_housing = empregos_od/ocupados_res`; `autocont = T_ii/O_i`; `ief = (A−P)/(A+P)`; `ief_par = (T_ij − T_ji)/(T_ij + T_ji)` (análogo do índice de eficácia migratória).

**Gate de precisão P1–P6** (confiabilidade, não sigilo — documentar a diferença): P1 célula só com n≥5 (abaixo, absorvida no residual `outros` da dimensão, preservando totais); P2 `fluxos_zona` só n≥10; AMC/sub/muni publicam n≥5 com `precisao` e o mapa não desenha `baixa` por padrão (toggle); P3 `fluxos_dim` e medianas/percentuais só com n≥30; P4 CV — v1 aproximado `cv = 100·sqrt(Σw²)/Σw·sqrt(deff)`, F2b bootstrap de domicílios (200 réplicas por `id_dom` dentro de zona) que calibra o `deff`; classes 15/30 (IBGE); P5 coerência hierárquica (soma das células + residual = total; zona→amc→sub→muni fecha); P6 comparabilidade (flags por edição: `na_area_1977`, `grau_ins_5` ausente em 1997, coordenadas só 2007+, raça/híbrido só 2023) → `comparabilidade.json` e selo na interface. `gate_check.py` grava `.gate_ok` (SHA-256); `verify_gate.py` roda no CI.

## Front-end (estado na URL: `ed, n, u, o, d, m, t, f, top, fmin, fluxos, baixa, modo, p, us, eds, ctx`)

1. **Mapa**: coroplético do indicador × fluxos (fita afunilada + seta, `lib/fluxos.ts`) da unidade selecionada ou top-N do sistema; `ControleFluxos` com slider de limiar mínimo (fração da faixa) + top-N + tipo (todas/trabalho/estudo/casa-trabalho) + filtro de perfil; troca de nível; camada de trilhos.
2. **Painel da unidade**: cabeçalho (pop, viagens, índice de mobilidade, imobilidade); abas *População* (pirâmide OD + censo 1970–2022 + CNEFE), *Empregos* (OD × RAIS × CNEFE por setor), *Acessibilidade* (CMA/TMI 2023, AOP), *Estrutura* (Hansen, jobs-housing, autocontenção, saldo, IEF, produção/atração), *Fluxos* (entradas/saídas com selo).
3. **Painel do fluxo**: total, n, CV, IEF do par, duração mediana; barras de modo, motivo, renda, sexo, idade, escolaridade; histograma de hora de saída; par recíproco.
4. **Série do par (nova funcionalidade)**: no painel do fluxo, seção "Ao longo das pesquisas" (`SerieDoPar`): o par selecionado em qualquer nível é resolvido para seu par de AMC-146 (1987–2023) e AMC-75 (1977–2023) via `zona_para_amc`; gráfico de linha com posições fixas 1977·1987·1997·2007·2017·2023 para `total`, `pct_coletivo`, `dur_mediana`, `ief_par` e `share_da_origem`, faixa de CV, marcadores de ausência (`não existia`, `fora da área de 1977`, `n insuficiente`) sem interpolar; botão "seguir este par" leva ao modo série com `o`/`d` fixos; seleção também direta no modo série (busca origem + busca destino). Pares recíprocos lado a lado.
5. **Perguntas**: grade por tema (recorrentes / emergentes); cada cartão → `irPara(vista)` com filtros e edição certos + texto de achado com números injetados de `perguntas.json` + notas de comparabilidade + literatura + link para a seção de `ANALISE.md`.
6. **Ao longo das pesquisas**: seletor de unidade (amc75/amc146/muni) e de edições; `sistema_serie` (mobilidade por quintil, split modal, tempos por modo, β, excesso, motorização) + série da unidade + série do par.
7. **Metodologia/Dados**: conteúdo TSX + download dos Parquet + citação.
8. **SEO** (`build_paginas.py`): `/zona/<ano>/<slug>/`, `/amc/<slug>/`, `/subprefeitura|municipio/<slug>/`, `/pergunta/<slug>/`, `/par/<amc_o>-<amc_d>/` para os maiores pares, `/achados/`, `/metodologia/`, `/dados/`.

## Catálogo inicial de perguntas (20–25 YAML)

Recorrentes: mobilidade × renda (índice de mobilidade por quintil, 1977–2023); tempo de deslocamento e desigualdade (Pereira & Schwanen 2013; coletivo vs individual); divisão modal por classe; emprego-moradia, excesso de deslocamento e autocontenção (top-10 AMC ≈ 47 %); acessibilidade e potencial gravitacional (Hansen, β; Boisjoly/Moreno-Monroy/El-Geneidy 2017; Giannotti/Bittencourt/Freiberg — CEM/Poli); exclusão social relacionada ao transporte e imobilidade (Lucas 2012; dimensão mobilidade do IBEU); motorização e posse de automóvel por renda; gênero (motivos, encadeamento, horários). Emergentes: queda pós-pandemia e trabalho híbrido/remoto (2023); aplicativos e motos; imobilidade oculta; mobilidade do cuidado (Sánchez de Madariaga) por sexo e faixa etária; raça (2023); proximidade/15 minutos (viagens a pé ≤15 min, CNEFE de destinos por zona); pobreza de tempo; envelhecimento; pico e espraiamento horário. Cada YAML: pergunta → indicadores → vista → literatura → comparabilidade → status (`respondida`, `parcial`, `aguarda dados`).

## Aquisições de dados (F6, paralelo)

- **RAIS pública** (PDET FTP, `RAIS_ESTAB`/`RAIS_VINC` 2006–2023): filtrar SP em streaming com DuckDB; município para a RMSP; distrito da capital via campo de distrito/bairro (disponível nos microdados públicos para o município de SP) → `empregos` por CNAE agregado e porte. RAIS identificada por CNPJ/CEP (Acordo de Cooperação Técnica com o MTE) fica fora da v1; preparar o pedido em `docs/termos/`.
- **GTFS + OSM → acessibilidade 2023**: SPTrans (cadastro de desenvolvedor), EMTU, Metrô/CPTM; r5py exige JDK 21 (não instalado). Publicar primeiro o **AOP/IPEA** (aopdata, H3, SP e Guarulhos 2017–19); a acessibilidade própria entra como F6b desacoplada. Alternativa sem Java: matriz de tempos declarados da própria OD + isócronas a pé por OSM.
- **Censo 2022 por área de ponderação**: renda, cor/raça, escolaridade, tempo de deslocamento casa-trabalho → `censo/apond_2022`.

## Orquestração automática entre modelos

Sessão principal em **Sonnet 5**; despacho por subagentes de modelo fixo em `.claude/agents/` (mesmo padrão da referência), com a regra "menor modelo que resolve":

| Agente | Modelo | Usa quando | Exemplos nesta v1 |
|---|---|---|---|
| `mecanico` | Haiku 4.5 | tarefa fechada, especificação completa, saída verificável por teste | converter os 20+ YAML de perguntas, gerar `rotulos` do `meta.json`, copiar/renomear componentes da referência, testes a partir de spec, formatação de docs, download e descompactação (RAIS, AOP, GTFS) |
| `implementador` | Sonnet 5 | código com desenho já definido | SQL do pipeline, TopoJSON/centroides, componentes React, `SerieDoPar`, `ControleFluxos`, `build_paginas`, CI |
| `revisor_dados` | Sonnet 5 | validação de saída contra totais/invariantes, sem decidir método | reconciliação de totais, checagem P1–P6, QA das páginas |
| `metodologo` | Opus 5.5 | decisão de método com trade-off | calibração do gravitacional e escolha da impedância, regras P1–P6 e `deff`, comparabilidade entre edições, redação de `METODOLOGIA.md`, encaixe AMC→subprefeitura, texto dos achados |
| `auditor` | Fable 5.1 | só em checkpoints de maior risco (≤ 4 na v1) | (a) auditoria da matriz `casa_trab` e da gravidade após F4, (b) crítica de UX/design do MVP após F3, (c) revisão final de `ANALISE.md` e do catálogo de perguntas, (d) release |

Regras: cada fase começa com um brief do `metodologo` só quando há decisão aberta; o `implementador` recebe caminhos e esquemas, nunca microdado; o `mecanico` só recebe tarefas com critério de aceitação automático; o `auditor` nunca implementa. Estimativa de mix de tokens: ~55 % Sonnet, ~30 % Haiku, ~12 % Opus, ~3 % Fable.

## Fases

| Fase | Entregas | Depende | Agentes | Esforço |
|---|---|---|---|---|
| **F0** Bootstrap | org+repo, skeleton web (tooling, `copy-duckdb`, `sync-data`), `fontes.py`, `edicoes.py`, `CLAUDE.md`, `DECISOES.md`, `.claude/agents/`, CI, pre-commit | — | mecanico, implementador | 1–2 d |
| **F1** Geo | TopoJSON WGS84+UTM por zoneamento, AMC, sub, muni; centroides ponderados; trilhos; earcut; `test_geo` | F0 | implementador, metodologo (sub) | 2 d |
| **F2** Pipeline núcleo | `01–08.sql`, `indicadores`, `fluxos_*`, `perfis`, `fluxos_dim`, `pares_serie`, P1–P6 com CV aproximado, `publish/gate/verify`, `meta.json`, testes de reconciliação | F1 | metodologo (gate), implementador, revisor_dados | 5–7 d |
| **F2b** CV bootstrap | `bootstrap_cv.py`, `deff` por edição | F2 | metodologo, implementador | 2 d |
| **F3** Web MVP | shell, DuckDB worker, mapa cartesiano, fluxos + controles, painéis unidade/fluxo, `SerieDoPar`, legenda, URL, vitest | F2 | implementador, mecanico; auditor (UX) | 6–8 d |
| **F4** Estrutura e série | `gravidade.py`, `excesso_pendular.py`, censo/CNEFE por unidade, `build_serie.py`, modo "Ao longo das pesquisas", painéis Estrutura/População | F2 | metodologo, implementador; auditor (gravidade) | 5 d |
| **F5** Perguntas + análise | YAML das perguntas, `build_perguntas.py`, vista Perguntas, `docs/ANALISE.md`, Achados, `METODOLOGIA.md` | F3, F4 | metodologo (texto), mecanico (YAML), implementador | 4–5 d |
| **F6** Aquisições | RAIS pública, Censo 2022 áreas de ponderação, AOP/IPEA; F6b GTFS+OSM→acessibilidade | F2 (paralelo a F3) | mecanico (download), implementador, metodologo (acess.) | 5–8 d |
| **F7** Publicação | `build_paginas.py`, Lighthouse/axe, orçamento de bundle, Zenodo/CITATION, release v1.0.0 | F5, F6 | implementador, revisor_dados; auditor (release) | 3 d |
| **F8** Opcional | H3 (res 8/9) a partir das coordenadas 2007–2023; modo MapLibre (ruas) | F7 | implementador | 4 d |

## `docs/ANALISE.md` e seção Achados

1. Por que um atlas orientado a perguntas. 2. Dados e método (OD 1977–2023, AMC, censo/CNEFE/RAIS/AOP, gate, gravidade/excesso). 3. Achados, um por pergunta, no formato *pergunta → indicadores → vista (link) → achado → literatura → comparabilidade*: 3.1 mobilidade × renda; 3.2 tempo de deslocamento e desigualdade; 3.3 divisão modal por classe, motos e aplicativos; 3.4 emprego-moradia, autocontenção e excesso de deslocamento na série; 3.5 acessibilidade e potencial (Hansen, β, AOP); 3.6 exclusão social e imobilidade oculta; 3.7 pós-pandemia e trabalho híbrido/remoto; 3.8 gênero e mobilidade do cuidado; 3.9 raça (2023); 3.10 proximidade/15 minutos; 3.11 envelhecimento e pobreza de tempo; 3.12 pares O/D que mais mudaram em 46 anos. 4. Comparabilidade e limitações. 5. Agenda (H3, GTFS histórico, RAIS identificada, OD 2027).

## Verificação

- **pytest (pipeline)**: totais expandidos por edição = oficiais (pop, viagens, domicílios; tolerância 0,1 %); Σ `fluxos_<nivel>` = viagens com ambas as pontas na área; `T_ij` vs `T_ji` (corr > 0,9 em `casa_trab`; `ief_par ∈ [−1,1]`); gate: nenhuma célula n<5, `fluxos_zona` toda n≥10, residual fecha o total, hierarquia fecha; `pares_serie` coerente com `fluxos_amc` de cada edição; gravidade: `mtl_modelo` a ±1 % de `mtl_obs`, `t_min ≤ t_obs ≤ t_max`, `0 ≤ excesso ≤ 1`; acessibilidade monotônica (`cma30 ≤ cma45 ≤ cma60`); geo 1:1 com `unidades_ref`; `perguntas.json` validado por JSON Schema e toda `vista` resolve para estado válido; páginas estáticas sem caminho local.
- **vitest**: codec de URL (ida e volta, inclusive `o`/`d` no modo série), `fluxos.test.ts`, escalas/contraste, `lib/perguntas.ts`, `edicoes.ts` (recursos por edição bloqueiam filtros inexistentes, ex.: raça fora de 2023), resolução par zona→par AMC.
- **Lighthouse ≥ 90** (perf/a11y/SEO) em `vite preview`; **axe** sem críticos; orçamento: JS inicial ≤ 600 kB gz (wasm à parte), carga inicial ≤ 1,5 MB (AMC + indicadores 2023).
- **QA manual** no browser integrado por vista: trocar de edição preserva unidade e par; slider não altera o painel; selo `baixa` visível; série do par mostra ausências sem interpolar; deep-link de cada pergunta; modo escuro; navegação por teclado.

## Riscos

- GTFS/r5: sem Java; SPTrans exige cadastro; feeds EMTU/Metrô/CPTM instáveis → acessibilidade desacoplada (F6b), AOP primeiro.
- RAIS por distrito depende do campo de distrito nos microdados públicos (só capital); arquivos de GB por ano → streaming DuckDB, só SP.
- CV sem desenho amostral é aproximação → declarar e calibrar com bootstrap (F2b).
- Encaixe AMC→subprefeitura imperfeito → medir; fallback regiões do Metrô.
- Esparsidade zona×zona: ~46 % do volume de 2023 fica fora dos pares publicáveis com n≥10 → a interface sempre mostra "cobertura publicada" do total da zona; a série do par usa AMC.
- 1977 cobre só a área central (75 AMC) → selo "fora da área de 1977" em toda série.
