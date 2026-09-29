import { POSICOES } from "../lib/serie";

export interface SerieLinha { id: string; rotulo: string; cor: string; pontos: { edicao: number; valor: number | null; n?: number }[]; tracejada?: boolean }
const W = 340, H = 150, PL = 34, PR = 10, PT = 12, PB = 20;

/** Linhas por edição; valores nulos quebram a linha (nunca se interpola). */
export function GraficoLinhas({ series, fmt, titulo, zero = false, posicoes = POSICOES as readonly number[] }: { series: SerieLinha[]; fmt: (v: number) => string; titulo: string; zero?: boolean; posicoes?: readonly number[] }) {
  const xp = (e: number) => PL + (posicoes.indexOf(e) * (W - PL - PR)) / (posicoes.length - 1);
  const vs = series.flatMap((s) => s.pontos.map((p) => p.valor).filter((v): v is number => v != null));
  if (!vs.length) return <p className="nota">Sem dados para “{titulo}”.</p>;
  const min = zero ? Math.min(0, ...vs) : Math.min(...vs), max = Math.max(...vs);
  const pad = (max - min || 1) * 0.08;
  const lo = zero ? min : min - pad, hi = max + pad;
  const y = (v: number) => PT + (H - PT - PB) * (1 - (v - lo) / (hi - lo));
  const ticks = [lo + pad * (zero ? 0 : 1), (lo + hi) / 2, hi - pad];
  return (
    <figure className="grafico">
      <figcaption>{titulo}</figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="serie" role="img" aria-label={titulo}>
        {ticks.map((t, i) => <g key={i}><line x1={PL} x2={W - PR} y1={y(t)} y2={y(t)} className="grade" /><text x={PL - 4} y={y(t) + 3} textAnchor="end" className="tick">{fmt(t)}</text></g>)}
        {posicoes.map((e) => <text key={e} x={xp(e)} y={H - 5} textAnchor="middle" className="tick">{e}</text>)}
        {series.map((s) => {
          const seg: { edicao: number; valor: number }[][] = []; let atual: { edicao: number; valor: number }[] = [];
          for (const e of posicoes) {
            const p = s.pontos.find((q) => q.edicao === e);
            if (p && p.valor != null) atual.push({ edicao: e, valor: p.valor }); else if (atual.length) { seg.push(atual); atual = []; }
          }
          if (atual.length) seg.push(atual);
          return (
            <g key={s.id}>
              {seg.map((g, i) => g.length > 1 && <polyline key={i} points={g.map((p) => `${xp(p.edicao)},${y(p.valor)}`).join(" ")} fill="none" stroke={s.cor} strokeWidth={2} strokeDasharray={s.tracejada ? "4 3" : undefined} />)}
              {s.pontos.filter((p) => p.valor != null).map((p) => <circle key={p.edicao} cx={xp(p.edicao)} cy={y(p.valor!)} r={3} fill={s.cor}><title>{`${s.rotulo} ${p.edicao}: ${fmt(p.valor!)}${p.n ? ` (n=${p.n})` : ""}`}</title></circle>)}
            </g>
          );
        })}
      </svg>
      <ul className="leg">{series.map((s) => <li key={s.id}><i style={{ background: s.cor }} />{s.rotulo}</li>)}</ul>
    </figure>
  );
}
