"""Gera docs/ANALISE.md a partir de data/processed/perguntas.json (números injetados; nada digitado à mão)."""
import json

from pipeline.fontes import PROCESSED, REPO_ROOT

VISTA_QS = {"modo": "modo", "ed": "ed", "nivel": "n", "metrica": "m", "tipo": "t", "unidade": "u", "univ": "univ", "ms": "ms", "us": "us"}


def link(v: dict) -> str:
    q = "&".join(f"{VISTA_QS[k]}={val}" for k, val in v.items() if k in VISTA_QS)
    return f"?{q}" if q else "?"


def main() -> None:
    ps = json.loads((PROCESSED / "perguntas.json").read_text())
    o = ["# Análise: perguntas e achados", "",
         "Gerado por `python -m pipeline.build_analise` a partir de `data/processed/perguntas.json`; os números vêm dos dados publicados. "
         "Formato de cada seção: pergunta → indicadores → vista (link de exemplo, relativo ao site) → achado → literatura → comparabilidade.", "",
         "## 1. Por que um atlas orientado a perguntas", "",
         "Cada vista do atlas responde a uma pergunta recorrente da literatura de mobilidade urbana ou a um tema emergente, em vez de expor a matriz de dados crua.", "",
         "## 2. Dados e método", "",
         "Pesquisa Origem e Destino do Metrô-SP (1977, 1987, 1997, 2007, 2017, 2023) harmonizada; Áreas Mínimas Comparáveis (146 desde 1987, 75 desde 1977); censos 1970–2022 e CNEFE 2022 por unidade; gate de precisão P1–P6; "
         "modelo gravitacional duplamente restrito, potencial de Hansen e excesso de deslocamento. Detalhes em `docs/METODOLOGIA.md` e `docs/DECISOES.md`.", "", "## 3. Achados", ""]
    for i, p in enumerate(ps, 1):
        o += [f"### 3.{i} {p['titulo']}", "", f"**Pergunta.** {p['pergunta']}", "", f"**Status.** {p['status'].replace('_', ' ')} · tema {p['tema']}", "",
              f"**Indicadores.** {', '.join(p['indicadores'])}", "", f"**Vista.** `{link(p['vista'])}`", "", f"**Achado.** {p['achado']['texto']}", ""]
        if p.get("literatura"):
            o += ["**Literatura.**"] + [f"- {l['autores']} ({l['ano']}). *{l['titulo']}*" + (f". {l['onde']}" if l.get("onde") else "") + (f". doi:{l['doi']}" if l.get("doi") else "") for l in p["literatura"]] + [""]
        if p.get("comparabilidade"):
            o += ["**Comparabilidade.**"] + [f"- {c}" for c in p["comparabilidade"]] + [""]
        if p.get("pendencias"):
            o += ["**Pendências.**"] + [f"- {c}" for c in p["pendencias"]] + [""]
    o += ["## 4. Comparabilidade e limitações", "",
          "- 1977 cobre só a área central pesquisada; use o universo `área comparável de 1977` para séries estritas.",
          "- Trabalho em casa e sem endereço fixo só é identificável de 2007 em diante; antes, esses ocupados aparecem como deslocamento intra-zonal. Séries de β, excesso e autocontenção têm versão comparável (inclui) e versão com local fixo (2007+).",
          "- Excesso de deslocamento depende da agregação (MAUP) e da distância intra-unidade: publicamos só AMC e com faixa de sensibilidade.",
          "- Zona × zona é esparsa: a interface sempre mostra a cobertura publicada; a série do par usa AMC.",
          "- As referências bibliográficas devem ter títulos, volumes e DOIs conferidos antes da versão 1.0.", "",
          "## 5. Agenda", "", "H3 (res. 8/9) a partir das coordenadas 2007–2023; GTFS histórico e acessibilidade por transporte público; RAIS identificada; OD 2027; tempo observado por modo no modelo gravitacional."]
    (REPO_ROOT / "docs" / "ANALISE.md").write_text("\n".join(o) + "\n")
    print("docs/ANALISE.md:", len(ps), "achados")


if __name__ == "__main__":
    main()
