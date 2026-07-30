import type { CountryProfile } from '../types'
import { Car, Gauge, MapPin } from 'lucide-react'

const FLAG: Record<string, string> = { TH: '🇹🇭', BH: '🇧🇭', AE: '🇦🇪' }

const VEHICLE_DIST: Record<string, { label: string; pct: number; color: string }[]> = {
  TH: [
    { label: 'Motorcycles', pct: 45, color: 'from-amber-500 to-orange-500' },
    { label: 'Sedans',      pct: 35, color: 'from-brand-500 to-cyan-400' },
    { label: 'Trucks',      pct: 20, color: 'from-violet-500 to-purple-400' },
  ],
  BH: [
    { label: 'Luxury',      pct: 55, color: 'from-brand-500 to-cyan-400' },
    { label: 'Sedans',      pct: 35, color: 'from-violet-500 to-purple-400' },
    { label: 'Trucks',      pct: 10, color: 'from-slate-500 to-slate-400' },
  ],
  AE: [
    { label: 'Luxury',      pct: 65, color: 'from-amber-400 to-yellow-400' },
    { label: 'Sedans',      pct: 25, color: 'from-brand-500 to-cyan-400' },
    { label: 'Trucks',      pct: 10, color: 'from-slate-500 to-slate-400' },
  ],
}

interface CountryCardProps { profile: CountryProfile }

export default function CountryCard({ profile }: CountryCardProps) {
  const dist = VEHICLE_DIST[profile.code] ?? []
  return (
    <div className="card-hover p-6 animate-fade-in flex flex-col gap-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <span className="text-3xl">{FLAG[profile.code] ?? '🌍'}</span>
        <div>
          <h3 className="font-bold text-white text-base">{profile.display_name}</h3>
          <p className="text-xs text-slate-500">{profile.code} · {profile.driving_side === 'left' ? 'LHT' : 'RHT'}</p>
        </div>
        <span className={`ml-auto px-2.5 py-1 rounded-full text-xs font-semibold ${profile.accurate_lane_discipline ? 'bg-emerald-500/15 text-emerald-400' : 'bg-amber-500/15 text-amber-400'}`}>
          {profile.accurate_lane_discipline ? '✓ Lane Accurate' : '⚠ Lane Approx.'}
        </span>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-slate-800/60 rounded-xl p-2.5">
          <Gauge size={14} className="text-brand-400 mx-auto mb-1" />
          <p className="text-sm font-bold text-white">{profile.speed_limit_kmh}</p>
          <p className="text-[10px] text-slate-500">km/h limit</p>
        </div>
        <div className="bg-slate-800/60 rounded-xl p-2.5">
          <Car size={14} className="text-violet-400 mx-auto mb-1" />
          <p className="text-sm font-bold text-white">{dist.length}</p>
          <p className="text-[10px] text-slate-500">vehicle types</p>
        </div>
        <div className="bg-slate-800/60 rounded-xl p-2.5">
          <MapPin size={14} className="text-neon-green mx-auto mb-1" />
          <p className="text-sm font-bold text-white">{profile.common_road_types.length}</p>
          <p className="text-[10px] text-slate-500">road types</p>
        </div>
      </div>

      {/* Vehicle distribution */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Vehicle Distribution</p>
        {dist.map((d) => (
          <div key={d.label} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">{d.label}</span>
              <span className="text-slate-300 font-semibold">{d.pct}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-800">
              <div className={`h-full rounded-full bg-gradient-to-r ${d.color} transition-all duration-700`} style={{ width: `${d.pct}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Road types */}
      <div className="flex flex-wrap gap-1.5">
        {profile.common_road_types.map((r) => (
          <span key={r} className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-400 border border-slate-700/60 capitalize">
            {r.replace('_', ' ')}
          </span>
        ))}
      </div>

      {/* Note */}
      <p className="text-xs text-slate-500 leading-relaxed border-t border-slate-800/60 pt-3">{profile.notes}</p>
    </div>
  )
}
