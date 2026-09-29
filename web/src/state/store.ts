import { create } from "zustand";
import type { Nivel, TipoFluxo } from "../lib/tipos";

export interface Estado {
  ed: number; nivel: Nivel; metrica: string; tipo: TipoFluxo;
  unidade: string | null; par: { o: string; d: string } | null;
  top: number; fmin: number; baixa: boolean; modo: "mapa" | "serie"; trilhos: boolean;
}
export interface Acoes {
  set: (p: Partial<Estado>) => void;
  selecionarUnidade: (u: string | null) => void;
  selecionarPar: (p: { o: string; d: string } | null) => void;
}
export const PADRAO: Estado = { ed: 2023, nivel: "amc146", metrica: "ind_mob", tipo: "todas", unidade: null, par: null, top: 40, fmin: 0, baixa: false, modo: "mapa", trilhos: true };
export const useStore = create<Estado & Acoes>((set) => ({
  ...PADRAO,
  set: (p) => set(p),
  selecionarUnidade: (unidade) => set({ unidade, par: null }),
  selecionarPar: (par) => set({ par }),
}));
