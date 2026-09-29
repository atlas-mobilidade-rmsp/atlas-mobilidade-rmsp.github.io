import type { Estado } from "../state/store";

export interface Pergunta {
  id: number; slug: string; titulo: string; pergunta: string; tema: "recorrente" | "emergente"; status: "respondida" | "parcial" | "aguarda_dados";
  literatura?: { autores: string; ano: number; titulo: string; onde?: string; doi?: string }[]; indicadores: string[];
  vista: { modo?: "mapa" | "serie" | "pesquisas"; ed?: number; nivel?: Estado["nivel"]; metrica?: string; tipo?: Estado["tipo"]; unidade?: string; origem?: string; destino?: string; top?: number; univ?: Estado["univ"]; ms?: string; us?: string };
  achado: { texto: string };
  comparabilidade?: string[]; dados?: string[]; pendencias?: string[];
}

/** Traduz a `vista` de uma pergunta em mudança de estado (deep-link do atlas). */
export function estadoDaVista(v: Pergunta["vista"]): Partial<Estado> {
  const e: Partial<Estado> = { modo: v.modo ?? "mapa", unidade: v.unidade ?? null, par: v.origem && v.destino ? { o: v.origem, d: v.destino } : null };
  if (v.ed) e.ed = v.ed;
  if (v.nivel) e.nivel = v.nivel;
  if (v.metrica) e.metrica = v.metrica;
  if (v.tipo) e.tipo = v.tipo;
  if (v.top) e.top = v.top;
  if (v.univ) e.univ = v.univ;
  if (v.ms) e.ms = v.ms;
  if (v.us) e.us = v.us;
  return e;
}
export const ROTULO_STATUS_PERGUNTA = { respondida: "respondida", parcial: "resposta parcial", aguarda_dados: "aguarda dados" } as const;
