import type { Nivel } from "./tipos";
export const POSICOES = [1977, 1987, 1997, 2007, 2017, 2023] as const;

export interface PontoSerie {
  edicao: number; status: string; total: number | null; n: number | null; cv: number | null; precisao: string | null;
  dur_mediana: number | null; pct_coletivo: number | null; ief_par: number | null; share_da_origem: number | null;
}
/** Segmentos contínuos (só edições consecutivas com valor); ausências quebram a linha — nunca se interpola. */
export function segmentos(pontos: PontoSerie[], campo: keyof PontoSerie): PontoSerie[][] {
  const segs: PontoSerie[][] = [];
  let atual: PontoSerie[] = [];
  for (const p of POSICOES.map((e) => pontos.find((x) => x.edicao === e))) {
    if (p && p.status === "publicado" && typeof p[campo] === "number") atual.push(p);
    else if (atual.length) { segs.push(atual); atual = []; }
  }
  if (atual.length) segs.push(atual);
  return segs;
}
/** Resolve o par selecionado (em qualquer nível) para o nível da série: zona→AMC via unidades_ref; sub não resolve. */
export function nivelDaSerie(n: Nivel, amc75: boolean): "amc146" | "amc75" | "muni" | null {
  if (n === "muni") return "muni";
  if (n === "sub") return null;
  return amc75 ? "amc75" : n === "amc75" ? "amc75" : "amc146";
}
