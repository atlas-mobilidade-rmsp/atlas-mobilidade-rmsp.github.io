import { METRICAS, valorMetrica } from "../lib/tipos";
import { paletaLegenda, quebrasDivergentes, quebrasQuantis, rgb } from "../lib/cores";
import type { Indicadores } from "../db/queries";
import { useEscuro } from "../map/MapaAtlas";
import { num, num1, num2 } from "../lib/format";

export function Legenda({ metrica, indic }: { metrica: string; indic: Indicadores[] }) {
  const escuro = useEscuro();
  const m = METRICAS.find((x) => x.id === metrica)!;
  const vals = indic.map((r) => valorMetrica(metrica, r[metrica] as number | null)).filter((v): v is number => v != null);
  const q = m.divergente ? quebrasDivergentes(vals) : quebrasQuantis(vals, 5);
  const pal = paletaLegenda(!!m.divergente, escuro);
  const f = m.casas >= 2 ? num2 : m.casas === 1 ? num1 : num;
  const rotulo = (i: number) => (i === 0 ? `< ${f(q[0])}` : i === pal.length - 1 ? `≥ ${f(q[q.length - 1])}` : `${f(q[i - 1])} – ${f(q[i])}`);
  return (
    <div className="legenda" aria-label={`Legenda: ${m.rotulo}`}>
      <strong>{m.rotulo}</strong> <span className="un">{m.unidade}</span>
      <ul>{q.length > 0 && pal.map((c, i) => <li key={i}><i style={{ background: rgb(c) }} />{rotulo(i)}</li>)}</ul>
      <p className="nota">Cinza: sem estimativa (amostra insuficiente). Fluxos: azul = chegam à unidade; laranja = saem.</p>
    </div>
  );
}
