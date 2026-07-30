import api from './api'
import type { QualityReport } from '../types'

export const fetchQualityReport = async (datasetId?: string): Promise<QualityReport | null> => {
  try {
    const { data } = await api.post<QualityReport>('/quality', { dataset_id: datasetId ?? null })
    return data
  } catch {
    return null
  }
}
