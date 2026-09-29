"""Repara feições inválidas (autointerseção pós-simplificação) nos *_s.json e reescreve-os.

Chamado por geo/build.sh entre o simplify e o TopoJSON final. Só geometria pública.
"""
import sys
from pathlib import Path

import geopandas as gpd
from shapely import make_valid
from shapely.geometry import MultiPolygon, Polygon


def poligonos(g):
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    partes = [p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")]
    flat = [q for p in partes for q in (p.geoms if p.geom_type == "MultiPolygon" else [p])]
    return MultiPolygon(flat) if len(flat) > 1 else (flat[0] if flat else Polygon())


def main(p: Path) -> None:
    g = gpd.read_file(p)
    bad = ~g.is_valid
    if bad.any():
        g.loc[bad, "geometry"] = g.loc[bad, "geometry"].apply(lambda x: poligonos(make_valid(x)))
        g.to_file(p, driver="GeoJSON")
    print(f"{p.name}: {int(bad.sum())} reparadas")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
