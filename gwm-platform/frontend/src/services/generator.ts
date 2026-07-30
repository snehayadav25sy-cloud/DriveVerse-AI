import api from './api'
import type { GenerateRequest, Job } from '../types'

export const VALID_MAPS = ['Town01', 'Town02', 'Town03']

export const generateDataset = async (req: GenerateRequest): Promise<Job> => {
  const { data } = await api.post<Job>('/jobs', req)
  return data
}
