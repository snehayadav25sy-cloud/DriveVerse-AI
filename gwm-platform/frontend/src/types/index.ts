// ── Shared domain types — Build 0/1 spec-aligned ─────────────────────────

export interface Job {
  id: string
  project_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  map: string
  sensors: string[]          // Build 2: list e.g. ["rgb", "lidar"]
  frames: number
  export_format: 'kitti' | 'coco' | 'nuscenes'
  output_path: string | null
  created_at: string
}

export interface Dataset {
  id: string
  job_id: string
  sensors: string[]          // Build 2: matches Job.sensors
  sensor_metadata?: Record<string, unknown> | null
  path: string
  frame_count: number
  rgb_count: number
  lidar_count: number
  annotation_count: number
  export_format: string
  created_at: string
}

export interface Project {
  id: string
  name: string
  description?: string
  created_at: string
}

export interface GenerateRequest {
  project_id: string
  map: string
  sensors: string[]          // Build 2: at least one of rgb | lidar
  frames: number
  export_format: string
}

// Legacy — kept for Country Profiles / Quality pages
export interface CountryProfile {
  code: string
  display_name: string
  driving_side: 'left' | 'right'
  accurate_lane_discipline: boolean
  common_road_types: string[]
  speed_limit_kmh: number
  notes: string
}

export interface QualityReport {
  overall_score: number
  coverage: number
  weather_diversity: number
  lighting_diversity: number
  road_coverage: number
  warnings: string[]
  recommendations: string[]
}
