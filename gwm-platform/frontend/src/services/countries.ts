import api from './api'
import type { CountryProfile } from '../types'

// Mock data as fallback when backend is offline
export const MOCK_COUNTRIES: CountryProfile[] = [
  {
    code: 'TH',
    display_name: 'Thailand',
    driving_side: 'left',
    accurate_lane_discipline: false,
    common_road_types: ['urban', 'mixed_traffic', 'coastal'],
    speed_limit_kmh: 80,
    notes: 'High motorcycle density, monsoon weather patterns. Left-hand traffic not yet accurately represented.',
  },
  {
    code: 'BH',
    display_name: 'Bahrain',
    driving_side: 'right',
    accurate_lane_discipline: true,
    common_road_types: ['urban', 'highway', 'coastal'],
    speed_limit_kmh: 120,
    notes: 'Modern passenger vehicles and highways. Predominantly clear/hot weather.',
  },
  {
    code: 'AE',
    display_name: 'Dubai / UAE',
    driving_side: 'right',
    accurate_lane_discipline: true,
    common_road_types: ['highway', 'urban', 'desert'],
    speed_limit_kmh: 140,
    notes: 'Premium/luxury vehicles. Wide high-speed highways. Desert sun glare conditions.',
  },
]

export const fetchCountries = async (): Promise<CountryProfile[]> => {
  try {
    const { data } = await api.get<CountryProfile[]>('/countries')
    return data
  } catch {
    return MOCK_COUNTRIES
  }
}
