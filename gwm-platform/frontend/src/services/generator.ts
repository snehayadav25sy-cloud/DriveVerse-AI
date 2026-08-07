import api from './api'
import type { GenerateRequest, Job } from '../types'

// Only Town01/02/03 confirmed loaded in CARLA 0.9.16 — matches backend SUPPORTED_MAPS
export const VALID_MAPS = ['Town01', 'Town02', 'Town03']

export const generateDataset = async (req: GenerateRequest): Promise<Job> => {
  const { data } = await api.post<Job>('/jobs', req)
  return data
}
