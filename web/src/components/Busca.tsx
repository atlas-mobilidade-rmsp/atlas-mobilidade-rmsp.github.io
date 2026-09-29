import { useMemo, useState } from "react";
import type { Unidade } from "../db/queries";

const norm = (s: string) => s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
export function Busca({ unidades, onEscolher, rotulo = "Buscar unidade" }: { unidades: Unidade[]; onEscolher: (c: string) => void; rotulo?: string }) {
  const [q, setQ] = useState("");
  const achados = useMemo(() => {
    const n = norm(q.trim()); if (n.length < 2) return [];
    return unidades.filter((u) => norm(u.nome).includes(n) || u.codigo === n).slice(0, 8);
  }, [q, unidades]);
  return (
    <div className="busca">
      <input type="search" placeholder={rotulo} aria-label={rotulo} value={q} onChange={(e) => setQ(e.target.value)} />
      {achados.length > 0 && (
        <ul role="listbox">{achados.map((u) => (
          <li key={u.codigo}><button onClick={() => { onEscolher(u.codigo); setQ(""); }}>{u.nome} <span className="cod">({u.codigo})</span></button></li>
        ))}</ul>
      )}
    </div>
  );
}
