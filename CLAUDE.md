# Atlas da Mobilidade na RMSP

Atlas web estático (GitHub Pages) orientado a perguntas sobre a mobilidade na RMSP, 1977–2023, a partir da
Pesquisa Origem e Destino do Metrô-SP. Mesma arquitetura do Atlas da Migração Interna (deck.gl `OrthographicView`
sobre TopoJSON em metros, DuckDB-WASM, estado na URL, gate antes de publicar). Plano: `docs/PLANO.md`.

## Regras não negociáveis
- O laboratório `metrosp` é a fonte (`METROSP_ROOT`, ver `pipeline/fontes.py`). Este repo **lê**, nunca copia microdado
  bruto (`viagens/pessoas/domicilios` linha a linha). Só agregados que passaram no gate entram em `data/processed/`.
- Nunca imprimir linhas individuais de microdado em logs, testes ou conversa.
- Gate de precisão P1–P6 (`pipeline/precisao_regras.py`): confiabilidade, não sigilo. `.gate_ok` (SHA-256) é escrito por
  `gate_check.py`; `verify_gate.py` roda no CI; o hook `scripts/pre-commit` recusa commit sem gate verde.
- Sem interpolar ausências na série: `não existia`, `fora da área de 1977`, `n insuficiente`.
- Toda tabela traz `n` amostral; ponderadas trazem `cv` e `precisao`.
- CRS interno EPSG:31983 (metros); nada de reprojeção no frame cartesiano.

## Orquestração (menor modelo que resolve)
`mecanico` (Haiku) tarefas fechadas com critério automático · `implementador` (Sonnet) código com desenho definido ·
`revisor_dados` (Sonnet) reconciliação/invariantes · `metodologo` (Opus) decisões de método · `auditor` (Fable) só em
checkpoints (≤ 4 na v1); nunca implementa.

## Comandos
- `python -m pytest` (pipeline) · `cd web && npm test && npm run build`
- `python pipeline/run.py` (pipeline completo) · `cd web && npm run sync-data`
