import { useEffect, useState } from "react";
import { estadoDaVista, ROTULO_STATUS_PERGUNTA, type Pergunta } from "../lib/perguntas";
import { useStore } from "../state/store";
import { METRICAS } from "../lib/tipos";

export function Perguntas({ cabecalho }: { cabecalho: React.ReactNode }) {
  const set = useStore((s) => s.set);
  const [ps, setPs] = useState<Pergunta[] | null>(null);
  const [aberta, setAberta] = useState<number | null>(null);
  useEffect(() => { fetch(new URL("data/perguntas.json", document.baseURI)).then((r) => r.json()).then(setPs); }, []);
  const nomeMetrica = (id: string) => METRICAS.find((m) => m.id === id)?.rotulo ?? id;
  const grupo = (tema: Pergunta["tema"], titulo: string, sub: string) => (
    <section aria-labelledby={`t-${tema}`}>
      <h2 id={`t-${tema}`}>{titulo}</h2><p className="nota">{sub}</p>
      <div className="grade-perguntas">
        {ps!.filter((p) => p.tema === tema).map((p) => (
          <article key={p.id} className={`cartao ${p.status}`} id={p.slug}>
            <header><span className={`status ${p.status}`}>{ROTULO_STATUS_PERGUNTA[p.status]}</span><h3>{p.titulo}</h3></header>
            <p className="pergunta">{p.pergunta}</p>
            <p className="achado">{p.achado.texto}</p>
            <div className="acoes">
              {p.status !== "aguarda_dados" && <button className="primario" onClick={() => set(estadoDaVista(p.vista))}>Ver no atlas</button>}
              <button onClick={() => setAberta(aberta === p.id ? null : p.id)} aria-expanded={aberta === p.id}>{aberta === p.id ? "Menos" : "Fontes e limites"}</button>
            </div>
            {aberta === p.id && (
              <div className="detalhe">
                {p.indicadores.length > 0 && <p><b>Indicadores:</b> {p.indicadores.map(nomeMetrica).join(", ")}</p>}
                {p.comparabilidade && p.comparabilidade.length > 0 && <><b>Comparabilidade</b><ul>{p.comparabilidade.map((c, i) => <li key={i}>{c}</li>)}</ul></>}
                {p.dados && p.dados.length > 0 && <p><b>Dados:</b> {p.dados.join("; ")}</p>}
                {p.pendencias && p.pendencias.length > 0 && <><b>Pendências</b><ul>{p.pendencias.map((c, i) => <li key={i}>{c}</li>)}</ul></>}
                {p.literatura && p.literatura.length > 0 && <><b>Literatura</b><ul>{p.literatura.map((l, i) => <li key={i}>{l.autores} ({l.ano}). <i>{l.titulo}</i>{l.onde ? `. ${l.onde}` : ""}{l.doi ? <> · <a href={`https://doi.org/${l.doi}`} target="_blank" rel="noreferrer">doi</a></> : null}</li>)}</ul></>}
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
  return (
    <div className="app serie-modo">
      {cabecalho}
      <main className="pagina larga">
        <h1 className="titulo-pagina">Perguntas</h1>
        <p className="nota">Cada cartão responde a uma pergunta com números calculados diretamente dos dados publicados e leva à vista do atlas que a mostra. Perguntas sem dados suficientes estão marcadas.</p>
        {!ps ? <p className="nota">carregando…</p> : (<>
          {grupo("recorrente", "Perguntas recorrentes", "As questões clássicas da literatura de mobilidade urbana.")}
          {grupo("emergente", "Perguntas emergentes", "Temas recentes: pós-pandemia, trabalho híbrido, aplicativos, cuidado, raça, proximidade.")}
        </>)}
      </main>
    </div>
  );
}
