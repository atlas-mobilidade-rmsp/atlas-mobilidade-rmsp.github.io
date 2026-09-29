import { useEffect, useMemo, useState } from "react";
import { sistemaSerie, unidades, unidadesSerie, type Linha, type MedidaSistema, type Unidade } from "../db/queries";
import { GraficoLinhas, type SerieLinha } from "./GraficoLinhas";
import { Busca } from "./Busca";
import { POSICOES } from "../lib/serie";
import { METRICAS, valorMetrica } from "../lib/tipos";
import { num, num1, num2 } from "../lib/format";
import { useStore } from "../state/store";

const QCOR = ["#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#0d3b7a"];
const pts = (d: MedidaSistema[], medida: string, cat: string, uni: string, f = (v: number) => v) =>
  POSICOES.map((e) => { const r = d.find((x) => x.edicao === e && x.medida === medida && x.categoria === cat && x.universo === uni); return { edicao: e, valor: r ? f(r.valor) : null, n: r?.n }; });

export function ModoPesquisas({ cabecalho }: { cabecalho: React.ReactNode }) {
  const s = useStore();
  const [sis, setSis] = useState<MedidaSistema[]>([]);
  const [nivelU, codU] = (s.us ?? "amc75:").split(":");
  const nivelSerie = (["amc75", "amc146", "muni"].includes(nivelU) ? nivelU : "amc75") as "amc75" | "amc146" | "muni";
  const [unid, setUnid] = useState<Unidade[]>([]);
  const [serU, setSerU] = useState<Linha[]>([]);
  useEffect(() => { sistemaSerie().then(setSis); }, []);
  useEffect(() => { unidades(2023, nivelSerie).then(setUnid); }, [nivelSerie]);
  useEffect(() => { if (codU) unidadesSerie(nivelSerie, codU).then(setSerU); else setSerU([]); }, [nivelSerie, codU]);
  const uni = s.univ;
  const m = METRICAS.find((x) => x.id === s.ms) ?? METRICAS[0];
  const nomeU = unid.find((u) => u.codigo === codU)?.nome;
  const quintis = ["q1", "q2", "q3", "q4", "q5"];
  const sq = (medida: string, f = (v: number) => v): SerieLinha[] => [
    ...quintis.map((q, i) => ({ id: q, rotulo: `Q${i + 1}${i === 0 ? " (mais pobre)" : i === 4 ? " (mais rico)" : ""}`, cor: QCOR[i], pontos: pts(sis, medida, q, uni, f) })),
    { id: "todos", rotulo: "Todos", cor: "var(--ink)", tracejada: true, pontos: pts(sis, medida, "todos", uni, f) },
  ];
  const modal = useMemo<SerieLinha[]>(() => [["coletivo", "Coletivo", "var(--arc-in)"], ["individual", "Individual motorizado", "var(--arc-out)"], ["a_pe", "A pé", "var(--precisao-boa)"], ["bicicleta", "Bicicleta", "var(--precisao-cautela)"]]
    .map(([c, r, cor]) => ({ id: c, rotulo: r, cor, pontos: pts(sis, "divisao_modal", c, uni, (v) => v * 100) })), [sis, uni]);
  const tempo: SerieLinha[] = [["coletivo", "Coletivo", "var(--arc-in)"], ["individual", "Individual motorizado", "var(--arc-out)"], ["a_pe", "A pé", "var(--precisao-boa)"]]
    .map(([c, r, cor]) => ({ id: c, rotulo: r, cor, pontos: pts(sis, "tempo_trab", c, uni) }));
  const serieUnidade: SerieLinha[] = [{ id: "u", rotulo: nomeU ?? codU ?? "", cor: "var(--acento-ativo)",
    pontos: POSICOES.map((e) => { const r = serU.find((x) => x.edicao === e); return { edicao: e, valor: r ? valorMetrica(m.id, r[m.id] as number | null) : null, n: r?.n_viag as number | undefined }; }) }];
  const ausentes = POSICOES.filter((e) => !serU.find((x) => x.edicao === e));
  const motivo = (e: number) => (nivelSerie === "amc146" && e < 1987 ? "não existia neste zoneamento" : e === 1977 ? "fora da área de 1977 ou sem amostra" : "sem amostra");
  return (
    <div className="app serie-modo">
      {cabecalho}
      <main className="pagina">
        <div className="controles linha-controles">
          <label className="grupo"><span className="rot">Universo do sistema</span>
            <select value={uni} onChange={(e) => s.set({ univ: e.target.value as any })}>
              <option value="edicao">Área pesquisada em cada edição</option><option value="area1977">Área comparável de 1977 (75 AMC)</option></select></label>
        </div>
        <h2>Sistema metropolitano</h2>
        <div className="grade-graficos">
          <GraficoLinhas series={sq("ind_mob", (v) => v)} fmt={num2} titulo="Índice de mobilidade por quintil de renda (viagens/hab.)" />
          <GraficoLinhas series={sq("imob_15m", (v) => v * 100)} fmt={(v) => `${num(v)}%`} titulo="Imobilidade (15+ sem viagem) por quintil" />
          <GraficoLinhas series={modal} fmt={(v) => `${num(v)}%`} titulo="Divisão modal (% das viagens)" zero />
          <GraficoLinhas series={tempo} fmt={num} titulo="Tempo médio das viagens casa→trabalho (min)" zero />
          <GraficoLinhas series={[{ id: "b", rotulo: "β (1/km) — exponencial", cor: "var(--acento-ativo)", pontos: pts(sis, "beta_dist_km", "exp", "area1977") }]} fmt={num2} titulo="Fricção da distância: β do modelo gravitacional (AMC-75)" zero />
          <GraficoLinhas series={[{ id: "x", rotulo: "Excesso de deslocamento (distância)", cor: "var(--arc-out)", pontos: pts(sis, "excesso_dist_km", "amc75", "area1977", (v) => v * 100) }]} fmt={(v) => `${num1(v)}%`} titulo="Excesso de deslocamento casa–trabalho (AMC-75)" zero />
          <GraficoLinhas series={[{ id: "a", rotulo: "Automóveis/100 hab.", cor: "var(--acento-ativo)", pontos: pts(sis, "autos_100hab", "todos", uni) }]} fmt={num} titulo="Motorização (automóveis por 100 habitantes)" zero />
          <GraficoLinhas series={[{ id: "g", rotulo: "Gini do potencial de empregos", cor: "var(--arc-in)", pontos: pts(sis, "gini_hansen_emp", "amc75", "area1977") }]} fmt={num2} titulo="Desigualdade de acesso a empregos (Gini de Hansen, AMC-75)" />
        </div>
        <p className="nota">A queda de 2023 é real nos dados (campo no pós-pandemia). Medidas de 1977 cobrem só a área pesquisada então (~95 % da população). Q1–Q5: renda familiar per capita, deflacionada (INPC), por edição.</p>
        <h2>Uma unidade ao longo das pesquisas</h2>
        <div className="controles linha-controles">
          <label className="grupo"><span className="rot">Unidade</span>
            <select value={nivelSerie} onChange={(e) => s.set({ us: `${e.target.value}:` })}>
              <option value="amc75">AMC 1977–2023 (75)</option><option value="amc146">AMC 1987–2023 (146)</option><option value="muni">Município</option></select></label>
          <label className="grupo"><span className="rot">Indicador</span>
            <select value={m.id} onChange={(e) => s.set({ ms: e.target.value })}>{METRICAS.map((x) => <option key={x.id} value={x.id}>{x.rotulo}</option>)}</select></label>
          <div className="grupo"><span className="rot">Buscar</span><Busca unidades={unid} onEscolher={(c) => s.set({ us: `${nivelSerie}:${c}` })} /></div>
        </div>
        {codU ? (<>
          <GraficoLinhas series={serieUnidade} fmt={(v) => (m.casas >= 2 ? num2(v) : m.casas === 1 ? num1(v) : num(v))} titulo={`${m.rotulo} — ${nomeU ?? codU}`} zero={m.id !== "ief"} />
          {ausentes.length > 0 && <p className="nota">Sem estimativa: {ausentes.map((e) => `${e} (${motivo(e)})`).join("; ")}. Nunca interpolamos.</p>}
        </>) : <p className="nota">Escolha uma unidade para ver o indicador em todas as pesquisas.</p>}
      </main>
    </div>
  );
}
