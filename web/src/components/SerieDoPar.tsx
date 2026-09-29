import { useEffect, useState } from "react";
import { parSerie } from "../db/queries";
import { POSICOES, segmentos, type PontoSerie } from "../lib/serie";
import { ROTULO_STATUS, type TipoFluxo } from "../lib/tipos";
import { num, num1, num2 } from "../lib/format";

type Campo = "total" | "pct_coletivo" | "dur_mediana" | "ief_par" | "share_da_origem";
const CAMPOS: { id: Campo; rotulo: string; fmt: (v: number) => string; escala: number }[] = [
  { id: "total", rotulo: "Viagens/dia", fmt: num, escala: 1 },
  { id: "pct_coletivo", rotulo: "Coletivo (%)", fmt: (v) => num1(v * 100), escala: 100 },
  { id: "dur_mediana", rotulo: "Duração mediana (min)", fmt: num, escala: 1 },
  { id: "ief_par", rotulo: "Saldo do par (IEF)", fmt: num2, escala: 1 },
  { id: "share_da_origem", rotulo: "% da origem", fmt: (v) => num1(v * 100), escala: 100 },
];
const W = 300, H = 110, PL = 8, PR = 8, PT = 14, PB = 18;
const xPos = (e: number) => PL + ((POSICOES.indexOf(e as any)) * (W - PL - PR)) / (POSICOES.length - 1);

function Grafico({ pontos, campo, cor, rotulo }: { pontos: PontoSerie[]; campo: (typeof CAMPOS)[number]; cor: string; rotulo: string }) {
  const vals = pontos.filter((p) => p.status === "publicado" && typeof p[campo.id] === "number").map((p) => p[campo.id] as number);
  const min = Math.min(0, ...vals), max = Math.max(1e-9, ...vals);
  const y = (v: number) => PT + (H - PT - PB) * (1 - (v - min) / (max - min || 1));
  const segs = segmentos(pontos, campo.id);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="serie" role="img" aria-label={`${campo.rotulo}: ${rotulo}`}>
      <line x1={PL} x2={W - PR} y1={y(0)} y2={y(0)} className="eixo" />
      {vals.length > 0 && <text x={W - PR} y={PT + 2} textAnchor="end" className="tick">máx. {campo.fmt(max)}</text>}
      {POSICOES.map((e) => <text key={e} x={xPos(e)} y={H - 4} textAnchor="middle" className="tick">{String(e).slice(2)}</text>)}
      {segs.map((s, i) => s.length > 1 && (
        <polyline key={i} points={s.map((p) => `${xPos(p.edicao)},${y(p[campo.id] as number)}`).join(" ")} fill="none" stroke={cor} strokeWidth={2} />
      ))}
      {POSICOES.map((e) => {
        const p = pontos.find((x) => x.edicao === e);
        if (!p) return <text key={e} x={xPos(e)} y={y(0) - 4} textAnchor="middle" className="aus"><title>{ROTULO_STATUS.nao_existia}</title>·</text>;
        if (p.status === "publicado" && typeof p[campo.id] === "number") {
          const v = p[campo.id] as number;
          return (
            <g key={e}>
              {p.cv != null && campo.id === "total" && <line x1={xPos(e)} x2={xPos(e)} y1={y(Math.max(min, v * (1 - 1.96 * p.cv / 100)))} y2={y(v * (1 + 1.96 * p.cv / 100))} stroke={cor} opacity={0.35} strokeWidth={5} />}
              <circle cx={xPos(e)} cy={y(v)} r={3.5} fill={cor}><title>{`${e}: ${campo.fmt(v)} (n=${p.n}, ${p.precisao})`}</title></circle>
            </g>
          );
        }
        const rot = p.status === "publicado" ? "sem valor nesta medida (amostra pequena)" : ROTULO_STATUS[p.status] ?? p.status;
        return <text key={e} x={xPos(e)} y={y(0) - 4} textAnchor="middle" className="aus"><title>{`${e}: ${rot}`}</title>×</text>;
      })}
    </svg>
  );
}

export function SerieDoPar({ nivel, tipo, o, d, nomeO, nomeD }: { nivel: "amc146" | "amc75" | "muni"; tipo: TipoFluxo; o: string; d: string; nomeO: string; nomeD: string }) {
  const [ida, setIda] = useState<PontoSerie[] | null>(null), [volta, setVolta] = useState<PontoSerie[] | null>(null);
  const [campo, setCampo] = useState<Campo>("total");
  useEffect(() => { setIda(null); setVolta(null); parSerie(nivel, tipo, o, d).then(setIda); parSerie(nivel, tipo, d, o).then(setVolta); }, [nivel, tipo, o, d]);
  const c = CAMPOS.find((x) => x.id === campo)!;
  return (
    <section className="serie-par" aria-label="Ao longo das pesquisas">
      <h4>Ao longo das pesquisas</h4>
      <div className="seg pequeno" role="group" aria-label="Medida">
        {CAMPOS.map((x) => <button key={x.id} className={campo === x.id ? "ativo" : ""} aria-pressed={campo === x.id} onClick={() => setCampo(x.id)}>{x.rotulo}</button>)}
      </div>
      {!ida ? <p className="nota">carregando…</p> : (
        <div className="duas">
          <div><p className="rot-serie"><i style={{ background: "var(--arc-in)" }} />{nomeO} → {nomeD}</p><Grafico pontos={ida} campo={c} cor="var(--arc-in)" rotulo="ida" /></div>
          <div><p className="rot-serie"><i style={{ background: "var(--arc-out)" }} />{nomeD} → {nomeO}</p>{volta && <Grafico pontos={volta} campo={c} cor="var(--arc-out)" rotulo="volta" />}</div>
        </div>
      )}
      <p className="nota">Pontos ligados só entre pesquisas consecutivas. <b>×</b> = amostra insuficiente ou fora da área; <b>·</b> = zoneamento inexistente. Nunca interpolamos.</p>
    </section>
  );
}
