export const EDICOES = [1977, 1987, 1997, 2007, 2017, 2023] as const;
export type Edicao = (typeof EDICOES)[number];
export type Nivel = "zona" | "amc146" | "amc75" | "sub" | "muni";
export type TipoFluxo = "todas" | "trabalho" | "estudo" | "casa_trab";
export type Precisao = "boa" | "cautela" | "baixa" | "sem_estimativa";

export const NIVEIS: { id: Nivel; rotulo: string }[] = [
  { id: "amc146", rotulo: "AMC (146)" },
  { id: "amc75", rotulo: "AMC 1977–2023 (75)" },
  { id: "muni", rotulo: "Município" },
  { id: "sub", rotulo: "Subprefeitura / município" },
  { id: "zona", rotulo: "Zona OD" },
];
export const TIPOS: { id: TipoFluxo; rotulo: string }[] = [
  { id: "todas", rotulo: "Todas as viagens" },
  { id: "trabalho", rotulo: "Viagens ao trabalho" },
  { id: "estudo", rotulo: "Viagens ao estudo" },
  { id: "casa_trab", rotulo: "Casa–trabalho (pendular)" },
];

/** Um nível existe numa edição? (amc146 só 1987+, sub só 1997+; docs/DECISOES.md) */
export const nivelExiste = (n: Nivel, e: number) => !(n === "amc146" && e < 1987) && !(n === "sub" && e < 1997);

export interface Metrica { id: string; rotulo: string; unidade: string; casas: number; ajuda: string; divergente?: boolean }
export const METRICAS: Metrica[] = [
  { id: "ind_mob", rotulo: "Índice de mobilidade", unidade: "viagens/hab.", casas: 2, ajuda: "Viagens diárias por habitante." },
  { id: "imob_15m", rotulo: "Imobilidade (15+)", unidade: "%", casas: 0, ajuda: "Pessoas de 15 anos ou mais que não fizeram nenhuma viagem no dia." },
  { id: "tempo_med_trab", rotulo: "Tempo médio ao trabalho", unidade: "min", casas: 0, ajuda: "Duração média das viagens casa→trabalho dos residentes." },
  { id: "pct_coletivo_trab", rotulo: "Coletivo no trabalho", unidade: "%", casas: 0, ajuda: "Parcela das viagens ao trabalho feitas por transporte coletivo." },
  { id: "pct_ape_ate15", rotulo: "A pé até 15 min", unidade: "%", casas: 0, ajuda: "Parcela das viagens que são a pé e duram até 15 minutos (proximidade)." },
  { id: "autos_100hab", rotulo: "Automóveis por 100 hab.", unidade: "", casas: 0, ajuda: "Automóveis das famílias por 100 habitantes." },
  { id: "renda_fa_media_r2023", rotulo: "Renda familiar média", unidade: "R$ (2023)", casas: 0, ajuda: "Renda familiar mensal média, deflacionada para out/2023." },
  { id: "jobs_housing", rotulo: "Empregos / ocupados residentes", unidade: "", casas: 2, ajuda: "Razão emprego–moradia (empregos onde a pessoa trabalha ÷ ocupados que moram na unidade)." },
  { id: "ief", rotulo: "Índice de eficácia (atração−produção)", unidade: "", casas: 2, ajuda: "(atração − produção)/(atração + produção). Positivo = polo atrator.", divergente: true },
];
const pct = new Set(["imob_15m", "pct_coletivo_trab", "pct_ape_ate15"]);
export const valorMetrica = (id: string, v: number | null | undefined): number | null =>
  v == null || !Number.isFinite(v) ? null : pct.has(id) ? v * 100 : v;

export const ROTULO_PRECISAO: Record<Precisao, string> = {
  boa: "boa precisão", cautela: "usar com cautela", baixa: "baixa precisão", sem_estimativa: "sem estimativa",
};
export const ROTULO_STATUS: Record<string, string> = {
  publicado: "publicado", n_insuficiente: "amostra insuficiente", nao_existia: "não existia neste zoneamento",
  fora_area_1977: "fora da área de 1977",
};
