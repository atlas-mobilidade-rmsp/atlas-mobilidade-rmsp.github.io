import { describe, expect, it } from "vitest";
import { lerUrl, montarQuery } from "../url";
import { PADRAO } from "../store";

describe("URL", () => {
  it("padrão gera query vazia", () => expect(montarQuery(PADRAO)).toBe(""));
  it("ida e volta, incluindo o/d no modo série", () => {
    const e = { ...PADRAO, ed: 2007 as const, nivel: "muni" as const, tipo: "casa_trab" as const, par: { o: "3550308", d: "3518800" }, modo: "serie" as const, baixa: true, fmin: 0.25, top: 80 };
    const volta = { ...PADRAO, ...lerUrl(new URLSearchParams(montarQuery(e))) };
    expect(volta).toEqual(e);
  });
  it("ignora valores inválidos", () => {
    const r = lerUrl(new URLSearchParams("ed=1999&n=xx&t=foo&top=99999&fmin=3"));
    expect(r).toEqual({});
  });
});
