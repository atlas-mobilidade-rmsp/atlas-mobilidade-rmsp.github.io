import { useEffect, useMemo, useRef, useState } from "react";
import DeckGL from "@deck.gl/react";
import { GeoJsonLayer, ScatterplotLayer, SolidPolygonLayer } from "@deck.gl/layers";
import { OrthographicView } from "@deck.gl/core";
import { feature } from "topojson-client";
import { poligonoFluxo } from "../lib/fluxos";
import { corDaClasse, quebrasDivergentes, quebrasQuantis, type RGB } from "../lib/cores";
import { METRICAS, valorMetrica } from "../lib/tipos";
import { topo, type Fluxo, type Indicadores, type Unidade } from "../db/queries";
import { useStore } from "../state/store";

const VIEW = new OrthographicView({ id: "mapa", flipY: false });
export const metrosPorPixel = (zoom: number) => 2 ** -zoom;
const larguraPx = (total: number, max: number) => 2 + 14 * Math.sqrt(total / Math.max(1, max));

export function useEscuro(): boolean {
  const [e, setE] = useState(() => matchMedia("(prefers-color-scheme: dark)").matches);
  useEffect(() => {
    const mq = matchMedia("(prefers-color-scheme: dark)"); const f = () => setE(mq.matches);
    mq.addEventListener("change", f); return () => mq.removeEventListener("change", f);
  }, []);
  const forcado = document.documentElement.getAttribute("data-theme");
  return forcado ? forcado === "dark" : e;
}

interface Props { unidades: Unidade[]; indic: Indicadores[]; fluxos: Fluxo[]; nomes: Map<string, string>; onHover: (t: string | null) => void }

function bbox(fc: any): [number, number, number, number] {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const visita = (c: any) => { if (typeof c[0] === "number") { x0 = Math.min(x0, c[0]); x1 = Math.max(x1, c[0]); y0 = Math.min(y0, c[1]); y1 = Math.max(y1, c[1]); } else c.forEach(visita); };
  fc.features.forEach((f: any) => visita(f.geometry.coordinates));
  return [x0, y0, x1, y1];
}

export function MapaAtlas({ unidades, indic, fluxos, nomes, onHover }: Props) {
  const { ed, nivel, metrica, unidade, par, fmin, baixa, trilhos, selecionarUnidade, selecionarPar } = useStore();
  const escuro = useEscuro();
  const [geoC, setGeoC] = useState<{ chave: string; fc: any } | null>(null);
  const geo = geoC && geoC.chave === `${nivel}:${nivel === "zona" ? ed : 0}` ? geoC.fc : null;
  const [tri, setTri] = useState<any>(null);
  const [est, setEst] = useState<any>(null);
  const [tam, setTam] = useState({ width: 0, height: 0 });
  const ref = useRef<HTMLDivElement>(null);
  const [vista, setVista] = useState<any>({ target: [345000, 7395000, 0], zoom: -7.5 });
  const nomeGeo = nivel === "zona" ? `zonas_${ed}` : nivel;

  useEffect(() => { let vivo = true; const chave = `${nivel}:${nivel === "zona" ? ed : 0}`; topo(nomeGeo).then((t) => { if (!vivo) return; setGeoC({ chave, fc: feature(t, t.objects[Object.keys(t.objects)[0]]) }); }); return () => { vivo = false; }; }, [nomeGeo]);
  useEffect(() => { topo("contexto_trilhos").then((t) => setTri(feature(t, t.objects[Object.keys(t.objects)[0]]))); topo("contexto_estacoes").then((t) => setEst(feature(t, t.objects[Object.keys(t.objects)[0]]))); }, []);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const ro = new ResizeObserver(() => setTam({ width: el.clientWidth, height: el.clientHeight })); ro.observe(el); return () => ro.disconnect();
  }, []);
  const areaFit = useRef(""), interagiu = useRef(false), tamFit = useRef("");
  useEffect(() => {
    if (!geo || !tam.width || !tam.height) return;
    // reenquadra ao trocar de nível (não de edição do mesmo nível, para preservar zoom/pan do usuário)
    const chave = nivel, t = `${tam.width}x${tam.height}`;
    const mudouNivel = areaFit.current !== chave;
    if (!mudouNivel && (interagiu.current || tamFit.current === t)) return;
    areaFit.current = chave; tamFit.current = t; if (mudouNivel) interagiu.current = false;
    const [x0, y0, x1, y1] = bbox(geo);
    const z = Math.log2(Math.min(tam.width / (x1 - x0), tam.height / (y1 - y0)) * 0.92);
    setVista({ target: [(x0 + x1) / 2, (y0 + y1) / 2, 0], zoom: z });
  }, [geo, nivel, tam.width, tam.height]);

  const m = METRICAS.find((x) => x.id === metrica)!;
  const { cores, quebras } = useMemo(() => {
    const val = new Map<string, number | null>();
    for (const r of indic) val.set(r.codigo, valorMetrica(metrica, r[metrica] as number | null));
    const arr = [...val.values()].filter((v): v is number => v != null);
    const q = m.divergente ? quebrasDivergentes(arr) : quebrasQuantis(arr, 5);
    const c = new Map<string, RGB>();
    for (const u of unidades) c.set(u.codigo, corDaClasse(val.get(u.codigo) ?? null, q, !!m.divergente, escuro));
    return { cores: c, quebras: q, val };
  }, [indic, unidades, metrica, escuro, m.divergente]);
  void quebras;

  const visiveis = useMemo(() => {
    const max = Math.max(1, ...fluxos.map((f) => f.total));
    return { max, lista: fluxos.filter((f) => f.total >= fmin * max && (baixa || f.precisao !== "baixa")) };
  }, [fluxos, fmin, baixa]);

  const mpp = metrosPorPixel(vista.zoom ?? -7);
  const tinta: RGB = escuro ? [235, 235, 230] : [20, 20, 20];
  const camadas = [
    geo && new GeoJsonLayer({
      id: "unidades", data: geo, pickable: true, stroked: true, filled: true, lineWidthUnits: "pixels", getLineWidth: 0.6,
      getLineColor: escuro ? [90, 90, 88, 255] : [255, 255, 255, 230],
      getFillColor: (f: any) => [...(cores.get(String(f.properties?.codigo ?? f.id)) ?? [200, 200, 200]), 235] as any,
      updateTriggers: { getFillColor: [cores] },
      onHover: (i: any) => { if (!i.object) return onHover(null); const c = String(i.object.properties?.codigo ?? i.object.id); onHover(nomes.get(c) ?? c); },
      onClick: (i: any) => i.object && selecionarUnidade(String(i.object.properties?.codigo ?? i.object.id)),
    }),
    unidade && geo && new GeoJsonLayer({
      id: "selecao", data: { type: "FeatureCollection", features: geo.features.filter((f: any) => String(f.properties?.codigo ?? f.id) === unidade) },
      stroked: true, filled: false, lineWidthUnits: "pixels", getLineWidth: 2.5, getLineColor: tinta as any,
    }),
    trilhos && tri && new GeoJsonLayer({ id: "trilhos", data: tri, stroked: false, filled: false, lineWidthUnits: "pixels", getLineWidth: 1.4,
      getLineColor: escuro ? [200, 200, 195, 150] : [40, 40, 40, 130] as any }),
    trilhos && est && new GeoJsonLayer({ id: "estacoes", data: est, pointType: "circle", pointRadiusUnits: "pixels", getPointRadius: 1.6,
      getFillColor: escuro ? [220, 220, 215, 170] : [40, 40, 40, 150] as any }),
    new SolidPolygonLayer<Fluxo>({
      id: "fluxos", data: visiveis.lista, pickable: true,
      getPolygon: (d) => poligonoFluxo(d.x_o, d.y_o, d.x_d, d.y_d, larguraPx(d.total, visiveis.max), mpp) ?? [],
      getFillColor: (d) => {
        const sel = par && par.o === d.origem && par.d === d.destino;
        if (sel) return [255, 190, 30, 255];
        const c = !unidade ? [42, 120, 214] : d.origem === unidade ? [235, 104, 52] : [42, 120, 214];
        return [...c, d.precisao === "baixa" ? 110 : 205] as any;
      },
      updateTriggers: { getPolygon: [mpp, visiveis], getFillColor: [par, unidade] },
      onHover: (i: any) => onHover(i.object ? `${nomes.get(i.object.origem) ?? i.object.origem} → ${nomes.get(i.object.destino) ?? i.object.destino}` : null),
      onClick: (i: any) => i.object && selecionarPar({ o: i.object.origem, d: i.object.destino }),
    }),
    new ScatterplotLayer<Fluxo>({ id: "nos", data: visiveis.lista, getPosition: (d) => [d.x_d, d.y_d], radiusUnits: "pixels", getRadius: 3.5,
      getFillColor: tinta as any, stroked: false }),
  ].filter(Boolean);

  return (
    <div ref={ref} className="mapa" role="img" aria-label="Mapa da região metropolitana com fluxos origem–destino">
      <DeckGL views={VIEW} viewState={vista} controller={{ scrollZoom: true, dragPan: true, doubleClickZoom: true }}
        onViewStateChange={({ viewState, interactionState }: any) => { if (interactionState?.isDragging || interactionState?.isZooming) interagiu.current = true; setVista({ ...viewState, zoom: Math.min(-3, Math.max(-11, viewState.zoom)) }); }}
        layers={camadas as any} getCursor={({ isHovering }: any) => (isHovering ? "pointer" : "grab")} />
    </div>
  );
}
