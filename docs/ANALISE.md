# Análise: perguntas e achados

Gerado por `python -m pipeline.build_analise` a partir de `data/processed/perguntas.json`; os números vêm dos dados publicados. Formato de cada seção: pergunta → indicadores → vista (link de exemplo, relativo ao site) → achado → literatura → comparabilidade.

## 1. Por que um atlas orientado a perguntas

Cada vista do atlas responde a uma pergunta recorrente da literatura de mobilidade urbana ou a um tema emergente, em vez de expor a matriz de dados crua.

## 2. Dados e método

Pesquisa Origem e Destino do Metrô-SP (1977, 1987, 1997, 2007, 2017, 2023) harmonizada; Áreas Mínimas Comparáveis (146 desde 1987, 75 desde 1977); censos 1970–2022 e CNEFE 2022 por unidade; gate de precisão P1–P6; modelo gravitacional duplamente restrito, potencial de Hansen e excesso de deslocamento. Detalhes em `docs/METODOLOGIA.md` e `docs/DECISOES.md`.

## 3. Achados

### 3.1 Quem se desloca mais? Mobilidade e renda

**Pergunta.** Quanto a mobilidade diária depende da renda, e isso mudou desde 1977?

**Status.** respondida · tema recorrente

**Indicadores.** ind_mob por quintil

**Vista.** `?modo=pesquisas`

**Achado.** Em 1977 o quintil mais rico fazia 2,69 viagens por habitante ao dia, contra 1,48 do mais pobre (razão de 1,82). Em 2023 são 1,83 e 1,61 (razão de 1,13): a distância entre os extremos encolheu porque o topo perdeu cerca de 32% da mobilidade, e o quintil mais pobre ganhou 9%.

**Literatura.**
- Vasconcellos, E. A. (2001). *Transporte urbano, espaço e equidade: análise das políticas públicas*. Annablume
- Pereira, R. H. M.; Schwanen, T. (2013). *Tempo de deslocamento casa-trabalho no Brasil (1992-2009): diferenças entre regiões metropolitanas, níveis de renda e sexo*. IPEA, Texto para Discussão 1813

**Comparabilidade.**
- Renda: renda familiar per capita deflacionada (INPC); quintis por edição. 1977 tem 6,8% sem declaração (grupo 'nd').
- 1977 cobre só a área central pesquisada (~95% da população); use o universo 'área comparável de 1977' para séries estritas.

### 3.2 Quanto tempo leva o caminho ao trabalho?

**Pergunta.** O tempo de deslocamento casa–trabalho depende do modo e da renda? Mudou ao longo da série?

**Status.** respondida · tema recorrente

**Indicadores.** tempo_trab por modo, tempo_diario_viajante por quintil

**Vista.** `?modo=pesquisas`

**Achado.** Em 2023 a viagem casa→trabalho por transporte coletivo dura em média 71 minutos, contra 32 minutos no transporte individual motorizado (2,2 vezes mais). Em 1977 eram 56 e 26 minutos. Entre quem viaja, o quintil mais pobre passa 70 minutos por dia em deslocamento, contra 84 do quarto quintil.

**Literatura.**
- Pereira, R. H. M.; Schwanen, T. (2013). *Tempo de deslocamento casa-trabalho no Brasil (1992-2009): diferenças entre regiões metropolitanas, níveis de renda e sexo*. IPEA, Texto para Discussão 1813
- Vasconcellos, E. A. (2001). *Transporte urbano, espaço e equidade: análise das políticas públicas*. Annablume

**Comparabilidade.**
- Renda: renda familiar per capita deflacionada (INPC); quintis por edição. 1977 tem 6,8% sem declaração (grupo 'nd').
- 1977 cobre só a área central pesquisada (~95% da população); use o universo 'área comparável de 1977' para séries estritas.
- Duração informada pelo entrevistado (arredondamentos).

### 3.3 Divisão modal por classe de renda

**Pergunta.** Como a escolha do modo varia com a renda, e o que mudou?

**Status.** respondida · tema recorrente

**Indicadores.** coletivo_q, individual_q, ape_q

**Vista.** `?modo=pesquisas`

**Achado.** Em 2023, 35% das viagens do quintil mais pobre são feitas por transporte coletivo, contra 24% no quintil mais rico; o transporte individual motorizado responde por 15% e 60% das viagens desses grupos. Em 1977 o coletivo respondia por 45% no quintil mais pobre.

**Literatura.**
- Vasconcellos, E. A. (2001). *Transporte urbano, espaço e equidade: análise das políticas públicas*. Annablume

**Comparabilidade.**
- Renda: renda familiar per capita deflacionada (INPC); quintis por edição. 1977 tem 6,8% sem declaração (grupo 'nd').
- 1977 cobre só a área central pesquisada (~95% da população); use o universo 'área comparável de 1977' para séries estritas.

### 3.4 Emprego–moradia e excesso de deslocamento

**Pergunta.** As pessoas moram longe demais dos empregos? O deslocamento casa–trabalho é maior que o mínimo possível?

**Status.** parcial · tema recorrente

**Indicadores.** excesso de deslocamento, MTL, autocontenção

**Vista.** `?modo=pesquisas`

**Achado.** Entre os ocupados com local fixo de trabalho, o deslocamento casa–trabalho médio (entre centroides de AMC) é de 10,0 km em 2023 e seria de 6,1 km se moradia e emprego fossem realocados para minimizá-lo: um excesso de 38%, pouco acima do de 2007 (36%). A hipótese de distância intra-unidade muda esse número entre 35% e 41%. Na série comparável com 1977–1997 (que inclui trabalho em casa) o excesso é de 34% em 1977 e 35% em 2023: sem tendência clara.

**Literatura.**
- Hamilton, B. W. (1982). *Wasteful commuting*. Journal of Political Economy 90(5), 1035-1053
- White, M. J. (1988). *Urban commuting journeys are not 'wasteful'*. Journal of Political Economy 96(5), 1097-1110
- Horner, M. W. (2002). *Extensions to the concept of excess commuting*. Environment and Planning A 34(3), 543-566
- Wilson, A. G. (1967). *A statistical theory of spatial distribution models*. Transportation Research 1(3), 253-269

**Comparabilidade.**
- Excesso depende da agregação (MAUP): publicamos só AMC, com faixa de sensibilidade à distância intra-unidade (fator 0,5–1,0).
- Trabalho em casa e sem endereço fixo só é identificável de 2007 em diante; 1977–1997 os incluem como deslocamento intra-zonal (ruptura de tratamento).
- Município e subprefeitura são dominados pela capital como unidade única e não têm excesso publicado.

**Pendências.**
- Recalcular com tempo observado por modo (regressão dist × modo).

### 3.5 Onde estão os empregos?

**Pergunta.** Quão concentrados estão os empregos na metrópole?

**Status.** respondida · tema recorrente

**Indicadores.** empregos_od, jobs_housing

**Vista.** `?modo=mapa&ed=2023&n=amc146&m=jobs_housing`

**Achado.** As dez AMC com mais empregos concentravam 49% dos empregos com local fixo em 1987 e 47% em 2023 — a concentração central praticamente não se dispersou em 36 anos.

**Literatura.**
- Hansen, W. G. (1959). *How accessibility shapes land use*. Journal of the American Institute of Planners 25(2), 73-76

**Comparabilidade.**
- Empregos = ocupados com local fixo de trabalho na RMSP, pela zona do 1º trabalho (não inclui trabalho em casa/sem local fixo).

### 3.6 Desigualdade de acesso a empregos

**Pergunta.** Quão desigual é o acesso a empregos entre as áreas da metrópole (potencial de Hansen)?

**Status.** parcial · tema recorrente

**Indicadores.** hansen_emp, gini_hansen_emp

**Vista.** `?modo=mapa&ed=2023&n=amc75`

**Achado.** O Gini do potencial de empregos entre as AMC (ponderado pela população) caiu de 0,42 em 1977 para 0,37 em 1997 — mesmo tratamento dos dados — e chegou a 0,34 em 2023. A partir de 2007 o β é calibrado sem quem trabalha em casa ou sem local fixo, o que reduz a comparabilidade com o período anterior; a queda até 1997 é a leitura mais segura.

**Literatura.**
- Hansen, W. G. (1959). *How accessibility shapes land use*. Journal of the American Institute of Planners 25(2), 73-76
- Boisjoly, G.; Moreno-Monroy, A. I.; El-Geneidy, A. (2017). *Informality and accessibility to jobs by public transit: Evidence from the São Paulo Metropolitan Region*. Journal of Transport Geography 64, 89-96. doi:10.1016/j.jtrangeo.2017.08.011

**Comparabilidade.**
- Acessibilidade aqui é por distância (centroides), não por tempo de transporte público real.
- β difere por edição; Gini de potenciais com β distintos deve ser lido como ordem de grandeza.
- Trabalho em casa e sem endereço fixo só é identificável de 2007 em diante; 1977–1997 os incluem como deslocamento intra-zonal (ruptura de tratamento).

**Pendências.**
- Acessibilidade por tempo de transporte público (GTFS/AOP-IPEA) — F6.

### 3.7 Imobilidade e exclusão

**Pergunta.** Quem não se desloca? A imobilidade diária é mais frequente entre os mais pobres?

**Status.** respondida · tema recorrente

**Indicadores.** imob_15m por quintil

**Vista.** `?modo=pesquisas`

**Achado.** Em 2023, 46% das pessoas de 15 anos ou mais do quintil mais pobre não fizeram nenhuma viagem no dia, contra 34% no quintil mais rico. Em 1977 os números eram 43% e 28%.

**Literatura.**
- Lucas, K. (2012). *Transport and social exclusion: Where are we now?*. Transport Policy 20, 105-113. doi:10.1016/j.tranpol.2012.01.013

**Comparabilidade.**
- Renda: renda familiar per capita deflacionada (INPC); quintis por edição. 1977 tem 6,8% sem declaração (grupo 'nd').
- 1977 cobre só a área central pesquisada (~95% da população); use o universo 'área comparável de 1977' para séries estritas.
- A OD registra um dia útil; imobilidade de um dia não é imobilidade estrutural.

### 3.8 Motorização

**Pergunta.** Quanto a motorização cresceu e como isso se relaciona à mobilidade?

**Status.** respondida · tema recorrente

**Indicadores.** autos_100hab

**Vista.** `?modo=mapa&ed=2023&n=amc146&m=autos_100hab`

**Achado.** A frota das famílias passou de 13,5 para 23,6 automóveis por 100 habitantes entre 1977 e 2023, e o transporte individual motorizado é o modo de 60% das viagens do quintil mais rico.

**Literatura.**
- Vasconcellos, E. A. (2001). *Transporte urbano, espaço e equidade: análise das políticas públicas*. Annablume

**Comparabilidade.**
- 1977 cobre só a área central pesquisada (~95% da população); use o universo 'área comparável de 1977' para séries estritas.

### 3.9 Gênero e mobilidade

**Pergunta.** Homens e mulheres se deslocam de modo diferente? A diferença mudou?

**Status.** respondida · tema recorrente

**Indicadores.** ind_mob_sexo, trabalho_sexo

**Vista.** `?modo=pesquisas`

**Achado.** Em 1977 as mulheres faziam 1,67 viagens por habitante contra 2,50 dos homens (razão de 0,67); em 2023 são 1,61 e 1,76 (razão de 0,91). A diferença encolheu sobretudo porque a mobilidade masculina caiu.

**Literatura.**
- Sánchez de Madariaga, I. (2013). *The mobility of care: a new concept in urban transportation*. in Fair Shared Cities, Ashgate

**Comparabilidade.**
- 1977 cobre só a área central pesquisada (~95% da população); use o universo 'área comparável de 1977' para séries estritas.
- População inteira (inclui crianças).

### 3.10 Horários de pico

**Pergunta.** O pico da manhã está se intensificando?

**Status.** respondida · tema recorrente

**Indicadores.** pico_manha, pico_tarde

**Vista.** `?modo=pesquisas`

**Achado.** A parcela das viagens que começam entre 6h e 8h59 passou de 21% em 1977 para 27% em 2023, enquanto a do pico da tarde (16h–19h59) ficou em torno de 29%: o pico da manhã ficou mais concentrado.

**Comparabilidade.**
- 1977 cobre só a área central pesquisada (~95% da população); use o universo 'área comparável de 1977' para séries estritas.
- Hora de saída informada pelo entrevistado.

### 3.11 A queda de 2023

**Pergunta.** Quanto a mobilidade caiu depois da pandemia?

**Status.** respondida · tema emergente

**Indicadores.** viagens, ind_mob

**Vista.** `?modo=pesquisas`

**Achado.** As viagens diárias da região foram de 42,0 milhões em 2017 para 35,7 milhões em 2023 (variação de -15%) e o índice de mobilidade caiu de 2,02 para 1,68 viagens por habitante.

**Comparabilidade.**
- O campo de 2023 foi feito no pós-pandemia; a queda é real nos dados, não efeito da harmonização.

### 3.12 Aplicativos e motos

**Pergunta.** Táxi/aplicativo e motocicleta ganharam espaço?

**Status.** respondida · tema emergente

**Indicadores.** pct_taxi_app, pct_moto

**Vista.** `?modo=pesquisas`

**Achado.** Táxi e aplicativo passaram de 1,1% das viagens em 2017 para 3,1% em 2023; a moto, de 2,5% para 3,5%. Ainda são parcelas pequenas, mas a de táxi/aplicativo quase triplicou.

**Comparabilidade.**
- Táxi e aplicativo compartilham o mesmo código de modo (não distinguíveis); a moto inclui mototáxi.
- Em 1977 'táxi' existia como modo próprio e não é comparável a aplicativo.

### 3.13 Trabalho híbrido, em casa e sem local fixo

**Pergunta.** Quantos trabalham em casa, de forma híbrida ou sem local fixo?

**Status.** respondida · tema emergente

**Indicadores.** trab_domicilio, sem_local_fixo, trab_hibrido

**Vista.** `?modo=mapa&ed=2023&n=amc146&m=jobs_housing`

**Achado.** Em 2023, 14% dos ocupados trabalham no próprio domicílio (eram 10% em 2007), 10% não têm endereço fixo e 6,0% declaram frequência presencial de trabalho híbrido.

**Comparabilidade.**
- Trabalho em casa e sem endereço fixo só é identificável de 2007 em diante; 1977–1997 os incluem como deslocamento intra-zonal (ruptura de tratamento).
- Híbrido: quem declara frequência de trabalho presencial (dias por semana/mês); só 2023.

### 3.14 Imobilidade oculta: quem fica em casa?

**Pergunta.** A imobilidade diária difere por sexo e idade?

**Status.** respondida · tema emergente

**Indicadores.** imob_sexo, imob_idade

**Vista.** `?modo=pesquisas`

**Achado.** Em 2023, 43% das mulheres e 35% dos homens de 15 anos ou mais não se deslocaram no dia, contra 48% e 21% em 1977 — a lacuna de gênero encolheu de 27,1 para 7,8 pontos percentuais porque a imobilidade masculina subiu e a feminina caiu. Entre idosos (60+) a imobilidade é de 61%.

**Literatura.**
- Lucas, K. (2012). *Transport and social exclusion: Where are we now?*. Transport Policy 20, 105-113. doi:10.1016/j.tranpol.2012.01.013

**Comparabilidade.**
- 1977 cobre só a área central pesquisada (~95% da população); use o universo 'área comparável de 1977' para séries estritas.
- Um dia útil de pesquisa.

### 3.15 Mobilidade do cuidado

**Pergunta.** As mulheres concentram as viagens de cuidado (compras e saúde)?

**Status.** parcial · tema emergente

**Indicadores.** cuidado_sexo

**Vista.** `?modo=pesquisas`

**Achado.** Em 2023, 5,5% das viagens das mulheres têm como destino compras ou saúde, contra 3,5% das viagens dos homens (1,6 vezes mais). Em 1977 a razão era de 2,8.

**Literatura.**
- Sánchez de Madariaga, I. (2013). *The mobility of care: a new concept in urban transportation*. in Fair Shared Cities, Ashgate

**Comparabilidade.**
- Proxy: compras + saúde no destino. Acompanhar dependentes (escola, levar filhos) não é identificável de forma harmonizada.

**Pendências.**
- Encadeamento de viagens (tripchaining) e acompanhamento de dependentes.

### 3.16 Cidade de 15 minutos

**Pergunta.** Quanto da vida cotidiana se resolve a pé e perto de casa?

**Status.** parcial · tema emergente

**Indicadores.** pct_ape_ate15, cnefe

**Vista.** `?modo=mapa&ed=2023&n=muni&m=pct_ape_ate15`

**Achado.** Em 2023, 28% das viagens da região são a pé; em São Paulo, 22% das viagens são a pé e duram até 15 minutos, contra 25% em Guarulhos.

**Literatura.**
- Moreno, C.; Allam, Z.; Chabaud, D.; Gall, C.; Pratlong, F. (2021). *Introducing the '15-Minute City': Sustainability, resilience and place identity in future post-pandemic cities*. Smart Cities 4(1), 93-111. doi:10.3390/smartcities4010006

**Comparabilidade.**
- A pé até 15 min mede o comportamento observado, não a oferta de serviços a 15 minutos.

**Pendências.**
- Oferta de destinos essenciais a 15 min (CNEFE) por unidade — cruzar com a caminhada.

### 3.17 Pobreza de tempo

**Pergunta.** O tempo diário gasto em deslocamentos difere entre classes?

**Status.** parcial · tema emergente

**Indicadores.** tempo_diario_viajante

**Vista.** `?modo=pesquisas`

**Achado.** Entre quem viaja, o quintil mais pobre gasta 70 minutos por dia em deslocamentos e o quarto quintil, 84 (2023), e o quintil mais rico, 77 — o tempo diário de deslocamento não cresce de forma monótona com a renda.

**Literatura.**
- Vickery, C. (1977). *The time-poor: a new look at poverty*. Journal of Human Resources 12(1), 27-48
- Pereira, R. H. M.; Schwanen, T. (2013). *Tempo de deslocamento casa-trabalho no Brasil (1992-2009): diferenças entre regiões metropolitanas, níveis de renda e sexo*. IPEA, Texto para Discussão 1813

**Comparabilidade.**
- Só tempo de deslocamento de quem viaja; pobreza de tempo plena exige jornada de trabalho e cuidado (não disponíveis).

**Pendências.**
- Tempo de trabalho e de cuidado não pago (fora da OD).

### 3.18 Envelhecimento

**Pergunta.** Como o envelhecimento aparece na mobilidade?

**Status.** respondida · tema emergente

**Indicadores.** ind_mob_idade, imob_idade, censo pct_60m

**Vista.** `?modo=pesquisas`

**Achado.** A proporção de idosos (60+) na região passou de 5,7% em 1970 para 16,3% em 2022 (Censo). Em 2023, os idosos fazem 1,04 viagens por habitante ao dia, contra 1,79 de quem tem 15–59 anos, e 61% deles não se deslocam no dia.

**Comparabilidade.**
- Censo Demográfico 1970–2022 interpolado por área (camada censitária do laboratório): 1970/1980 só em resolução municipal.

### 3.19 Raça/cor e mobilidade (2023)

**Pergunta.** Pessoas pretas e pardas se deslocam de modo diferente das brancas?

**Status.** respondida · tema emergente

**Indicadores.** ind_mob_raca, tempo_trab_raca, coletivo_raca

**Vista.** `?modo=pesquisas`

**Achado.** Em 2023 pretos e pardos fazem praticamente o mesmo número de viagens por habitante que brancos (1,67 contra 1,68), mas usam mais o transporte coletivo (38% contra 31% das viagens) e levam 6 minutos a mais nas viagens ao trabalho (48 contra 42 min). O quintil médio de renda per capita é 2,8 contra 3,7.

**Comparabilidade.**
- Raça/cor só existe em 2023 (autodeclarada); grupos amarela, indígena e sem declaração ficam fora da comparação (<3% da amostra).

### 3.20 Acessibilidade por transporte público

**Pergunta.** Quantos empregos se alcançam em 60 min de transporte público, e isso depende da renda de quem mora onde?

**Status.** parcial · tema recorrente

**Indicadores.** cma30, cma60, cma90, tmi_saude, tmi_escola

**Vista.** `?modo=mapa&ed=2023&n=muni&m=jobs_housing`

**Achado.** Em São Paulo (2019), os moradores das áreas do décimo de renda mais pobre alcançam em média 167.612 empregos em 60 minutos de transporte público, contra 1.640.337 nas áreas do décimo mais rico (9,8 vezes mais). De carro, o município como um todo alcança 2.604.955 empregos no mesmo tempo, contra 678.626 de transporte público.

**Literatura.**
- Boisjoly, G.; Moreno-Monroy, A. I.; El-Geneidy, A. (2017). *Informality and accessibility to jobs by public transit: Evidence from the São Paulo Metropolitan Region*. Journal of Transport Geography 64, 89-96. doi:10.1016/j.jtrangeo.2017.08.011

**Comparabilidade.**
- AOP/IPEA cobre só São Paulo (transporte público, carro, a pé) e Guarulhos (carro, a pé); sem transporte público em Guarulhos e nos demais municípios.
- Acessibilidade de 2019 (pico da manhã) e população/renda de 2010 (do próprio AOP): vintages diferentes da OD.
- Média ponderada pela população dos hexágonos H3 (res. 9) cujo centroide cai na unidade; só unidades com ≥ 90% de cobertura.

**Pendências.**
- GTFS próprio da RMSP (SPTrans/EMTU/Metrô/CPTM) para cobrir os demais municípios e 2023 — F6b.

### 3.21 Empregos formais e oferta de trabalho

**Pergunta.** Onde estão os empregos formais (RAIS) frente aos declarados na OD?

**Status.** aguarda dados · tema recorrente

**Indicadores.** empregos_rais, empregos_od

**Vista.** `?modo=mapa`

**Achado.** Aguardando a RAIS pública por município/distrito para comparar o emprego formal com os locais de trabalho declarados na OD.

**Comparabilidade.**
- RAIS pública cobre só o emprego formal; distrito só na capital.

**Pendências.**
- F6: RAIS pública (PDET).

## 4. Comparabilidade e limitações

- 1977 cobre só a área central pesquisada; use o universo `área comparável de 1977` para séries estritas.
- Trabalho em casa e sem endereço fixo só é identificável de 2007 em diante; antes, esses ocupados aparecem como deslocamento intra-zonal. Séries de β, excesso e autocontenção têm versão comparável (inclui) e versão com local fixo (2007+).
- Excesso de deslocamento depende da agregação (MAUP) e da distância intra-unidade: publicamos só AMC e com faixa de sensibilidade.
- Zona × zona é esparsa: a interface sempre mostra a cobertura publicada; a série do par usa AMC.
- As referências bibliográficas devem ter títulos, volumes e DOIs conferidos antes da versão 1.0.

## 5. Agenda

H3 (res. 8/9) a partir das coordenadas 2007–2023; GTFS histórico e acessibilidade por transporte público; RAIS identificada; OD 2027; tempo observado por modo no modelo gravitacional.
