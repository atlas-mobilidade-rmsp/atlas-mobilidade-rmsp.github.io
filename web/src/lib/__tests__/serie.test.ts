import { describe, expect, it } from "vitest";
import { segmentos, nivelDaSerie, type PontoSerie } from "../serie";
import { nivelExiste, valorMetrica } from "../tipos";
import { quebrasQuantis, corDaClasse } from "../cores";

const p = (edicao: number, status: string, total: number | null): PontoSerie => ({
  edicao, status, total, n: 10, cv: 5, precisao: "boa", dur_mediana: null, pct_coletivo: null, ief_par: null, share_da_origem: null });

describe("série do par", () => {
  it("não interpola ausências: quebra o segmento", () => {
    const s = segmentos([p(1977, "publicado", 5), p(1987, "publicado", 6), p(1997, "n_insuficiente", null), p(2007, "publicado", 7), p(2017, "nao_existia", null), p(2023, "publicado", 9)], "total");
    expect(s.map((x) => x.map((y) => y.edicao))).toEqual([[1977, 1987], [2007], [2023]]);
  });
  it("sub não resolve na série", () => { expect(nivelDaSerie("sub", false)).toBeNull(); expect(nivelDaSerie("muni", false)).toBe("muni"); });
});
describe("níveis e cores", () => {
  it("existência por edição", () => {
    expect(nivelExiste("amc146", 1977)).toBe(false); expect(nivelExiste("sub", 1987)).toBe(false); expect(nivelExiste("zona", 1977)).toBe(true);
  });
  it("percentuais em pontos", () => { expect(valorMetrica("imob_15m", 0.4)).toBeCloseTo(40); expect(valorMetrica("ind_mob", 1.5)).toBe(1.5); expect(valorMetrica("ind_mob", null)).toBeNull(); });
  it("cor sem dado é neutra e quantis coerentes", () => {
    const q = quebrasQuantis([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5);
    expect(q.length).toBe(4);
    expect(corDaClasse(null, q, false, false)).not.toEqual(corDaClasse(10, q, false, false));
    expect(corDaClasse(1, q, false, false)).not.toEqual(corDaClasse(10, q, false, false));
  });
});
