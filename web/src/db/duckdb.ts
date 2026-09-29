/** DuckDB-WASM em worker; Parquet publicados registrados por URL sob demanda (range requests).
 *  Runtime servido de /duckdb (scripts/copy-duckdb.sh), same-origin. */
import * as duckdb from "@duckdb/duckdb-wasm";

let conexao: Promise<duckdb.AsyncDuckDBConnection> | null = null;
let db: duckdb.AsyncDuckDB | null = null;
const registrados = new Set<string>();

async function iniciar(): Promise<duckdb.AsyncDuckDBConnection> {
  const raiz = new URL("duckdb/", document.baseURI).href;
  const bundle = { mainModule: `${raiz}duckdb-eh.wasm`, mainWorker: `${raiz}duckdb-browser-eh.worker.js`, pthreadWorker: null };
  const worker = new Worker(bundle.mainWorker);
  db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(duckdb.LogLevel.WARNING), worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
  return db.connect();
}
export function conectar() {
  if (!conexao) conexao = iniciar().catch((e) => { conexao = null; throw e; });
  return conexao;
}
/** Registra data/<caminho> e devolve a expressão `read_parquet('<caminho>')` para usar em FROM. */
export async function parquet(caminho: string): Promise<string> {
  await conectar();
  if (!registrados.has(caminho)) {
    await db!.registerFileURL(caminho, new URL(`data/${caminho}`, document.baseURI).href, duckdb.DuckDBDataProtocol.HTTP, false);
    registrados.add(caminho);
  }
  return `read_parquet('${caminho}')`;
}
export async function consultar<T = Record<string, unknown>>(sql: string): Promise<T[]> {
  const con = await conectar();
  const res = await con.query(sql);
  return res.toArray().map((l) => {
    const o = l.toJSON() as Record<string, unknown>;
    for (const [k, v] of Object.entries(o)) if (typeof v === "bigint") o[k] = Number(v);
    return o as T;
  });
}
export const lit = (s: string) => `'${s.replace(/'/g, "''")}'`;
