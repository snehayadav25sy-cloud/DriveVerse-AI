import api from './api'

export interface BackendCountryProfile {
  id: string
  version: string
  drive_side: 'left' | 'right'
  vehicle_classes: string[]
  weather_presets: string[]
  supports: {
    auto_rickshaw: boolean
    tram: boolean
    train: boolean
    snow_accumulation: boolean
    deformable_terrain: boolean
  }
}

export const fetchCountries = async (): Promise<BackendCountryProfile[]> => {
  const { data } = await api.get<BackendCountryProfile[]>('/countries')
  return data
}

export const getCountry = async (id: string): Promise<any> => {
  const { data } = await api.get(`/countries/${id}`)
  return data
}

export const createCountry = async (yamlContent: string): Promise<any> => {
  const { data } = await api.post('/countries', { yaml_content: yamlContent })
  return data
}

export const updateCountry = async (id: string, yamlContent: string): Promise<any> => {
  const { data } = await api.put(`/countries/${id}`, { yaml_content: yamlContent })
  return data
}

export const deleteCountry = async (id: string): Promise<any> => {
  const { data } = await api.delete(`/countries/${id}`)
  return data
}
