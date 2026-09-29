# Metodologia

## Fonte e universo
Pesquisa Origem e Destino do Metrô-SP, seis edições (1977, 1987, 1997, 2007, 2017, 2023), microdados públicos harmonizados no laboratório `metrosp` (variáveis presentes em todas as edições, recodificadas ao nível comum). Populações, viagens e domicílios expandidos reproduzem os totais oficiais (tolerância 0,3%). 1977 cobre ~41% da área da RMSP e ~95% da população.

## Unidades territoriais
Zona OD do ano (243–527); AMC de 146 áreas (1987–2023) e de 75 (1977–2023), definidas por grafo de sobreposição entre zonas; município; subprefeituras de São Paulo + demais municípios (`sub`), só de 1997 em diante (as zonas de 1997–2023 encaixam ≥ 98,6% na subprefeitura dominante; AMC-146 só 65%, por isso `sub` fica fora da série). Geometria em EPSG:31983 (metros), simplificada com mapshaper.

## Indicadores
Por unidade de residência, ponderados: população, viagens, índice de mobilidade (viagens/hab.), imobilidade (15+ sem viagem), divisão modal, tempo de viagem casa→trabalho, motorização, renda familiar (R$ 2023, INPC), produção/atração e IEF, emprego–moradia. Empregos = ocupados com local fixo de trabalho pela zona do 1º trabalho. Quintis de renda: renda familiar per capita deflacionada, por edição, ponderado por pessoa.

## Gate de precisão (P1–P6)
Confiabilidade estatística (não sigilo: o microdado é público). P1 células com n ≥ 5 (senão `outros`); P2 fluxos de zona n ≥ 10, demais níveis n ≥ 5 com selo; P3 perfis, medianas e percentuais de fluxo só com n ≥ 30; P4 CV aproximado por pesos (deff = 1; calibração por bootstrap prevista), classes 15%/30%; P5 coerência entre níveis; P6 comparabilidade por edição (`comparabilidade.json`). `gate_check.py` carimba SHA-256 dos arquivos; `verify_gate.py` roda no CI.

## Modelo gravitacional, Hansen e excesso
Matriz casa–trabalho completa (ocupados com local fixo). Modelo duplamente restrito de Wilson, `T_ij = A_i O_i B_j D_j f(c_ij)`, `f = exp(−βc)` ou `c^−γ`, com parâmetro calibrado até MTL_modelo = MTL_observado. Impedâncias: distância entre centroides (ponderados por domicílios do Censo 2022; intra-unidade `⅔·√(A/π)`, sensibilidade 0,5–1,0) e tempo observado (imputado por regressão log–log). Potencial de Hansen com o mesmo β. Excesso de deslocamento (Hamilton, White) e utilização da capacidade (Horner) por programação linear (T_min, T_max). Sensível à agregação (MAUP); publicado só para AMC.

## Auditoria (checkpoint F4)
Uma auditoria independente identificou que trabalho em casa e sem endereço fixo (`trab1_re` = 1 ou 3, presente de 2007 em diante) entrava na matriz como pseudo-deslocamento intra-zonal, contaminando autocontenção, β e excesso, e criando uma quebra artificial entre 1997 e 2007. Correção: a versão principal exclui esses ocupados de 2007 em diante; a versão "comparável" mantém o tratamento de 1977–1997. Na versão comparável, β (≈ 0,26/km) e excesso (≈ 34–35%) são estáveis; a versão com local fixo (2007–2023) mostra excesso de 36% a 38%. Também foram corrigidos: unidades sem residentes amostrados (agora presentes nos totais) e rótulos de faixas.

## Limitações conhecidas
Renda individual tem alta recusa (usa-se a familiar); imputação de renda familiar cresce de 11% a ~55%; deff = 1 até a calibração por bootstrap; escolha de modo não distingue táxi de aplicativo; pesquisa de um dia útil; distâncias entre centroides não são rede viária.
