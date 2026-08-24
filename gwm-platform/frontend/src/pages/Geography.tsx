/**
 * Geography.tsx — Build 5 + deck.gl: Geography Engine page
 */

import { useState } from 'react'
import { Globe, MapPin, Search, Loader2, CheckCircle2, XCircle, Box, Map } from 'lucide-react'
import Navbar from '../components/Navbar'
import RoadMapCanvas from '../components/RoadMapCanvas'
import {
  resolveLocation,
  buildMap,
  fetchRoadGraph,
  type ResolveResponse,
  type BuildResponse,
  type MapArtifact,
  type GraphGeoJSONResponse,
} from '../services/geography'

interface BuildStage {
  status: string
  elapsed_ms?: number
  [key: string]: unknown
}

const STAGES = [
  'resolve',
  'osm',
  'graph',
  'projection',
  'opendrive',
  'validate',
] as const

export default function Geography() {
  const [location, setLocation] = useState('MG Road, Bengaluru')
  const [radius, setRadius] = useState(500)
  const [resolveResult, setResolveResult] = useState<ResolveResponse | null>(null)
  const [buildResult, setBuildResult] = useState<BuildResponse | null>(null)
  const [graphResult, setGraphResult] = useState<GraphGeoJSONResponse | null>(null)
  const [loadingStage, setLoadingStage] = useState<string | null>(null)
  const [loadingMap, setLoadingMap] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleResolve() {
    setError(null)
    setResolveResult(null)
    setBuildResult(null)
    try {
      const data = await resolveLocation(location, radius)
      setResolveResult(data)
      if (data.status === 'failed') {
        setError(data.error || 'Resolution failed')
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(err?.response?.data?.detail || err?.message || 'Resolve failed')
    }
  }

  async function handleViewMap() {
    setError(null)
    setGraphResult(null)
    setLoadingMap(true)
    try {
      const data = await fetchRoadGraph(location, radius)
      setGraphResult(data)
      if (data.status === 'failed') {
        setError(data.error || 'Graph fetch failed')
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(err?.response?.data?.detail || err?.message || 'Map fetch failed')
    } finally {
      setLoadingMap(false)
    }
  }

  async function handleBuild() {
    setError(null)
    setBuildResult(null)
    setLoadingStage('resolve')
    // Also kick off the map preview in parallel
    handleViewMap()
    try {
      const data = await buildMap(location, radius)
      setBuildResult(data)
      setLoadingStage(null)
      if (data.status === 'failed') {
        setError(data.error || 'Build failed')
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(err?.response?.data?.detail || err?.message || 'Build failed')
      setLoadingStage(null)
    }
  }

  function renderStageIcon(stage: string, stageResult?: BuildStage) {
    if (!stageResult) return <div className="w-2 h-2 rounded-full bg-slate-700" />
    const s = stageResult.status
    if (['done', 'resolved', 'complete', 'valid', 'compiled', 'built', 'downloaded', 'projected'].includes(s))
      return <CheckCircle2 size={16} className="text-emerald-400" />
    if (['failed', 'invalid'].includes(s))
      return <XCircle size={16} className="text-rose-400" />
    if (loadingStage === stage)
      return <Loader2 size={16} className="animate-spin text-brand-400" />
    return <div className="w-2 h-2 rounded-full bg-slate-700" />
  }

  const artifact: MapArtifact | undefined = buildResult?.map_artifact

  return (
    <div className="animate-fade-in">
      <Navbar title="Geography Engine" subtitle="Resolve real-world locations and generate CARLA maps" />

      <div className="p-8 max-w-6xl mx-auto space-y-8">
        {/* Input Card */}
        <div className="card p-6 space-y-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600/20 to-violet-600/20 border border-brand-500/20">
              <Globe size={18} className="text-brand-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Location Input</h2>
              <p className="text-xs text-slate-500">Enter a real-world location to resolve, preview, and build</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Location</label>
              <input
                id="geo-location-input"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. MG Road, Bengaluru"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500/80 focus:ring-1 focus:ring-brand-500/80 transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Radius</label>
              <select
                id="geo-radius-select"
                value={radius}
                onChange={(e) => setRadius(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500/80 focus:ring-1 focus:ring-brand-500/80 transition-all"
              >
                <option value={500}>500 m</option>
                <option value={1000}>1 000 m</option>
                <option value={2000}>2 000 m</option>
              </select>
            </div>
            <div className="md:col-span-2 flex items-end gap-2">
              <button
                id="geo-resolve-btn"
                onClick={handleResolve}
                className="flex-1 btn-primary justify-center py-2.5 text-xs"
              >
                <Search size={14} /> Resolve
              </button>
              <button
                id="geo-viewmap-btn"
                onClick={handleViewMap}
                disabled={loadingMap}
                className="flex-1 btn-primary justify-center py-2.5 text-xs disabled:opacity-50"
              >
                {loadingMap
                  ? <><Loader2 size={14} className="animate-spin" /> Loading…</>
                  : <><Map size={14} /> View Map</>}
              </button>
              <button
                id="geo-build-btn"
                onClick={handleBuild}
                className="flex-1 btn-primary justify-center py-2.5 text-xs"
              >
                <Box size={14} /> Build Map
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-rose-500/15 text-rose-400 border border-rose-500/30 p-4 rounded-xl flex gap-2.5 items-start text-sm">
              <XCircle size={16} className="shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Resolve Result */}
        {resolveResult && resolveResult.status === 'resolved' && resolveResult.resolution && (
          <div className="card p-6 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <MapPin size={16} className="text-brand-400" /> Resolved Location
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div>
                <p className="text-slate-500">Latitude</p>
                <p className="text-slate-200 font-mono">{resolveResult.resolution.latitude}</p>
              </div>
              <div>
                <p className="text-slate-500">Longitude</p>
                <p className="text-slate-200 font-mono">{resolveResult.resolution.longitude}</p>
              </div>
              <div>
                <p className="text-slate-500">Country</p>
                <p className="text-slate-200">{resolveResult.resolution.country}</p>
              </div>
              <div>
                <p className="text-slate-500">City</p>
                <p className="text-slate-200">{resolveResult.resolution.city}</p>
              </div>
            </div>
            {resolveResult.resolution.bounding_box && (
              <div className="text-xs text-slate-400">
                BBox: S={resolveResult.resolution.bounding_box.south.toFixed(4)} N={resolveResult.resolution.bounding_box.north.toFixed(4)} W={resolveResult.resolution.bounding_box.west.toFixed(4)} E={resolveResult.resolution.bounding_box.east.toFixed(4)}
              </div>
            )}
          </div>
        )}

        {/* deck.gl Road Map Panel */}
        {(loadingMap || graphResult) && (
          <div className="animate-fade-in">
            {graphResult?.status === 'complete' && graphResult.geojson ? (
              <RoadMapCanvas
                geojson={graphResult.geojson}
                centerLat={graphResult.center_lat!}
                centerLon={graphResult.center_lon!}
                nodeCount={graphResult.node_count}
                edgeCount={graphResult.edge_count}
                elapsedMs={graphResult.elapsed_ms}
                loading={false}
              />
            ) : loadingMap ? (
              <RoadMapCanvas
                geojson={{ type: 'FeatureCollection', features: [] }}
                centerLat={0}
                centerLon={0}
                nodeCount={0}
                edgeCount={0}
                elapsedMs={0}
                loading
              />
            ) : null}
          </div>
        )}

        {/* Build Progress / Result */}
        {buildResult && (
          <div className="card p-6 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Box size={16} className="text-brand-400" /> Build Pipeline
            </h3>
            <div className="space-y-2">
              {STAGES.map((stage) => {
                const stageResult = buildResult.stages[stage] as BuildStage | undefined
                return (
                  <div key={stage} className="flex items-center gap-3 text-xs">
                    {renderStageIcon(stage, stageResult)}
                    <span className="text-slate-400 capitalize w-24">{stage}</span>
                    <span className={`font-mono ${stageResult?.status === 'failed' || stageResult?.status === 'invalid' ? 'text-rose-400' : 'text-slate-200'}`}>
                      {stageResult?.status || 'idle'}
                    </span>
                    {stageResult?.elapsed_ms && (
                      <span className="text-slate-500">{stageResult.elapsed_ms}ms</span>
                    )}
                  </div>
                )
              })}
            </div>

            {artifact && (
              <div className="mt-4 p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2 text-xs">
                <p className="text-slate-400 font-semibold">Map Artifact</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-slate-500">OpenDRIVE</p>
                    <p className="text-slate-200 font-mono truncate" title={artifact.xodr_path}>{artifact.xodr_path}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Size</p>
                    <p className="text-slate-200 font-mono">{artifact.xodr_size_bytes} bytes</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Validator</p>
                    <p className={artifact.validator_passed ? 'text-emerald-400' : 'text-rose-400'}>
                      {artifact.validator_passed ? 'PASSED' : 'FAILED'}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500">Errors</p>
                    <p className="text-slate-200 font-mono">{artifact.validator_errors.length}</p>
                  </div>
                </div>
                {artifact.validator_errors.length > 0 && (
                  <div className="mt-2 text-rose-400">
                    {artifact.validator_errors.slice(0, 3).map((e, i) => <div key={i}>- {e}</div>)}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
