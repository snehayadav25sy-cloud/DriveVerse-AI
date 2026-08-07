// src/services/prompt.ts — Build 3 v1.0 Stable
// Complete ScenarioConfig types and all API calls

import api from './api'

// ── ScenarioConfig types ──────────────────────────────────────────────────────

export interface VehicleMix {
  car: number
  truck: number
  bus: number
  motorcycle: number
  bicycle: number
  van: number
}

export interface ValidationIssue {
  level: 'error' | 'warning' | 'info'
  field: string
  message: string
  value?: any
  limit?: any
}

export interface ValidationResult {
  passed: boolean
  errors: ValidationIssue[]
  warnings: ValidationIssue[]
  infos: ValidationIssue[]
}

export interface OptimizerChange {
  field: string
  from_value: any
  to_value: any
  reason: string
}

export interface TranslationResult {
  carla_map: string
  confidence: number
  source: string
  note: string
}

export interface ScenarioEstimate {
  estimated_duration_seconds: number
  estimated_disk_mb: number
  estimated_gpu_vram_mb: number
  estimated_frames_actual: number
  cost_breakdown: Record<string, string>
  warnings: string[]
}

export interface ScenarioConfig {
  schema_version: string
  country?: string | null
  city?: string | null
  road_type?: string | null
  weather?: string | null
  time_of_day?: string | null
  lighting?: string | null
  traffic_density?: string | null
  vehicles: VehicleMix
  pedestrians: number
  sensors: string[]
  frames: number
  export_format: 'kitti' | 'coco' | 'nuscenes'
  carla_map?: string | null
  optimizer_applied: boolean
  validation_passed: boolean
  confidence: Record<string, number>
  explanation: string[]
  unrecognised_tokens: string[]
  source_prompt?: string | null
  llm_provider?: string | null
  validation?: ValidationResult | null
  optimizer_changes: OptimizerChange[]
  translation?: TranslationResult | null
  estimate?: ScenarioEstimate | null
}

export interface ParseResponse extends ScenarioConfig {
  validation: ValidationResult
  estimate?: ScenarioEstimate | null
}

export interface GenerateResponse {
  job_id: string
  scenario: ScenarioConfig
  scenario_id: string
  validation: { passed: boolean; warnings: ValidationIssue[] }
}

export interface PromptHistoryItem {
  id: string
  text: string
  created_at: string
  project_id: string
  scenario?: ScenarioConfig | null
  job_id?: string | null
}

export interface ProviderInfo {
  provider: string
  available: boolean
  supports_optimization: boolean
  env_key: string
  error?: string
}

export interface ScenarioTemplate {
  id: string
  label: string
  prompt: string
  scenario: Partial<ScenarioConfig>
}

export interface MapEntry {
  city: string
  country: string
  carla_map: string
  note: string
}

// ── API calls ─────────────────────────────────────────────────────────────────

/** Dry-run parse + full pipeline (no job created). */
export const parsePrompt = async (prompt: string): Promise<ParseResponse> => {
  const { data } = await api.post<ParseResponse>('/prompt/parse', { prompt })
  return data
}

/** Parse + immediately queue a job. */
export const parseAndSubmit = async (
  prompt: string,
  project_id: string,
): Promise<GenerateResponse> => {
  const { data } = await api.post<GenerateResponse>('/prompt/generate', {
    prompt,
    project_id,
  })
  return data
}

/** Optimize a ScenarioConfig. */
export const optimizeScenario = async (scenario: Partial<ScenarioConfig>) => {
  const { data } = await api.post('/prompt/optimize', { scenario })
  return data
}

/** Get resource estimate for a ScenarioConfig. */
export const previewScenario = async (
  scenario: Partial<ScenarioConfig>,
): Promise<ScenarioEstimate> => {
  const { data } = await api.post<ScenarioEstimate>('/prompt/preview', { scenario })
  return data
}

/** Get prompt history for current user. */
export const getPromptHistory = async (): Promise<PromptHistoryItem[]> => {
  const { data } = await api.get<PromptHistoryItem[]>('/prompt/history')
  return data
}

/** Get active LLM provider info. */
export const getProviderInfo = async (): Promise<ProviderInfo> => {
  const { data } = await api.get<ProviderInfo>('/prompt/provider')
  return data
}

/** Get city → CARLA map lookup table. */
export const getMaps = async (): Promise<{ maps: MapEntry[]; total: number }> => {
  const { data } = await api.get('/prompt/maps')
  return data
}

/** Get 10 built-in scenario templates. */
export const getTemplates = async (): Promise<{
  templates: ScenarioTemplate[]
  total: number
}> => {
  const { data } = await api.get('/prompt/templates')
  return data
}
