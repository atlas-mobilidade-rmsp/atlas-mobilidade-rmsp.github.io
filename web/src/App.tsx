import { useEffect, useMemo, useState } from "react";
import { cobertura, fluxos as qFluxos, indicadores, umFluxo, unidades as qUnidades, type Cobertura, type Fluxo, type Indicadores, type Unidade } from "./db/queries";
import { Controles } from "./components/Controles";
import { Legenda } from "./components/Legenda";
import { Busca } from "./components/Busca";
import { PainelFluxo, PainelUnidade } from "./components/Paineis";
import { SerieDoPar } from "./components/SerieDoPar";
import { MapaAtlas } from "./map/MapaAtlas";
import { useStore, type Estado } from "./state/store";
import { lerUrl, montarQuery } from "./state/url";
import { nivelDaSerie } from "./lib/serie";
import { num, num1 } from "./lib/format";
import { NIVEIS } from "./lib/tipos";
import { ModoPesquisas } from "./components/ModoPesquisas";

export default function App() {
  const s = useStore();
  const [unid, setUnid] = useState<Unidade[]>([]);
  const [ind, setInd] = useState<Indicadores[]>([]);
  const [flx, setFlx] = useState<Fluxo[]>([]);
  const [par, setPar] = useState<Fluxo | null>(null);
  const [cob, setCob] = useState<Cobertura | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [dica, setDica] = useState<string | null>(null);
  const [pronto, setPronto] = useState(false);

  useEffect(() => { s.set(lerUrl(new URLSearchParams(location.search))); setPronto(true); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!pronto) return;
    const q = montarQuery(useStore.getState() as Estado);
    history.replaceState(null, "", q ? `?${q}` : location.pathname);
  }, [pronto, s.ed, s.nivel, s.metrica, s.tipo, s.unidade, s.par, s.top, s.fmin, s.baixa, s.modo, s.trilhos, s.us, s.ms, s.univ]);

  useEffect(() => {
    if (!pronto) return; let vivo = true; setErro(null);
    Promise.all([qUnidades(s.ed, s.nivel), indicadores(s.ed, s.nivel)]).then(([u, i]) => { if (vivo) { setUnid(u); setInd(i); } }).catch((e) => vivo && setErro(String(e.message ?? e)));
    return () => { vivo = false; };
  }, [pronto, s.ed, s.nivel]);
  useEffect(() => {
    if (!pronto) return; let vivo = true;
    qFluxos(s.ed, s.nivel, s.tipo, s.unidade, s.top).then((f) => vivo && setFlx(f)).catch((e) => vivo && setErro(String(e.message ?? e)));
    cobertura(s.ed, s.nivel, s.tipo).then((c) => vivo && setCob(c));
    return () => { vivo = false; };
  }, [pronto, s.ed, s.nivel, s.tipo, s.unidade, s.top]);
  useEffect(() => {
    if (!s.par) { setPar(null); return; } let vivo = true;
    const achado = flx.find((f) => f.origem === s.par!.o && f.destino === s.par!.d);
    if (achado) setPar(achado); else umFluxo(s.ed, s.nivel, s.tipo, s.par.o, s.par.d).then((f) => vivo && setPar(f));
    return () => { vivo = false; };
  }, [s.par, s.ed, s.nivel, s.tipo, flx]);

  const nomes = useMemo(() => new Map(unid.map((u) => [u.codigo, u.nome])), [unid]);
  const porCod = useMemo(() => new Map(unid.map((u) => [u.codigo, u])), [unid]);
  const indPor = useMemo(() => new Map(ind.map((r) => [r.codigo, r])), [ind]);
  const uSel = s.unidade ? porCod.get(s.unidade) : undefined;

  // par -> nível da série (zona resolve para AMC via unidades_ref; sub não resolve)
  const nivelSerie = useMemo(() => {
    if (!s.par) return null;
    const ns = nivelDaSerie(s.nivel, s.ed < 1987);
    if (s.nivel !== "zona") return ns ? { nivel: ns, o: s.par.o, d: s.par.d } : null;
    const uo = porCod.get(s.par.o), ud = porCod.get(s.par.d);
    if (!uo || !ud) return null;
    if (s.ed >= 1987 && uo.amc_8723 && ud.amc_8723) return { nivel: "amc146" as const, o: uo.amc_8723, d: ud.amc_8723 };
    if (uo.amc_7723 && ud.amc_7723) return { nivel: "amc75" as const, o: uo.amc_7723, d: ud.amc_7723 };
    return null;
  }, [s.par, s.nivel, s.ed, porCod]);

  if (erro) return <main className="erro" role="alert"><h1>Não foi possível carregar os dados</h1><p>{erro}</p><p>Rode <code>npm run sync-data</code> depois do gate do pipeline.</p></main>;

  const cabecalho = (
    <header className="topo">
      <h1>Atlas da Mobilidade na RMSP</h1>
      <p>Pesquisa Origem e Destino do Metrô-SP · 1977–2023</p>
      <nav className="modos" aria-label="Modo">
        <button className={s.modo === "mapa" ? "ativo" : ""} onClick={() => s.set({ modo: "mapa" })}>Mapa</button>
        <button className={s.modo === "serie" ? "ativo" : ""} onClick={() => s.set({ modo: "serie" })}>Um par ao longo das pesquisas</button>
        <button className={s.modo === "pesquisas" ? "ativo" : ""} onClick={() => s.set({ modo: "pesquisas" })}>Ao longo das pesquisas</button>
      </nav>
    </header>
  );

  if (s.modo === "serie") return <ModoSerie cabecalho={cabecalho} />;
  if (s.modo === "pesquisas") return <ModoPesquisas cabecalho={cabecalho} />;

  return (
    <div className="app">
      {cabecalho}
      <aside className="lateral esquerda">
        <Controles />
        <Busca unidades={unid} onEscolher={(c) => s.selecionarUnidade(c)} />
        <Legenda metrica={s.metrica} indic={ind} />
        {cob && <p className="nota">Cobertura publicada: {num1((100 * cob.total_publicado) / cob.total_todos)} % das viagens ({num(cob.pares_publicados)} de {num(cob.pares_todos)} pares com amostra suficiente).</p>}
      </aside>
      <main className="centro">
        {unid.length > 0 && <MapaAtlas unidades={unid} indic={ind} fluxos={flx} nomes={nomes} onHover={setDica} />}
        <div className="dica" aria-live="polite">{dica ?? `${NIVEIS.find((n) => n.id === s.nivel)?.rotulo} · ${s.ed} — clique numa unidade ou num fluxo`}</div>
      </main>
      <aside className="lateral direita">
        {par && <PainelFluxo f={par} nivel={s.nivel} ed={s.ed} tipo={s.tipo} nomes={nomes} nivelSerie={nivelSerie} />}
        {uSel && <PainelUnidade u={uSel} ind={indPor.get(uSel.codigo)} nivel={s.nivel} ed={s.ed} tipo={s.tipo} nomes={nomes} />}
        {!par && !uSel && <p className="nota">Selecione uma unidade no mapa para ver seus indicadores e os fluxos que entram e saem dela, ou um fluxo para ver o perfil e a série.</p>}
      </aside>
    </div>
  );
}

function ModoSerie({ cabecalho }: { cabecalho: React.ReactNode }) {
  const s = useStore();
  const nivel = s.nivel === "muni" ? "muni" : s.nivel === "amc75" ? "amc75" : "amc146";
  const [unid, setUnid] = useState<Unidade[]>([]);
  useEffect(() => { qUnidades(2023, nivel).then(setUnid); }, [nivel]);
  const nomes = useMemo(() => new Map(unid.map((u) => [u.codigo, u.nome])), [unid]);
  const o = s.par?.o ?? null, d = s.par?.d ?? null;
  return (
    <div className="app serie-modo">
      {cabecalho}
      <main className="pagina">
        <div className="controles">
          <label className="grupo"><span className="rot">Unidade</span>
            <select value={nivel} onChange={(e) => s.set({ nivel: e.target.value as any, par: null })}>
              <option value="amc146">AMC (146) — 1987–2023</option><option value="amc75">AMC (75) — 1977–2023</option><option value="muni">Município</option></select></label>
          <label className="grupo"><span className="rot">Fluxos</span>
            <select value={s.tipo} onChange={(e) => s.set({ tipo: e.target.value as any })}>
              <option value="todas">Todas as viagens</option><option value="trabalho">Trabalho</option><option value="estudo">Estudo</option><option value="casa_trab">Casa–trabalho</option></select></label>
        </div>
        <div className="duas">
          <div><Busca unidades={unid} rotulo="Origem" onEscolher={(c) => s.set({ par: { o: c, d: d ?? c } })} /><p>Origem: <b>{o ? nomes.get(o) ?? o : "—"}</b></p></div>
          <div><Busca unidades={unid} rotulo="Destino" onEscolher={(c) => s.set({ par: { o: o ?? c, d: c } })} /><p>Destino: <b>{d ? nomes.get(d) ?? d : "—"}</b></p></div>
        </div>
        {o && d && o !== d ? <SerieDoPar nivel={nivel} tipo={s.tipo} o={o} d={d} nomeO={nomes.get(o) ?? o} nomeD={nomes.get(d) ?? d} />
          : <p className="nota">Escolha uma origem e um destino diferentes para acompanhar o par em todas as pesquisas.</p>}
      </main>
    </div>
  );
}
