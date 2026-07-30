import api from './api'
import type { Job, Dataset } from '../types'

export const fetchJobs = async (): Promise<Job[]> => {
  const { data } = await api.get<Job[]>('/jobs')
  return data
}

export const fetchJob = async (id: string): Promise<Job> => {
  const { data } = await api.get<Job>(`/jobs/${id}`)
  return data
}

export const fetchDatasets = async (): Promise<Dataset[]> => {
  try {
    const { data } = await api.get<Dataset[]>('/datasets')
    return data
  } catch (err) {
    return []
  }
}
