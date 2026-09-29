import { consultar, lit, parquet } from "./duckdb";
import type { Nivel, TipoFluxo } from "../lib/tipos";
import type { PontoSerie } from "../lib/serie";

export interface Unidade { codigo: string; nome: string; muni_ibge: string | null; area_km2: number; amc_8723: string | null; amc_7723: string | null; x: number; y: number }
const edGeo = (n: Nivel, ed: number) => (n === "zona" ? ed : 0);

export async function unidades(ed: number, nivel: Nivel): Promise<Unidade[]> {
  const u = await parquet("geo/unidades_ref_geo.parquet"), c = await parquet("geo/centroides.parquet");
  return consultar<Unidade>(`select u.codigo, u.nome, u.muni_ibge, u.area_km2, u.amc_8723, u.amc_7723, c.x, c.y
    from ${u} u join ${c} c on c.nivel=u.nivel and c.edicao=u.edicao and c.codigo=u.codigo
    where u.nivel=${lit(nivel)} and u.edicao=${edGeo(nivel, ed)}`);
}
export type Indicadores = Record<string, number | string | null> & { codigo: string };
export async function indicadores(ed: number, nivel: Nivel): Promise<Indicadores[]> {
  const t = await parquet(`${ed}/indicadores.parquet`);
  return consultar<Indicadores>(`select * from ${t} where nivel=${lit(nivel)}`);
}
export interface Fluxo { origem: string; destino: string; total: number; n: number; cv: number | null; precisao: string;
  dur_mediana: number | null; pct_coletivo: number | null; pct_individual: number | null; pct_ativo: number | null; ief_par: number | null; dist_km: number; x_o: number; y_o: number; x_d: number; y_d: number }
export async function fluxos(ed: number, nivel: Nivel, tipo: TipoFluxo, unidade: string | null, top: number): Promise<Fluxo[]> {
  const f = await parquet(`${ed}/fluxos_${nivel}.parquet`), c = await parquet("geo/centroides.parquet");
  const eg = edGeo(nivel, ed);
  const filtro = unidade ? `and (f.origem=${lit(unidade)} or f.destino=${lit(unidade)}) and f.origem<>f.destino` : "and f.origem<>f.destino";
  return consultar<Fluxo>(`select f.origem, f.destino, f.total, f.n, f.cv, f.precisao, f.dur_mediana, f.pct_coletivo, f.pct_individual,
      f.pct_ativo, f.ief_par, f.dist_km, co.x x_o, co.y y_o, cd.x x_d, cd.y y_d
    from ${f} f join ${c} co on co.nivel=${lit(nivel)} and co.edicao=${eg} and co.codigo=f.origem
                join ${c} cd on cd.nivel=${lit(nivel)} and cd.edicao=${eg} and cd.codigo=f.destino
    where f.tipo=${lit(tipo)} ${filtro} order by f.total desc limit ${Math.max(1, Math.floor(top))}`);
}
export interface Cobertura { total_todos: number; total_publicado: number; pares_todos: number; pares_publicados: number }
export async function cobertura(ed: number, nivel: Nivel, tipo: TipoFluxo): Promise<Cobertura | null> {
  const t = await parquet(`${ed}/cobertura_fluxos.parquet`);
  return (await consultar<Cobertura>(`select * from ${t} where nivel=${lit(nivel)} and tipo=${lit(tipo)}`))[0] ?? null;
}
export interface Cat { dimensao: string; categoria: string; valor: number; n: number }
export async function perfilUnidade(ed: number, nivel: Nivel, codigo: string, papel = "residente"): Promise<Cat[]> {
  const t = await parquet(`${ed}/perfis.parquet`);
  return consultar<Cat>(`select dimensao, categoria, valor, n from ${t} where nivel=${lit(nivel)} and codigo=${lit(codigo)} and papel=${lit(papel)}`);
}
export async function perfilFluxo(ed: number, nivel: Nivel, tipo: TipoFluxo, o: string, d: string): Promise<Cat[]> {
  if (nivel === "zona") return [];
  const t = await parquet(`${ed}/fluxos_dim.parquet`);
  return consultar<Cat>(`select dimensao, categoria, valor, n from ${t} where nivel=${lit(nivel)} and tipo=${lit(tipo)} and origem=${lit(o)} and destino=${lit(d)}`);
}
export async function parSerie(nivel: "amc146" | "amc75" | "muni", tipo: TipoFluxo, o: string, d: string): Promise<PontoSerie[]> {
  const t = await parquet("serie/pares_serie.parquet");
  return consultar<PontoSerie>(`select edicao, status, total, n, cv, precisao, dur_mediana, pct_coletivo, ief_par, share_da_origem
    from ${t} where nivel=${lit(nivel)} and tipo=${lit(tipo)} and origem=${lit(o)} and destino=${lit(d)} order by edicao`);
}
export async function meta(): Promise<Record<string, any>> {
  return (await fetch(new URL("data/meta.json", document.baseURI))).json();
}
export async function topo(nome: string): Promise<any> {
  return (await fetch(new URL(`data/geo/${nome}.topojson`, document.baseURI))).json();
}
export async function umFluxo(ed: number, nivel: Nivel, tipo: TipoFluxo, o: string, d: string): Promise<Fluxo | null> {
  const f = await parquet(`${ed}/fluxos_${nivel}.parquet`), c = await parquet("geo/centroides.parquet"), eg = edGeo(nivel, ed);
  return (await consultar<Fluxo>(`select f.origem, f.destino, f.total, f.n, f.cv, f.precisao, f.dur_mediana, f.pct_coletivo, f.pct_individual,
      f.pct_ativo, f.ief_par, f.dist_km, co.x x_o, co.y y_o, cd.x x_d, cd.y y_d
    from ${f} f join ${c} co on co.nivel=${lit(nivel)} and co.edicao=${eg} and co.codigo=f.origem
                join ${c} cd on cd.nivel=${lit(nivel)} and cd.edicao=${eg} and cd.codigo=f.destino
    where f.tipo=${lit(tipo)} and f.origem=${lit(o)} and f.destino=${lit(d)}`))[0] ?? null;
}
