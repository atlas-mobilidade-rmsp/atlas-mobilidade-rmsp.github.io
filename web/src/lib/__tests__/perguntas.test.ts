import { describe, expect, it } from "vitest";
import { readFileSync, existsSync } from "node:fs";
import { estadoDaVista, type Pergunta } from "../perguntas";
import { METRICAS, NIVEIS, TIPOS, nivelExiste } from "../tipos";

const arq = new URL("../../../../data/processed/perguntas.json", import.meta.url);
describe.skipIf(!existsSync(arq))("perguntas.json", () => {
  const ps: Pergunta[] = JSON.parse(readFileSync(arq, "utf8"));
  it("toda vista resolve para um estado válido", () => {
    for (const p of ps) {
      const e = estadoDaVista(p.vista);
      expect(["mapa", "serie", "pesquisas"]).toContain(e.modo);
      if (e.nivel) expect(NIVEIS.map((n) => n.id)).toContain(e.nivel);
      if (e.tipo) expect(TIPOS.map((t) => t.id)).toContain(e.tipo);
      if (e.metrica) expect(METRICAS.map((m) => m.id)).toContain(e.metrica);
      if (e.nivel && e.ed) expect(nivelExiste(e.nivel, e.ed)).toBe(true);
    }
  });
  it("achados sem placeholders e com status válido", () => {
    for (const p of ps) { expect(p.achado.texto).not.toMatch(/[{}]/); expect(["respondida", "parcial", "aguarda_dados"]).toContain(p.status); }
  });
});
