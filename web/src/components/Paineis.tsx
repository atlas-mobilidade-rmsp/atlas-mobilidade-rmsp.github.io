import { useEffect, useState } from "react";
import { perfilFluxo, perfilUnidade, type Cat, type Fluxo, type Indicadores, type Unidade } from "../db/queries";
import { METRICAS, ROTULO_PRECISAO, TIPOS, valorMetrica, type Nivel, type Precisao, type TipoFluxo } from "../lib/tipos";
import { num, num1, num2 } from "../lib/format";
import { BarrasDimensao } from "./Barras";
import { SerieDoPar } from "./SerieDoPar";
import { useStore } from "../state/store";
import { AbaEstrutura, AbaFluxos, AbaPopulacao } from "./AbasUnidade";

const fmt = (id: string, v: number | null) => {
  const m = METRICAS.find((x) => x.id === id); if (v == null || !m) return "—";
  return (m.casas >= 2 ? num2 : m.casas === 1 ? num1 : num)(v) + (m.unidade === "%" ? " %" : "");
};
export const Selo = ({ p }: { p: string }) => <span className={`selo ${p}`}>{ROTULO_PRECISAO[p as Precisao] ?? p}</span>;

type Aba = "resumo" | "populacao" | "estrutura" | "fluxos";
export function PainelUnidade({ u, ind, nivel, ed, tipo, nomes }: { u: Unidade; ind?: Indicadores; nivel: Nivel; ed: number; tipo: TipoFluxo; nomes: Map<string, string> }) {
  const [perfil, setPerfil] = useState<Cat[]>([]);
  const [aba, setAba] = useState<Aba>("resumo");
  useEffect(() => { perfilUnidade(ed, nivel, u.codigo).then(setPerfil); }, [ed, nivel, u.codigo]);
  const set = useStore((s) => s.set);
  return (
    <article className="painel" aria-label={`Unidade ${u.nome}`}>
      <header><h3>{u.nome}</h3><button className="fechar" aria-label="Limpar seleção" onClick={() => set({ unidade: null, par: null })}>×</button></header>
      <div className="seg pequeno abas" role="tablist" aria-label="Seções da unidade">
        {([["resumo", "Resumo"], ["populacao", "População"], ["estrutura", "Estrutura"], ["fluxos", "Fluxos"]] as [Aba, string][]).map(([id, r]) =>
          <button key={id} role="tab" aria-selected={aba === id} className={aba === id ? "ativo" : ""} onClick={() => setAba(id)}>{r}</button>)}
      </div>
      {aba === "populacao" && <AbaPopulacao nivel={nivel} ed={ed} codigo={u.codigo} />}
      {aba === "estrutura" && <AbaEstrutura nivel={nivel} ed={ed} codigo={u.codigo} ind={ind} />}
      {aba === "fluxos" && <AbaFluxos nivel={nivel} ed={ed} tipo={tipo} codigo={u.codigo} nomes={nomes} />}
      {aba !== "resumo" ? null : !ind ? <p className="nota">Sem estimativa para esta unidade nesta pesquisa.</p> : (<>
        <dl className="kpis">
          <div><dt>População</dt><dd>{num(ind.pop as number)}</dd></div>
          <div><dt>Viagens/dia</dt><dd>{num(ind.viagens as number)}</dd></div>
          <div><dt>Amostra</dt><dd>{num(ind.n_viag as number)} viagens <Selo p={String(ind.precisao)} /></dd></div>
        </dl>
        <table className="tabela"><tbody>
          {METRICAS.map((m) => <tr key={m.id} title={m.ajuda}><th scope="row">{m.rotulo}</th><td>{fmt(m.id, valorMetrica(m.id, ind[m.id] as number | null))}</td></tr>)}
        </tbody></table>
        <BarrasDimensao dados={perfil} dimensao="sexo" />
        <BarrasDimensao dados={perfil} dimensao="idade" />
        <BarrasDimensao dados={perfil} dimensao="renda_q" />
      </>)}
    </article>
  );
}

export function PainelFluxo({ f, nivel, ed, tipo, nomes, nivelSerie }: { f: Fluxo; nivel: Nivel; ed: number; tipo: string; nomes: Map<string, string>; nivelSerie: { nivel: "amc146" | "amc75" | "muni"; o: string; d: string } | null }) {
  const [dim, setDim] = useState<Cat[]>([]);
  const set = useStore((s) => s.set);
  useEffect(() => { perfilFluxo(ed, nivel, tipo as any, f.origem, f.destino).then(setDim); }, [ed, nivel, tipo, f.origem, f.destino]);
  const nd = tipo === "casa_trab" ? "n/d (pendular)" : "amostra < 30";
  const nO = nomes.get(f.origem) ?? f.origem, nD = nomes.get(f.destino) ?? f.destino;
  return (
    <article className="painel" aria-label="Fluxo selecionado">
      <header><h3>{nO} → {nD}</h3><button className="fechar" aria-label="Fechar fluxo" onClick={() => set({ par: null })}>×</button></header>
      <p className="nota">{TIPOS.find((t) => t.id === tipo)?.rotulo} · {ed}</p>
      <dl className="kpis">
        <div><dt>Viagens/dia</dt><dd>{num(f.total)}</dd></div>
        <div><dt>Amostra</dt><dd>n = {num(f.n)} <Selo p={f.precisao} /></dd></div>
        <div><dt>CV</dt><dd>{f.cv == null ? "—" : `${num1(f.cv)} %`}</dd></div>
        <div><dt>Duração mediana</dt><dd>{f.dur_mediana == null ? nd : `${num(f.dur_mediana)} min`}</dd></div>
        <div><dt>Coletivo</dt><dd>{f.pct_coletivo == null ? nd : `${num(f.pct_coletivo * 100)} %`}</dd></div>
        <div><dt>Saldo do par</dt><dd title="(ida − volta)/(ida + volta)">{f.ief_par == null ? "—" : num2(f.ief_par)}</dd></div>
        <div><dt>Distância entre centros</dt><dd>{num1(f.dist_km)} km</dd></div>
      </dl>
      {dim.length === 0 && <p className="nota">Perfil detalhado só para pares com n ≥ 30 (níveis agregados).</p>}
      {["modo", "motivo", "renda_q", "sexo", "idade", "escolaridade", "hora_saida", "duracao_faixa", "setor"].map((d) => <BarrasDimensao key={d} dados={dim} dimensao={d} />)}
      {nivelSerie ? <SerieDoPar nivel={nivelSerie.nivel} tipo={tipo as any} o={nivelSerie.o} d={nivelSerie.d} nomeO={nO} nomeD={nD} />
        : <p className="nota">A série histórica deste par não está disponível para este nível (subprefeituras só existem desde 1997).</p>}
    </article>
  );
}
