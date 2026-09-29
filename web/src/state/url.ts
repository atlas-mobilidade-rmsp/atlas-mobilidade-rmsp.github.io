import { EDICOES, NIVEIS, TIPOS, type Nivel, type TipoFluxo } from "../lib/tipos";
import { PADRAO, type Estado } from "./store";

/** Estado <-> query string: ed, n, m, t, u, o, d, top, fmin, baixa, modo, tri (só o que difere do padrão). */
export function lerUrl(p: URLSearchParams): Partial<Estado> {
  const e: Partial<Estado> = {};
  const ed = Number(p.get("ed")); if ((EDICOES as readonly number[]).includes(ed)) e.ed = ed;
  const n = p.get("n") as Nivel | null; if (n && NIVEIS.some((x) => x.id === n)) e.nivel = n;
  const t = p.get("t") as TipoFluxo | null; if (t && TIPOS.some((x) => x.id === t)) e.tipo = t;
  if (p.get("m")) e.metrica = p.get("m")!;
  if (p.get("u")) e.unidade = p.get("u");
  if (p.get("o") && p.get("d")) e.par = { o: p.get("o")!, d: p.get("d")! };
  const top = Number(p.get("top")); if (top >= 1 && top <= 500) e.top = Math.floor(top);
  const fmin = Number(p.get("fmin")); if (p.get("fmin") && fmin >= 0 && fmin <= 1) e.fmin = fmin;
  if (p.get("baixa") === "1") e.baixa = true;
  const md = p.get("modo"); if (md === "serie" || md === "pesquisas" || md === "perguntas") e.modo = md;
  if (p.get("us")?.includes(":")) e.us = p.get("us");
  if (p.get("ms")) e.ms = p.get("ms")!;
  if (p.get("univ") === "area1977") e.univ = "area1977";
  if (p.get("tri") === "0") e.trilhos = false;
  return e;
}
export function montarQuery(e: Estado): string {
  const p = new URLSearchParams();
  if (e.ed !== PADRAO.ed) p.set("ed", String(e.ed));
  if (e.nivel !== PADRAO.nivel) p.set("n", e.nivel);
  if (e.metrica !== PADRAO.metrica) p.set("m", e.metrica);
  if (e.tipo !== PADRAO.tipo) p.set("t", e.tipo);
  if (e.unidade) p.set("u", e.unidade);
  if (e.par) { p.set("o", e.par.o); p.set("d", e.par.d); }
  if (e.top !== PADRAO.top) p.set("top", String(e.top));
  if (e.fmin > 0) p.set("fmin", String(e.fmin));
  if (e.baixa) p.set("baixa", "1");
  if (e.modo !== "mapa") p.set("modo", e.modo);
  if (e.us) p.set("us", e.us);
  if (e.ms !== PADRAO.ms) p.set("ms", e.ms);
  if (e.univ !== PADRAO.univ) p.set("univ", e.univ);
  if (!e.trilhos) p.set("tri", "0");
  return p.toString();
}
