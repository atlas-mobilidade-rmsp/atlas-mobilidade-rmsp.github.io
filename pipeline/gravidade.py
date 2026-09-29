"""F4 — modelo gravitacional duplamente restrito (Wilson), potencial de Hansen e excesso de deslocamento.

Sobre a matriz casa–trabalho COMPLETA (sem piso de n; é insumo de modelo, não publicação) por edição e nível.
T_ij = A_i O_i B_j D_j f(c_ij); f = exp(-beta c) ou c^-gamma; beta/gamma calibrados por bissecção até
MTL_modelo = MTL_obs (Hyman 1969). Impedâncias: distância entre centroides (km) e tempo observado (min; pares
n < 5 imputados por regressão log t ~ log d). Excesso (Hamilton 1982; White 1988; Horner 2002) por programação linear.
MAUP: os resultados dependem da agregação; comparar níveis só com essa ressalva (docs/METODOLOGIA).
"""
import json

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, vstack

from pipeline.base import GEO, conectar, niveis_da_edicao, preparar
from pipeline.edicoes import ANOS
from pipeline.fontes import PROCESSED

NIVEIS_GRAV = ("amc146", "amc75", "muni", "sub")
FAIXAS_KM = [0, 5, 10, 20, 40, 80, 1e9]
FAIXAS_MIN = [0, 15, 30, 45, 60, 90, 1e9]


def _unidades(ano: int, nivel: str) -> pd.DataFrame:
    u = pd.read_parquet(GEO / "unidades_ref_geo.parquet")
    u = u[(u.nivel == nivel) & (u.edicao == 0)]
    c = pd.read_parquet(GEO / "centroides.parquet")
    c = c[(c.nivel == nivel) & (c.edicao == 0)]
    return u.merge(c[["codigo", "x", "y"]], on="codigo").sort_values("codigo").reset_index(drop=True)


def matriz(con, ano: int, nivel: str, unid: pd.DataFrame, excluir: bool = True):
    """T (ocupados com local fixo de trabalho, casa->trabalho) e tempo médio observado (min, ponderado) por par.

    Exclui `trab_re` 1 (trabalha em casa) e 3 (sem endereço fixo): sem isso viram pseudo-viagens intra-zonais (auditoria F4:
    ~14 % dos ocupados em 2007 → ~24 % em 2023). 1977–1997 não têm o atributo (2–3 % sem zona) — limitação de comparabilidade P6."""
    idx = {c: i for i, c in enumerate(unid.codigo)}
    n = len(idx)
    df = con.execute(f"""select u_home_{nivel} o, u_trab_{nivel} d, sum(fe_pess) t, count(*) k from pessoa
        where ano={ano} and cond_ativ=1 and {'coalesce(trab_re,2)=2 and' if excluir else ''} u_home_{nivel} is not null and u_trab_{nivel} is not null group by 1,2""").df()
    df = df[df.o.isin(idx) & df.d.isin(idx)]
    T = np.zeros((n, n)); K = np.zeros((n, n))
    T[df.o.map(idx), df.d.map(idx)] = df.t; K[df.o.map(idx), df.d.map(idx)] = df.k
    tv = con.execute(f"""select u_o_{nivel} o, u_d_{nivel} d, sum(fe_via*duracao)/sum(fe_via) tmin, count(*) k from viagem
        where ano={ano} and motivo_o=8 and motivo_d in (1,2,3) and duracao>0 and u_o_{nivel} is not null and u_d_{nivel} is not null group by 1,2""").df()
    tv = tv[tv.o.isin(idx) & tv.d.isin(idx)]
    TM = np.full((n, n), np.nan); KT = np.zeros((n, n))
    TM[tv.o.map(idx), tv.d.map(idx)] = tv.tmin; KT[tv.o.map(idx), tv.d.map(idx)] = tv.k
    return T, K, TM, KT


INTRA_FATOR = 2 / 3      # c_ii = INTRA_FATOR·sqrt(area/π); sensibilidade em 0,5 e 1,0 (auditoria F4)


def custo_dist(unid: pd.DataFrame, fator: float = INTRA_FATOR) -> np.ndarray:
    x, y = unid.x.values, unid.y.values
    c = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :]) / 1000.0
    np.fill_diagonal(c, fator * np.sqrt(unid.area_km2.values / np.pi))     # intra-unidade
    return np.maximum(c, 0.05)


def custo_tempo(cd: np.ndarray, TM: np.ndarray, KT: np.ndarray, T: np.ndarray) -> tuple[np.ndarray, dict]:
    obs = (KT >= 5) & np.isfinite(TM) & (TM > 0)
    x, y, w = np.log(cd[obs]), np.log(TM[obs]), T[obs] + 1
    b = np.polyfit(x, y, 1, w=np.sqrt(w)) if obs.sum() > 5 else np.array([0.5, 2.5])
    ct = np.exp(np.polyval(b, np.log(cd)))
    ct[obs] = TM[obs]
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2) if obs.sum() > 5 else float("nan")
    return np.maximum(ct, 1.0), {"pares_obs": int(obs.sum()), "reg_b": float(b[0]), "reg_a": float(b[1]), "r2_reg": r2}


def furness(f: np.ndarray, O: np.ndarray, D: np.ndarray, it: int = 300, tol: float = 1e-7) -> np.ndarray:
    a, b = np.ones_like(O), np.ones_like(D)
    for _ in range(it):
        a = O / np.maximum(f @ b, 1e-300)
        b_new = D / np.maximum(f.T @ a, 1e-300)
        if np.max(np.abs(b_new - b) / np.maximum(b, 1e-300)) < tol:
            b = b_new; break
        b = b_new
    else:
        import warnings
        warnings.warn("Furness não convergiu em %d iterações" % it)
    return a[:, None] * b[None, :] * f


def mtl(T, c): return float((T * c).sum() / T.sum())


def calibrar(c: np.ndarray, O, D, alvo: float, forma: str) -> tuple[float, np.ndarray]:
    fn = (lambda p: np.exp(-p * c)) if forma == "exp" else (lambda p: c ** (-p))
    lo, hi = (1e-4, 3.0) if forma == "exp" else (0.05, 6.0)
    for _ in range(45):
        mid = 0.5 * (lo + hi)
        m = mtl(furness(fn(mid), O, D), c)
        lo, hi = (mid, hi) if m > alvo else (lo, mid)       # MTL decresce com o parâmetro
    p = 0.5 * (lo + hi)
    return p, furness(fn(p), O, D)


def extremos(c: np.ndarray, O: np.ndarray, D: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Problema de transporte: T_min (min sum c T) e T_max (max), mesmas margens O e D."""
    n = len(O)
    A_row = csr_matrix((np.ones(n * n), (np.repeat(np.arange(n), n), np.arange(n * n))), shape=(n, n * n))
    A_col = csr_matrix((np.ones(n * n), (np.tile(np.arange(n), n), np.arange(n * n))), shape=(n, n * n))
    A = vstack([A_row, A_col]).tocsr()
    b = np.concatenate([O, D])
    out = []
    for sinal in (1, -1):
        r = linprog(sinal * c.ravel(), A_eq=A[:-1], b_eq=b[:-1], bounds=(0, None), method="highs")   # última restrição redundante
        out.append(r.x.reshape(n, n) if r.success else np.full((n, n), np.nan))
    return out[0], out[1]


def ajuste(T: np.ndarray, M: np.ndarray, c: np.ndarray, faixas_cortes=FAIXAS_KM, unidade="km") -> dict:
    ok = (T > 0) & (M > 0)
    r2 = float(np.corrcoef(np.log(T[ok]), np.log(M[ok]))[0, 1] ** 2) if ok.sum() > 3 else float("nan")
    faixas = []
    for a, b in zip(faixas_cortes[:-1], faixas_cortes[1:]):
        m = (c >= a) & (c < b)
        faixas.append({f"de_{unidade}": a, f"ate_{unidade}": min(b, 999), "obs": float(T[m].sum() / T.sum()), "modelo": float(M[m].sum() / M.sum())})
    return {"r2_log": r2, "faixas": faixas}


def um_nivel(con, ano: int, nivel: str):
    unid = _unidades(ano, nivel)
    T, K, TM, KT = matriz(con, ano, nivel, unid)
    ativo = (T.sum(1) > 0) | (T.sum(0) > 0)
    if ativo.sum() < 5:
        return None, None
    unid = unid[ativo].reset_index(drop=True)
    T, K, TM, KT = (m[np.ix_(ativo, ativo)] for m in (T, K, TM, KT))
    O, D = T.sum(1), T.sum(0)
    cd = custo_dist(unid)
    ct, reg = custo_tempo(cd, TM, KT, T)
    pop = con.execute(f"select u_home_{nivel} c, sum(fe_pess) p from pessoa where ano={ano} group by 1").df().set_index("c").p
    P = unid.codigo.map(pop).fillna(0).values
    params, tab = {}, {"nivel": nivel, "codigo": unid.codigo.values}
    for imp, c in (("dist_km", cd), ("tempo_min", ct)):
        alvo = mtl(T, c)
        res = {"mtl_obs": alvo}
        for forma in ("exp", "pow"):
            p, M = calibrar(c, O, D, alvo, forma)
            f = np.exp(-p * c) if forma == "exp" else c ** (-p)
            res[forma] = {"parametro": p, "mtl_modelo": mtl(M, c), **ajuste(T, M, c, *((FAIXAS_KM, "km") if imp == "dist_km" else (FAIXAS_MIN, "min")))}
            tab[f"hansen_emp_{forma}_{imp}"] = f @ D
            tab[f"hansen_pop_{forma}_{imp}"] = f @ P
        if nivel != "sub" or True:
            Tmin, Tmax = extremos(c, O, D) if len(O) <= 160 else (None, None)
            if Tmin is not None and np.isfinite(Tmin).all():
                t_min, t_max = mtl(Tmin, c), mtl(Tmax, c)
                res.update({"t_min": t_min, "t_max": t_max, "excesso": (alvo - t_min) / alvo,
                            "utilizacao_capacidade": (alvo - t_min) / (t_max - t_min)})
                tab[f"t_medio_min_{imp}"] = (Tmin * c).sum(1) / np.maximum(O, 1e-9)
            tab[f"t_medio_obs_{imp}"] = (T * c).sum(1) / np.maximum(O, 1e-9)
        if imp == "dist_km" and nivel.startswith("amc"):
            res["sensibilidade_intra"] = {}
            for fator in (0.5, 1.0):
                c2 = custo_dist(unid, fator); a2 = mtl(T, c2)
                tmin2, _ = extremos(c2, O, D)
                b2, _ = calibrar(c2, O, D, a2, "exp")
                res["sensibilidade_intra"][str(fator)] = {"mtl_obs": a2, "t_min": mtl(tmin2, c2), "excesso": (a2 - mtl(tmin2, c2)) / a2, "beta": b2}
        params[imp] = res
    tab["autocont"] = np.diag(T) / np.maximum(O, 1e-9)
    tab["jobs_housing_od"] = D / np.maximum(O, 1e-9)
    tab["empregos_od"], tab["ocupados_od"] = D, O
    if nivel == "amc75":
        # variante comparável com 1977–1997 (que não têm `trab_re`): inclui trabalho em casa/sem local fixo (pseudo-diagonal)
        T2, *_ = matriz(con, ano, nivel, _unidades(ano, nivel), excluir=False)
        T2 = T2[np.ix_(ativo, ativo)]
        O2, D2 = T2.sum(1), T2.sum(0)
        a2 = mtl(T2, cd)
        b2, _ = calibrar(cd, O2, D2, a2, "exp")
        tmin2, _ = extremos(cd, O2, D2)
        params["dist_km"]["incl_domicilio"] = {"mtl_obs": a2, "beta": b2, "t_min": mtl(tmin2, cd), "excesso": (a2 - mtl(tmin2, cd)) / a2, "autocont_sistema": float(np.trace(T2) / T2.sum())}
        params["dist_km"]["autocont_sistema"] = float(np.trace(T) / T.sum())
    params["n_unidades"], params["n_pares_obs"], params["regressao_tempo"] = int(len(O)), int((K > 0).sum()), reg
    return pd.DataFrame(tab), params


def rodar(anos=ANOS) -> None:
    con = conectar(); preparar(con)
    todos = {}
    for ano in anos:
        tabs, params = [], {}
        for nivel in NIVEIS_GRAV:
            if nivel not in niveis_da_edicao(ano, NIVEIS_GRAV):
                continue
            t, p = um_nivel(con, ano, nivel)
            if t is not None:
                tabs.append(t); params[nivel] = p
        pd.concat(tabs, ignore_index=True).to_parquet(PROCESSED / str(ano) / "gravitacional.parquet", index=False)
        todos[str(ano)] = params
        print(ano, {n: round(p["dist_km"]["exp"]["parametro"], 3) for n, p in params.items()})
    (PROCESSED / "serie").mkdir(exist_ok=True)
    (PROCESSED / "serie" / "gravitacional_params.json").write_text(json.dumps(
        {"aviso": "MAUP: resultados dependem da agregação territorial; comparar entre níveis com cautela.", "edicoes": todos},
        indent=1, ensure_ascii=False))


if __name__ == "__main__":
    rodar()
