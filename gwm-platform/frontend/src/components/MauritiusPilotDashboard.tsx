import { useState } from 'react'
import {
  MapPin,
  ShieldCheck,
  Car,
  Layers,
  Info
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip as RechartsTooltip
} from 'recharts'

interface ScenarioCardProps {
  id: string
  title: string
  location: string
  status: 'PLANNED' | 'GENERATED' | 'RUNNING'
  speed: string
  weather: string
  details: string
  tag?: string
}

const MAURITIUS_SCENARIOS: ScenarioCardProps[] = [
  {
    id: 'SC-MU-01',
    title: 'Ebene Cybercity Peak-Hour Drop-off',
    location: 'Ebene Cybercity (lat: -20.244, lon: 57.491)',
    status: 'PLANNED',
    speed: '30 km/h',
    weather: 'Clear / Congested',
    details: 'Dense static + dynamic urban traffic around tech hub',
    tag: 'Urban Drop-off'
  },
  {
    id: 'SC-MU-02',
    title: 'M1/M2 Highway High-Speed Corridor Flow',
    location: 'Pont-Fer Roundabout Segment',
    status: 'PLANNED',
    speed: '110 km/h',
    weather: 'Clear Noon',
    details: 'Dual-carriageway LHT arterial flow with 20% heavy trucks',
    tag: 'Highway Corridor'
  },
  {
    id: 'SC-MU-03',
    title: 'Pont-Fer Roundabout Navigation',
    location: 'Pont-Fer Roundabout (lat: -20.274, lon: 57.497)',
    status: 'PLANNED',
    speed: '60 km/h',
    weather: 'Clear',
    details: 'Priority-to-the-right yielding at multi-lane roundabout',
    tag: 'Junction Yielding'
  },
  {
    id: 'SC-MU-04',
    title: 'Heavy Tropical Rain on M1 Highway',
    location: 'M1 Highway Corridor',
    status: 'PLANNED',
    speed: '80 km/h',
    weather: 'Heavy Rain (Precip 0.8, Wetness 0.9)',
    details: 'Reduced friction, fog, active wiper synchronization',
    tag: 'Weather Edge Case'
  },
  {
    id: 'SC-MU-05',
    title: 'Safety-Operator Intervention Event',
    location: 'Ebene Cybercity Junction',
    status: 'PLANNED',
    speed: '30 km/h',
    weather: 'Clear',
    details: 'Forced manual takeover triggered during congestion deadlock',
    tag: 'Safety Takeover'
  }
]

const NLTA_FLEET_DATA = [
  { name: 'Cars & Dual Purpose', value: 56.8, color: '#3b82f6' },
  { name: 'Motorcycles & Auto-cycles', value: 34.4, color: '#06b6d4' },
  { name: 'Goods Vehicles (Trucks)', value: 4.1, color: '#f59e0b' },
  { name: 'Buses & Shuttles', value: 0.6, color: '#10b981' },
  { name: 'Other Vehicles', value: 4.1, color: '#8b5cf6' }
]

export default function MauritiusPilotDashboard() {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null)

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Pilot Overview Header */}
      <div className="card p-6 bg-gradient-to-r from-slate-900 via-slate-900/90 to-brand-950/40 border border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <span className="text-4xl">🇲🇺</span>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white">Mauritius Autonomous Pilot View</h2>
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 text-xs font-semibold border border-emerald-500/20">
                  LHT Rules Active
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Ebene Cybercity & M1/M2 Highway Corridor Pilot Zone (NLTA 2025 Fleet Parametrized)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* City2Graph Toggle */}
            <div className="relative group">
              <button
                disabled
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/60 text-slate-500 text-xs font-medium border border-slate-700/50 cursor-not-allowed opacity-75"
              >
                <Layers size={14} /> City2Graph Layer
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Pending Data Source
                </span>
              </button>
              <div className="absolute right-0 top-full mt-2 hidden group-hover:block z-20 w-64 p-3 bg-slate-950 border border-slate-800 rounded-xl text-[11px] text-slate-400 shadow-xl">
                <p className="font-semibold text-slate-200 mb-1 flex items-center gap-1">
                  <Info size={12} className="text-amber-400" /> City2Graph Status
                </p>
                No public GTFS feed available for Ebene. Graph visualization defaults to structural road network.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Map & OpenDRIVE Validation Badges */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Geo-spatial Corridor Map Card */}
        <div className="lg:col-span-2 card p-6 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MapPin size={18} className="text-brand-400" />
              <h3 className="text-sm font-bold text-white">Target Zone: Ebene & Pont-Fer Corridor</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              Center: -20.2500°S, 57.4900°E
            </span>
          </div>

          {/* Map Canvas Visualiser Simulation */}
          <div className="relative w-full h-72 rounded-xl bg-slate-950 border border-slate-800 overflow-hidden flex flex-col justify-between p-4 group">
            {/* Visual grid / road graphics representation */}
            <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-40"></div>
            
            {/* Roundabout Graphic Accent */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 rounded-full border-2 border-dashed border-cyan-500/30 flex items-center justify-center">
              <div className="w-20 h-20 rounded-full border border-brand-500/40 bg-brand-500/10 flex items-center justify-center">
                <span className="text-[10px] font-bold text-cyan-400 tracking-widest uppercase">Pont-Fer</span>
              </div>
            </div>

            {/* Ebene Cybercity Node */}
            <div className="absolute top-1/4 left-1/3 flex items-center gap-1.5 bg-slate-900/90 border border-slate-700 px-2.5 py-1 rounded-lg shadow-lg">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></div>
              <span className="text-xs font-semibold text-slate-200">Ebene Cybercity</span>
            </div>

            {/* M1 Highway Vector */}
            <div className="absolute bottom-1/4 right-1/4 flex items-center gap-1.5 bg-slate-900/90 border border-slate-700 px-2.5 py-1 rounded-lg shadow-lg">
              <div className="w-2 h-2 rounded-full bg-brand-400"></div>
              <span className="text-xs font-semibold text-slate-200">M1 Highway Dual-Carriageway</span>
            </div>

            <div className="relative z-10 flex justify-between items-end mt-auto">
              <div className="bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] text-slate-300">
                <span className="text-slate-500">Bounding Box:</span> 500m radius around Ebene & Pont-Fer
              </div>
              <div className="flex gap-2">
                <span className="px-2 py-1 rounded bg-slate-800 text-slate-300 text-[10px] font-mono border border-slate-700">
                  OpenDRIVE v1.6
                </span>
                <span className="px-2 py-1 rounded bg-amber-500/10 text-amber-400 text-[10px] font-semibold border border-amber-500/20">
                  Left-Hand Drive (LHT)
                </span>
              </div>
            </div>
          </div>

          {/* OpenDRIVE Validator Status Badges */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-2">
            <div className="p-3.5 rounded-xl bg-slate-950 border border-emerald-500/20 flex items-start gap-3">
              <ShieldCheck size={18} className="text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-200">Ebene Cybercity XODR</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 font-bold">VALID</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  0 errors, 77 warnings (246.5 KB map size, 74 junctions)
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-emerald-500/20 flex items-start gap-3">
              <ShieldCheck size={18} className="text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-200">Pont-Fer Roundabout XODR</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 font-bold">VALID</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  0 errors, 41 warnings (146.0 KB map size, 40 junctions)
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Fleet Mix Breakdown Card */}
        <div className="card p-6 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Car size={16} className="text-brand-400" /> NLTA 2025 Fleet Distribution
              </h3>
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Official Stats</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Parametrized vehicle spawn ratios for Mauritius simulations
            </p>
          </div>

          {/* Recharts Pie Chart */}
          <div className="h-48 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={NLTA_FLEET_DATA}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {NLTA_FLEET_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip
                  formatter={(val: any) => [`${val}%`, 'Share']}
                  contentStyle={{ backgroundColor: '#090d16', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Fleet Shares Legend */}
          <div className="space-y-1.5 text-xs pt-2 border-t border-slate-800">
            {NLTA_FLEET_DATA.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-slate-300">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-[11px]">{item.name}</span>
                </div>
                <span className="font-mono font-semibold text-slate-200">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Scenario Coverage Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Mauritius Scenario Library Coverage</h3>
            <p className="text-xs text-slate-400">5 Pilot Scenarios parametrized with WorldPlanner determinism</p>
          </div>
          <span className="text-xs text-brand-400 font-semibold bg-brand-500/10 px-3 py-1 rounded-full border border-brand-500/20">
            5 / 5 Scenarios Ready
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {MAURITIUS_SCENARIOS.map((sc) => (
            <div
              key={sc.id}
              onClick={() => setSelectedScenario(sc.id)}
              className={`card p-5 space-y-3 cursor-pointer transition-all border ${
                selectedScenario === sc.id
                  ? 'border-brand-500 bg-brand-500/5 shadow-lg shadow-brand-500/10'
                  : 'border-slate-800 hover:border-slate-700 bg-slate-900/60'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-500">{sc.id}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/20">
                  {sc.status}
                </span>
              </div>

              <div>
                <h4 className="text-sm font-bold text-white group-hover:text-brand-300 transition-colors">
                  {sc.title}
                </h4>
                <p className="text-xs text-slate-400 mt-1">{sc.details}</p>
              </div>

              <div className="flex flex-wrap items-center gap-2 text-[10px] pt-2 border-t border-slate-800 text-slate-400">
                <span className="bg-slate-800 px-2 py-0.5 rounded text-slate-300">⚡ {sc.speed}</span>
                <span className="bg-slate-800 px-2 py-0.5 rounded text-slate-300">🌤 {sc.weather}</span>
                {sc.tag && (
                  <span className="bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded font-semibold">
                    {sc.tag}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
