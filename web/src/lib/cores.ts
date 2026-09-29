export type RGB = [number, number, number];
// Sequencial 5 classes (claro→escuro) e divergente 7 classes; valores validados em contraste contra o fundo do mapa.
const SEQ_CLARO: RGB[] = [[233, 240, 250], [186, 212, 243], [120, 170, 226], [52, 118, 199], [20, 70, 140]];
const SEQ_ESCURO: RGB[] = [[40, 52, 70], [50, 84, 130], [64, 120, 190], [110, 165, 235], [190, 218, 250]];
const DIV_CLARO: RGB[] = [[140, 40, 40], [224, 110, 104], [243, 173, 167], [240, 239, 236], [158, 197, 244], [85, 152, 231], [24, 79, 149]];
const DIV_ESCURO: RGB[] = [[180, 59, 58], [214, 88, 84], [251, 213, 209], [56, 56, 53], [205, 226, 251], [57, 135, 229], [37, 106, 191]];
export const SEM_DADO_CLARO: RGB = [225, 224, 217];
export const SEM_DADO_ESCURO: RGB = [48, 48, 46];

export function quebrasQuantis(valores: number[], k: number): number[] {
  const v = valores.filter((x) => Number.isFinite(x)).sort((a, b) => a - b);
  if (v.length < 2) return [];
  return Array.from({ length: k - 1 }, (_, i) => v[Math.min(v.length - 1, Math.floor(((i + 1) * v.length) / k))]);
}
/** Quebras simétricas em torno de zero para escalas divergentes (7 classes). */
export function quebrasDivergentes(valores: number[]): number[] {
  const m = Math.max(1e-9, ...valores.filter(Number.isFinite).map(Math.abs));
  const q = m * 0.75;
  return [-q * 0.66, -q * 0.33, -q * 0.1, q * 0.1, q * 0.33, q * 0.66].map((x) => x);
}
const classe = (v: number, quebras: number[]) => quebras.filter((q) => v >= q).length;
export function corDaClasse(v: number | null, quebras: number[], divergente: boolean, escuro: boolean): RGB {
  if (v == null) return escuro ? SEM_DADO_ESCURO : SEM_DADO_CLARO;
  const paleta = divergente ? (escuro ? DIV_ESCURO : DIV_CLARO) : escuro ? SEQ_ESCURO : SEQ_CLARO;
  return paleta[Math.min(paleta.length - 1, classe(v, quebras))];
}
export const paletaLegenda = (divergente: boolean, escuro: boolean) =>
  divergente ? (escuro ? DIV_ESCURO : DIV_CLARO) : escuro ? SEQ_ESCURO : SEQ_CLARO;
export const rgb = (c: RGB) => `rgb(${c[0]},${c[1]},${c[2]})`;
