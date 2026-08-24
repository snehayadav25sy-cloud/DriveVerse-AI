/**
 * RoadMapCanvas.tsx — deck.gl road network visualisation
 *
 * Renders the GeoJSON road graph as interactive deck.gl layers overlaid on a
 * MapLibre GL tile basemap (dark-matter from CARTO, no API key required).
 *
 * Architecture: DeckGL (overlaid) + raw maplibre-gl Map instance synced via
 * onViewStateChange. This avoids react-map-gl and @deck.gl/mapbox dependencies.
 *
 * Layers:
 *   - GeoJsonLayer (LineString): road edges, coloured by road_type
 *   - GeoJsonLayer (Point):      graph nodes, coloured by node_type
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import DeckGL from '@deck.gl/react'
import { GeoJsonLayer } from '@deck.gl/layers'
import type { PickingInfo, ViewStateChangeParameters } from '@deck.gl/core'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Activity, GitBranch, Clock } from 'lucide-react'

// ── Colour palettes ──────────────────────────────────────────────────────────
const ROAD_COLOURS: Record<string, [number, number, number, number]> = {
  motorway:     [162,  89, 255, 230],
  trunk:        [126,  87, 255, 220],
  primary:      [ 56, 189, 248, 220],
  secondary:    [ 20, 184, 166, 210],
  tertiary:     [ 99, 179, 161, 200],
  residential:  [ 71,  85, 105, 200],
  service:      [ 51,  65,  85, 170],
  unclassified: [ 71,  85, 105, 160],
  path:         [148, 163, 184, 130],
  cycleway:     [ 74, 222, 128, 180],
}
const DEFAULT_EDGE: [number, number, number, number] = [100, 116, 139, 180]

const NODE_COLOURS: Record<string, [number, number, number, number]> = {
  intersection: [251, 191,  36, 255],
  dead_end:     [248, 113, 113, 255],
  merge:        [167, 243, 208, 230],
  split:        [147, 197, 253, 230],
  endpoint:     [ 71,  85, 105, 180],
}
const DEFAULT_NODE: [number, number, number, number] = [100, 116, 139, 200]

// ── Types ────────────────────────────────────────────────────────────────────
interface GeoJSONFeature {
  type: 'Feature'
  geometry: { type: string; coordinates: unknown }
  properties: Record<string, unknown>
}

interface RoadMapCanvasProps {
  geojson: { type: string; features: GeoJSONFeature[] }
  centerLat: number
  centerLon: number
  nodeCount: number
  edgeCount: number
  elapsedMs: number
  loading?: boolean
}

// Typed viewState used throughout
type DeckViewState = {
  latitude: number
  longitude: number
  zoom: number
  pitch?: number
  bearing?: number
}

const BASEMAP_STYLE =
  'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

// ── Component ────────────────────────────────────────────────────────────────
export default function RoadMapCanvas({
  geojson,
  centerLat,
  centerLon,
  nodeCount,
  edgeCount,
  elapsedMs,
  loading = false,
}: RoadMapCanvasProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)

  const [viewState, setViewState] = useState<DeckViewState>({
    latitude: centerLat,
    longitude: centerLon,
    zoom: 15,
    pitch: 30,
    bearing: 0,
  })

  const [tooltip, setTooltip] = useState<{
    x: number; y: number; content: string
  } | null>(null)

  // ── Boot maplibre-gl once ─────────────────────────────────────────────────
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: BASEMAP_STYLE,
      center: [centerLon, centerLat],
      zoom: 15,
      pitch: 30,
      interactive: false, // deck.gl drives camera
      attributionControl: false,
    })
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── Sync maplibre camera when deck.gl viewState changes ──────────────────
  const onViewStateChange = useCallback(
    ({ viewState: vs }: ViewStateChangeParameters) => {
      const mvs = vs as DeckViewState
      setViewState(mvs)
      mapRef.current?.jumpTo({
        center: [mvs.longitude, mvs.latitude],
        zoom: mvs.zoom,
        pitch: mvs.pitch ?? 0,
        bearing: mvs.bearing ?? 0,
      })
    },
    [],
  )

  // ── Re-center when location changes ──────────────────────────────────────
  useEffect(() => {
    const next: DeckViewState = {
      latitude: centerLat,
      longitude: centerLon,
      zoom: 15,
      pitch: 30,
      bearing: 0,
    }
    setViewState(next)
    mapRef.current?.jumpTo({
      center: [centerLon, centerLat],
      zoom: 15,
      pitch: 30,
    })
  }, [centerLat, centerLon])

  // ── Hover tooltip ────────────────────────────────────────────────────────
  const onHover = useCallback((info: PickingInfo) => {
    if (!info.object) { setTooltip(null); return }
    const props = (info.object as GeoJSONFeature).properties
    if (props.feature_type === 'edge') {
      const name = props.name ? String(props.name) : String(props.road_type)
      setTooltip({
        x: info.x, y: info.y,
        content: [
          name,
          `Type: ${String(props.road_type)}`,
          `Lanes: ${String(props.lanes)}`,
          `Length: ${String(props.length_m)} m`,
          props.one_way ? '⟶ one-way' : '⇄ two-way',
        ].join('\n'),
      })
    } else if (props.feature_type === 'node') {
      setTooltip({ x: info.x, y: info.y, content: `Node: ${String(props.node_type)}` })
    }
  }, [])

  // ── Split features by type ────────────────────────────────────────────────
  const edgeFeatures = geojson.features.filter(f => f.properties.feature_type === 'edge')
  const nodeFeatures = geojson.features.filter(f => f.properties.feature_type === 'node')

  // ── deck.gl layers ────────────────────────────────────────────────────────
  const layers = [
    new GeoJsonLayer<Record<string, unknown>>({
      id: 'road-edges',
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: { type: 'FeatureCollection', features: edgeFeatures } as any,
      pickable: true,
      stroked: false,
      filled: false,
      lineWidthMinPixels: 1.5,
      getLineWidth: (f: { properties: Record<string, unknown> }) => {
        const rt = String(f.properties?.road_type ?? '')
        if (['motorway', 'trunk'].includes(rt)) return 8
        if (rt === 'primary') return 6
        if (['secondary', 'tertiary'].includes(rt)) return 4
        return 2
      },
      getLineColor: (f: { properties: Record<string, unknown> }): [number, number, number, number] => {
        const rt = String(f.properties?.road_type ?? '')
        return ROAD_COLOURS[rt] ?? DEFAULT_EDGE
      },
      onHover,
      updateTriggers: { getLineColor: [geojson], getLineWidth: [geojson] },
    }),
    new GeoJsonLayer<Record<string, unknown>>({
      id: 'road-nodes',
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: { type: 'FeatureCollection', features: nodeFeatures } as any,
      pickable: true,
      stroked: true,
      filled: true,
      pointRadiusMinPixels: 3,
      pointRadiusMaxPixels: 10,
      getPointRadius: (f: { properties: Record<string, unknown> }) => {
        const nt = String(f.properties?.node_type ?? '')
        if (nt === 'intersection') return 6
        if (nt === 'dead_end') return 5
        return 3
      },
      getFillColor: (f: { properties: Record<string, unknown> }): [number, number, number, number] => {
        const nt = String(f.properties?.node_type ?? '')
        return NODE_COLOURS[nt] ?? DEFAULT_NODE
      },
      getLineColor: [15, 23, 42, 200] as [number, number, number, number],
      getLineWidth: 1,
      onHover,
      updateTriggers: { getFillColor: [geojson], getPointRadius: [geojson] },
    }),
  ]

  return (
    <div className="w-full rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 flex flex-col shadow-2xl">
      {/* Header */}
      <div className="flex items-center gap-4 px-5 py-3 border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-600/20 to-violet-600/20 border border-brand-500/20">
          <Activity size={15} className="text-brand-400" />
        </div>
        <span className="text-sm font-semibold text-white">Road Network Preview</span>
        <div className="ml-auto flex items-center gap-5 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <GitBranch size={12} className="text-sky-400" />
            <span className="font-mono text-slate-200">{edgeCount}</span> edges
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span className="font-mono text-slate-200">{nodeCount}</span> nodes
          </span>
          <span className="flex items-center gap-1.5">
            <Clock size={11} className="text-slate-500" />
            <span className="font-mono text-slate-400">{elapsedMs} ms</span>
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-2 border-b border-slate-800/60 bg-slate-900/40">
        {[
          { label: 'Motorway', cls: 'bg-violet-400' },
          { label: 'Primary',  cls: 'bg-sky-400'    },
          { label: 'Secondary', cls: 'bg-teal-400'  },
          { label: 'Residential', cls: 'bg-slate-500' },
        ].map(({ label, cls }) => (
          <span key={label} className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <span className={`w-5 h-0.5 rounded-full ${cls}`} /> {label}
          </span>
        ))}
        <span className="ml-auto flex items-center gap-3 text-[11px] text-slate-500">
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-400" />Intersection</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-400" />Dead end</span>
        </span>
      </div>

      {/* Map canvas */}
      <div className="relative" style={{ height: 480 }}>
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
              <p className="text-xs text-slate-400">Fetching road network…</p>
            </div>
          </div>
        ) : (
          <>
            {/* maplibre basemap div (positioned absolutely, fills container) */}
            <div ref={mapContainerRef} className="absolute inset-0" />
            {/* deck.gl canvas overlaid */}
            <DeckGL
              viewState={viewState}
              onViewStateChange={onViewStateChange}
              controller
              layers={layers}
              style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
            />
          </>
        )}

        {/* Hover tooltip */}
        {tooltip && (
          <div
            className="pointer-events-none absolute z-50 px-3 py-2 rounded-xl bg-slate-900/95 border border-slate-700 text-xs text-slate-200 shadow-xl whitespace-pre-line max-w-[220px]"
            style={{ left: tooltip.x + 12, top: tooltip.y + 12 }}
          >
            {tooltip.content}
          </div>
        )}
      </div>
    </div>
  )
}
