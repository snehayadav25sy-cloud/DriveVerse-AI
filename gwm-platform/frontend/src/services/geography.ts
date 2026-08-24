/**
 * src/services/geography.ts — Build 5: Geography API service
 */

import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000'

export interface GeoCoordinate {
  latitude: number
  longitude: number
  altitude?: number
}

export interface BoundingBox {
  south: number
  north: number
  west: number
  east: number
}

export interface LocationResolution {
  query: string
  provider: string
  latitude: number
  longitude: number
  display_name?: string
  country?: string
  country_code?: string
  state?: string
  city?: string
  bounding_box?: BoundingBox
  cached?: boolean
  timestamp?: string
}

export interface ResolveResponse {
  status: 'resolved' | 'failed'
  query: string
  resolution?: LocationResolution
  error?: string
}

export interface BuildStage {
  status: string
  [key: string]: any
}

export interface MapArtifact {
  xodr_path?: string
  xodr_size_bytes: number
  xodr_hash?: string
  validator_passed: boolean
  validator_errors: string[]
  validator_warnings: string[]
  carla_map_name?: string
  carla_load_succeeded?: boolean
  carla_spawn_point_count?: number
  metadata: Record<string, any>
}

export interface BuildResponse {
  status: string
  stages: Record<string, BuildStage>
  map_artifact?: MapArtifact
  provenance?: Record<string, any>
  error?: string
}

export async function resolveLocation(
  location: string,
  radius_m: number = 500,
): Promise<ResolveResponse> {
  const resp = await axios.post(`${API_BASE}/geography/resolve`, {
    location,
    radius_m,
  })
  return resp.data
}

export interface GraphGeoJSONResponse {
  status: string
  center_lat?: number
  center_lon?: number
  node_count: number
  edge_count: number
  elapsed_ms: number
  geojson?: {
    type: 'FeatureCollection'
    features: GeoJSONFeature[]
  }
  error?: string
}

export interface GeoJSONFeature {
  type: 'Feature'
  geometry: {
    type: 'LineString' | 'Point'
    coordinates: number[] | number[][]
  }
  properties: Record<string, any>
}

export async function buildMap(
  location: string,
  radius_m: number = 500,
): Promise<BuildResponse> {
  const resp = await axios.post(`${API_BASE}/geography/build`, {
    location,
    radius_m,
  })
  return resp.data
}

export async function fetchRoadGraph(
  location: string,
  radius_m: number = 500,
): Promise<GraphGeoJSONResponse> {
  const resp = await axios.post(`${API_BASE}/geography/graph`, {
    location,
    radius_m,
  })
  return resp.data
}
