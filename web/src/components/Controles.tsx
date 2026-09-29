import { EDICOES, METRICAS, NIVEIS, TIPOS, nivelExiste, type Nivel, type TipoFluxo } from "../lib/tipos";
import { useStore } from "../state/store";

export function Controles() {
  const s = useStore();
  const troca = (ed: number) => {
    const nivel: Nivel = nivelExiste(s.nivel, ed) ? s.nivel : s.nivel === "sub" ? "muni" : "amc75";
    s.set({ ed, nivel, par: null });
  };
  return (
    <section className="controles" aria-label="Controles do mapa">
      <div className="grupo" role="group" aria-label="Edição da pesquisa">
        <span className="rot">Pesquisa</span>
        <div className="seg">
          {EDICOES.map((e) => (
            <button key={e} className={s.ed === e ? "ativo" : ""} aria-pressed={s.ed === e} onClick={() => troca(e)}>{e}</button>
          ))}
        </div>
      </div>
      <label className="grupo"><span className="rot">Unidade territorial</span>
        <select value={s.nivel} onChange={(e) => s.set({ nivel: e.target.value as Nivel, unidade: null, par: null })}>
          {NIVEIS.filter((n) => nivelExiste(n.id, s.ed)).map((n) => <option key={n.id} value={n.id}>{n.rotulo}</option>)}
        </select></label>
      <label className="grupo"><span className="rot">Cor do mapa</span>
        <select value={s.metrica} onChange={(e) => s.set({ metrica: e.target.value })}>
          {METRICAS.map((m) => <option key={m.id} value={m.id}>{m.rotulo}</option>)}
        </select></label>
      <label className="grupo"><span className="rot">Fluxos</span>
        <select value={s.tipo} onChange={(e) => s.set({ tipo: e.target.value as TipoFluxo, par: null })}>
          {TIPOS.map((t) => <option key={t.id} value={t.id}>{t.rotulo}</option>)}
        </select></label>
      <label className="grupo"><span className="rot">Maiores fluxos: {s.top}</span>
        <input type="range" min={5} max={200} step={5} value={s.top} onChange={(e) => s.set({ top: Number(e.target.value) })} /></label>
      <label className="grupo"><span className="rot">Volume mínimo: {Math.round(s.fmin * 100)}% do maior</span>
        <input type="range" min={0} max={0.8} step={0.05} value={s.fmin} onChange={(e) => s.set({ fmin: Number(e.target.value) })} /></label>
      <label className="check"><input type="checkbox" checked={s.baixa} onChange={(e) => s.set({ baixa: e.target.checked })} /> mostrar fluxos de baixa precisão</label>
      <label className="check"><input type="checkbox" checked={s.trilhos} onChange={(e) => s.set({ trilhos: e.target.checked })} /> trilhos (metrô e trem)</label>
    </section>
  );
}
