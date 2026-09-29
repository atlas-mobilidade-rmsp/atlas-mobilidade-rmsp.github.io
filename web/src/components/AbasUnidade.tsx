import { useEffect, useState } from "react";
import { acessibilidadeUnidade, censoUnidade, cnefeUnidade, empregoFormal, gravitacional, vizinhos, type Linha } from "../db/queries";
import { GraficoLinhas } from "./GraficoLinhas";
import { num, num1, num2 } from "../lib/format";
import type { Nivel, TipoFluxo } from "../lib/tipos";
import { Selo } from "./Paineis";
import { useStore } from "../state/store";

const CENSOS = [1970, 1980, 1991, 2000, 2010, 2022] as const;
const GRUPOS: Record<string, string> = { alimentacao: "Alimentação", compras: "Compras", servicos: "Serviços", industria_logistica: "Indústria e logística", religioso: "Religioso",
  educacao: "Educação", saude: "Saúde", lazer_cultura: "Lazer e cultura", residencial: "Residencial", em_construcao: "Em construção", nao_classificado: "Não classificado", sem_uso: "Sem uso", estacionamento: "Estacionamento", hospedagem: "Hospedagem", publico_institucional: "Público/institucional" };

export function AbaPopulacao({ nivel, ed, codigo }: { nivel: Nivel; ed: number; codigo: string }) {
  const [c, setC] = useState<Linha[]>([]), [cn, setCn] = useState<{ grupo: string; n: number }[]>([]);
  useEffect(() => { censoUnidade(nivel, ed, codigo).then(setC); cnefeUnidade(nivel, ed, codigo).then(setCn); }, [nivel, ed, codigo]);
  const ser = (campo: string, cor: string, rotulo: string) => ({ id: campo, rotulo, cor, pontos: CENSOS.map((a) => ({ edicao: a, valor: (c.find((r) => r.ano_censo === a)?.[campo] as number | null) ?? null })) });
  const tot = cn.reduce((s, x) => s + x.n, 0);
  return (
    <div className="aba">
      <p className="nota">Censos 1970–2022 interpolados por área para esta unidade; 1970 e 1980 só têm resolução municipal (mesma composição dentro do município).</p>
      <GraficoLinhas posicoes={CENSOS} series={[ser("pop_total", "var(--acento-ativo)", "População")]} fmt={(v) => num(v)} titulo="População (Censo)" zero />
      <GraficoLinhas posicoes={CENSOS} series={[ser("pct_60m", "var(--arc-out)", "60 anos ou mais (%)")]} fmt={(v) => num1(v)} titulo="Envelhecimento: % com 60+" zero />
      <GraficoLinhas posicoes={CENSOS} series={[ser("renda_resp_r2023", "var(--arc-in)", "Renda do responsável (R$ 2023)")]} fmt={(v) => num(v)} titulo="Renda média do responsável (R$ de 2023)" zero />
      <GraficoLinhas posicoes={CENSOS} series={[ser("moradores_por_dom", "var(--div-neg-2)", "Moradores por domicílio")]} fmt={(v) => num2(v)} titulo="Moradores por domicílio" />
      {tot > 0 && (
        <figure className="barras"><figcaption>Endereços por uso (CNEFE 2022): {num(tot)}</figcaption>
          {cn.slice(0, 8).map((x) => <div key={x.grupo} className="linha"><span className="cat">{GRUPOS[x.grupo] ?? x.grupo}</span><span className="trilha"><span className="preench" style={{ width: `${(100 * x.n) / cn[0].n}%` }} /></span><span className="v">{num(x.n)}</span></div>)}
        </figure>)}
    </div>
  );
}

const ROT_EST: [string, string, string, (v: number) => string][] = [
  ["hansen_emp_exp_dist_km", "Potencial de empregos (Hansen)", "Σ empregos × exp(−β·distância): quantos empregos ‘cabem’ ao alcance, com β calibrado para a edição.", num],
  ["hansen_pop_exp_dist_km", "Potencial de população (Hansen)", "Mesmo cálculo com a população: mercado de mão de obra/consumo ao alcance.", num],
  ["jobs_housing_od", "Empregos / ocupados residentes", "Razão emprego–moradia a partir da matriz casa–trabalho (universo da AMC/município).", num2],
  ["autocont", "Autocontenção", "Parcela dos ocupados residentes que trabalha na própria unidade.", (v) => `${num1(v * 100)} %`],
  ["t_medio_obs_dist_km", "Distância média casa–trabalho (obs.)", "Média ponderada entre centroides (km).", num1],
  ["t_medio_min_dist_km", "Distância mínima possível (realocação)", "Média se os trabalhadores fossem realocados aos empregos mais próximos (problema de transporte).", num1],
];
const ANOS_RAIS = [2007, 2017, 2023] as const;
const GRUPOS_RAIS: [string, string][] = [["pct_industria", "Indústria"], ["pct_construcao", "Construção"], ["pct_comercio", "Comércio"], ["pct_servicos", "Serviços"], ["pct_adm_publica_edu_saude", "Adm. pública, educação e saúde"]];
function EmpregoFormal({ codigo }: { codigo: string }) {
  const [d, setD] = useState<Linha[] | undefined>(undefined);
  useEffect(() => { setD(undefined); empregoFormal(codigo).then(setD); }, [codigo]);
  if (d === undefined || d.length === 0) return null;
  const v = (ano: number, k: string) => d.find((x) => x.ano === ano)?.[k] as number | null | undefined;
  const cel = (ano: number, k: string, f: (x: number) => string) => { const x = v(ano, k); return <td key={ano}>{x != null ? f(x) : "—"}</td>; };
  return (
    <section>
      <h4>Emprego formal (RAIS)</h4>
      <table className="tabela"><thead><tr><th></th>{ANOS_RAIS.map((a) => <th key={a}>{a}</th>)}</tr></thead><tbody>
        <tr><th scope="row">Vínculos ativos em 31/12</th>{ANOS_RAIS.map((a) => cel(a, "vinculos", num))}</tr>
        <tr title="Empregos declarados pelos moradores da RMSP na OD, com local de trabalho fixo neste município."><th scope="row">Empregos na OD</th>{ANOS_RAIS.map((a) => cel(a, "empregos_od", num))}</tr>
        <tr title="Não mede formalidade: a RAIS inclui quem mora fora da RMSP e vínculos múltiplos; a OD inclui informais."><th scope="row">RAIS / OD</th>{ANOS_RAIS.map((a) => cel(a, "razao_rais_od", num2))}</tr>
        <tr><th scope="row">Remuneração média (SM)</th>{ANOS_RAIS.map((a) => cel(a, "rem_media_sm", num2))}</tr>
        {GRUPOS_RAIS.map(([k, r]) => <tr key={k}><th scope="row">{r} (%)</th>{ANOS_RAIS.map((a) => cel(a, k, (x) => num1(100 * x)))}</tr>)}
      </tbody></table>
      <p className="nota">RAIS pública (MTE): vínculos ativos em 31/12 por município de trabalho, remuneração média em salários mínimos. Só município inteiro; a razão RAIS/OD não mede formalidade (ver Perguntas, nº 21).</p>
    </section>
  );
}

export function AbaEstrutura({ nivel, ed, codigo, ind }: { nivel: Nivel; ed: number; codigo: string; ind?: Record<string, any> }) {
  const [g, setG] = useState<Linha | null | undefined>(undefined);
  useEffect(() => { setG(undefined); gravitacional(ed, nivel, codigo).then(setG); }, [ed, nivel, codigo]);
  if (nivel === "zona") return <p className="nota">Medidas de estrutura (gravidade, Hansen, excesso) não são calculadas por zona; use AMC, município ou subprefeitura.</p>;
  if (g === undefined) return <p className="nota">carregando…</p>;
  const obs = g?.t_medio_obs_dist_km as number | undefined, min = g?.t_medio_min_dist_km as number | undefined;
  return (
    <div className="aba">
      <table className="tabela"><tbody>
        {ROT_EST.map(([k, r, h, f]) => <tr key={k} title={h}><th scope="row">{r}</th><td>{g && g[k] != null ? f(g[k] as number) : "—"}</td></tr>)}
        {obs && min ? <tr title="(distância observada − mínima)/observada; depende da agregação (MAUP)."><th scope="row">Excesso de deslocamento</th><td>{num1((100 * (obs - min)) / obs)} %</td></tr> : null}
        {ind && <>
          <tr title="Viagens produzidas (moradores) e atraídas (destinos não residenciais)."><th scope="row">Atração / produção</th><td>{num2(ind.razao_ap as number)}</td></tr>
          <tr><th scope="row">Saldo pendular (empregos − ocupados)</th><td>{ind.saldo_pend != null ? num(ind.saldo_pend as number) : "—"}</td></tr>
        </>}
      </tbody></table>
      {nivel === "muni" && <EmpregoFormal codigo={codigo} />}
      <p className="nota">Modelo gravitacional duplamente restrito (Wilson) calibrado por edição; resultados dependem da agregação territorial (MAUP). Metodologia: docs/DECISOES.md.</p>
    </div>
  );
}

export function AbaFluxos({ nivel, ed, tipo, codigo, nomes }: { nivel: Nivel; ed: number; tipo: TipoFluxo; codigo: string; nomes: Map<string, string> }) {
  const [v, setV] = useState<Awaited<ReturnType<typeof vizinhos>>>([]);
  const set = useStore((s) => s.set);
  useEffect(() => { vizinhos(ed, nivel, tipo, codigo).then(setV); }, [ed, nivel, tipo, codigo]);
  const bloco = (sentido: "saem" | "chegam", titulo: string) => (
    <section><h4>{titulo}</h4>
      {v.filter((x) => x.sentido === sentido).length === 0 ? <p className="nota">nenhum par com amostra suficiente</p> : (
        <ul className="lista">{v.filter((x) => x.sentido === sentido).map((x) => (
          <li key={x.outro}><button onClick={() => set({ par: sentido === "saem" ? { o: codigo, d: x.outro } : { o: x.outro, d: codigo } })}>
            <span>{nomes.get(x.outro) ?? x.outro}</span><span>{num(x.total)} <Selo p={x.precisao} /></span></button></li>))}</ul>)}
    </section>
  );
  return <div className="aba">{bloco("saem", "Para onde vão")}{bloco("chegam", "De onde vêm")}</div>;
}

const MODOS_AOP: [string, string][] = [["tp", "Transporte público"], ["auto", "Automóvel"], ["ape", "A pé"]];
export function AbaAcessibilidade({ nivel, ed, codigo }: { nivel: Nivel; ed: number; codigo: string }) {
  const [d, setD] = useState<Linha[] | undefined>(undefined);
  useEffect(() => { setD(undefined); acessibilidadeUnidade(nivel, ed, codigo).then(setD); }, [nivel, ed, codigo]);
  if (d === undefined) return <p className="nota">carregando…</p>;
  if (d.length === 0) return <p className="nota">Sem acessibilidade calculada para esta unidade: o AOP/IPEA (2019) cobre só o município de São Paulo (transporte público, carro e a pé) e Guarulhos (carro e a pé), e exige ≥ 90% da população da unidade dentro da cobertura.{nivel === "zona" && ed !== 2023 ? " Para zonas, só o zoneamento de 2023." : ""}</p>;
  const v = (m: string, k: string) => d.find((x) => x.modo === m && x.medida === k)?.valor as number | undefined;
  const linhas: [string, string, (x: number) => string][] = [["cma30", "Empregos em 30 min", num], ["cma60", "Empregos em 60 min", num], ["cma90", "Empregos em 90 min", num], ["cma60_saude", "Equipamentos de saúde em 60 min", num1], ["tmi_saude", "Tempo ao equipamento de saúde mais próximo (min)", num1], ["tmi_escola", "Tempo à escola mais próxima (min)", num1]];
  return (
    <div className="aba">
      <table className="tabela"><thead><tr><th></th>{MODOS_AOP.map(([, r]) => <th key={r}>{r}</th>)}</tr></thead><tbody>
        {linhas.map(([k, r, f]) => <tr key={k}><th scope="row">{r}</th>{MODOS_AOP.map(([m]) => <td key={m}>{v(m, k) != null ? f(v(m, k)!) : "—"}</td>)}</tr>)}
      </tbody></table>
      <p className="nota">Projeto Acesso a Oportunidades (IPEA), 2019, pico da manhã; média ponderada pela população (Censo 2010) dos hexágonos da unidade. Tempos e acesso não são comparáveis com o modelo gravitacional (distância).</p>
    </div>
  );
}
