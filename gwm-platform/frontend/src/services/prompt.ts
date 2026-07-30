// src/services/prompt.ts — Build 3: AI Prompt Engine v1.0
// Calls the backend /prompt/parse endpoint and returns the parsed config.

import api from './api'

export interface PromptConfidence {
  map: number
  sensors: number
  frames: number
  export_format: number
}

export interface PromptParseResult {
  map: string
  sensors: string[]
  frames: number
  export_format: 'kitti' | 'coco' | 'nuscenes'
  confidence: PromptConfidence
  unrecognised_tokens: string[]
  explanation: string[]
}

export interface PromptSubmitResult {
  job_id: string
  map: string
  sensors: string[]
  frames: number
  export_format: string
  confidence: PromptConfidence
  explanation: string[]
}

/** Dry-run parse: returns inferred config WITHOUT creating a job. */
export const parsePrompt = async (prompt: string): Promise<PromptParseResult> => {
  const { data } = await api.post<PromptParseResult>('/prompt/parse', { prompt })
  return data
}

/** Parse + immediately queue a job. */
export const parseAndSubmit = async (
  prompt: string,
  project_id: string,
): Promise<PromptSubmitResult> => {
  const { data } = await api.post<PromptSubmitResult>('/prompt/parse-and-submit', {
    prompt,
    project_id,
  })
  return data
}
