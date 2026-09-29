import type { Cat } from "../db/queries";
import { num } from "../lib/format";

const ROT: Record<string, string> = {
  masculino: "Masculino", feminino: "Feminino", nd: "Renda não informada", outros: "Outros (amostra pequena)", coletivo: "Coletivo", individual: "Individual motorizado",
  bicicleta: "Bicicleta", a_pe: "A pé", trabalho: "Trabalho", educacao: "Educação", compras: "Compras", saude: "Saúde", lazer: "Lazer", residencia: "Residência",
  fund_incompleto: "Fundamental incompleto", fund_completo: "Fundamental completo", medio: "Médio", superior: "Superior", agricola: "Agrícola",
  construcao: "Construção", industria: "Indústria", comercio: "Comércio", servicos: "Serviços",
};
const NOME_DIM: Record<string, string> = { sexo: "Sexo", idade: "Idade", renda_q: "Quintil de renda familiar per capita", escolaridade: "Escolaridade", setor: "Setor",
  modo: "Modo", motivo: "Motivo do destino", hora_saida: "Hora de saída", duracao_faixa: "Duração (min)" };
const rot = (c: string) => ROT[c] ?? (c.startsWith("q") && c.length === 2 ? `Q${c[1]}` : c);

export function BarrasDimensao({ dados, dimensao }: { dados: Cat[]; dimensao: string }) {
  const d = dados.filter((x) => x.dimensao === dimensao).sort((a, b) => a.categoria.localeCompare(b.categoria));
  const tot = d.reduce((s, x) => s + x.valor, 0);
  if (!d.length || tot <= 0) return null;
  return (
    <figure className="barras">
      <figcaption>{NOME_DIM[dimensao] ?? dimensao}</figcaption>
      {d.map((x) => (
        <div key={x.categoria} className="linha" title={`n amostral = ${num(x.n)}`}>
          <span className="cat">{rot(x.categoria)}</span>
          <span className="trilha"><span className="preench" style={{ width: `${(100 * x.valor) / tot}%` }} /></span>
          <span className="v">{((100 * x.valor) / tot).toFixed(0)}%</span>
        </div>
      ))}
    </figure>
  );
}
