import { useQuery } from '@tanstack/react-query'
import { Database, Cpu, Globe, BarChart3, ArrowRight, Zap, Download } from 'lucide-react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import StatCard from '../components/StatCard'
import JobTable from '../components/JobTable'
import { fetchJobs } from '../services/jobs'
import { fetchDatasets, downloadDataset } from '../services/datasets'
import { useAuth } from '../contexts/AuthContext'


function relativeTime(iso: string) {
  const dateStr = iso.endsWith('Z') ? iso : `${iso}Z`
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.max(0, Math.floor(diff / 60000))
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}
import { useState } from 'react'
import MauritiusPilotDashboard from '../components/MauritiusPilotDashboard'

export default function Dashboard() {
  const { token } = useAuth();
  const [selectedCountry, setSelectedCountry] = useState<'india' | 'mauritius'>('mauritius')
  


  const { data: jobs = [], isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: fetchJobs,
    refetchInterval: 5000,
    enabled: !!token
  })
  
  const { data: datasets = [], isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: fetchDatasets,
    refetchInterval: 5000,
    enabled: !!token
  })

  const { data: analytics } = useQuery({
    queryKey: ['analyticsQuality'],
    queryFn: async () => {
      const res = await (await import('../services/api')).default.get('/analytics/quality')
      return res.data
    },
    refetchInterval: 5000,
    enabled: !!token
  })

  const running  = jobs.filter((j: any) => j.status === 'Running' || j.status === 'Processing' || j.status === 'Pending').length
  const complete = datasets.length

  return (
    <div className="animate-fade-in">
      <Navbar title="Dashboard" subtitle="DriveVerse AI · Synthetic Dataset Platform" />

      <div className="p-8 space-y-8">
        {/* Country Selector Header Bar */}
        <div className="flex items-center justify-between bg-slate-900/80 border border-slate-800 p-4 rounded-2xl">
          <div className="flex items-center gap-3">
            <Globe className="text-brand-400" size={20} />
            <div>
              <h3 className="text-sm font-bold text-white">Active Regulator Pilot View</h3>
              <p className="text-xs text-slate-400">Select target region to filter scenario coverage and geography</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-slate-400">Target Region:</label>
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value as 'india' | 'mauritius')}
              className="bg-slate-950 border border-slate-750 text-white text-xs font-bold px-3 py-2 rounded-xl focus:outline-none focus:border-brand-500 transition-all cursor-pointer"
            >
              <option value="mauritius">🇲🇺 Mauritius Pilot (Ebene / M1 Corridor)</option>
              <option value="india">🇮🇳 India Baseline (Bengaluru / Mumbai)</option>
            </select>
          </div>
        </div>

        {selectedCountry === 'mauritius' ? (
          <MauritiusPilotDashboard />
        ) : (
          <>
            {/* Hero */}
            <div className="card p-8 relative overflow-hidden bg-grid-pattern">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-600/10 via-transparent to-violet-600/10 pointer-events-none" />
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-500/15 text-brand-400 text-xs font-semibold border border-brand-500/20">
                <Zap size={10} /> v1.0 Pilot Active
              </span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">
              Country-Aware Synthetic{' '}
              <span className="gradient-text">Driving Datasets</span>
            </h2>
            <p className="text-slate-400 max-w-xl text-sm leading-relaxed">
              Generate labeled autonomous driving data for Thailand 🇹🇭, Bahrain 🇧🇭, and the UAE 🇦🇪.
              Each clip is parametrized by regional vehicle mix, weather bias, and edge-case scenario presets.
            </p>
            <div className="flex gap-3 mt-6">
              <Link to="/generate" className="btn-primary">
                <Zap size={15} /> Generate Dataset
              </Link>
              <Link to="/countries" className="btn-secondary">
                <Globe size={15} /> View Profiles
              </Link>
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <StatCard label="Datasets Generated" value={complete} icon={Database} accent="cyan"
            trend={1} trendLabel="+1 this session" loading={datasetsLoading} />
          <StatCard label="Jobs Running" value={running} icon={Cpu} accent="amber"
            trendLabel={running > 0 ? 'Processing now' : 'Queue empty'} loading={jobsLoading} />
          <StatCard label="Countries Supported" value={3} icon={Globe} accent="green"
            trendLabel="TH · BH · AE" />
          <StatCard label="Avg Quality Score" value={analytics?.overall_quality ?? 0} icon={BarChart3} accent="violet"
            trend={1} trendLabel="Computed live from DB" />
        </div>

        {/* Datasets & Jobs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Jobs */}
          <div className="card p-6 flex flex-col">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="section-title">Recent Jobs</h3>
                <p className="section-sub">Auto-refreshes every 5 seconds</p>
              </div>
              <Link to="/jobs" className="btn-ghost text-xs">
                View all <ArrowRight size={13} />
              </Link>
            </div>
            <div className="flex-1 overflow-auto">
              <JobTable jobs={jobs.slice(0, 5)} loading={jobsLoading} />
            </div>
          </div>

          {/* Datasets */}
          <div className="card p-6 flex flex-col">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="section-title">Ready Datasets</h3>
                <p className="section-sub">Download completed datasets</p>
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              {datasetsLoading ? (
                <div className="text-sm text-slate-500 p-4 text-center">Loading datasets...</div>
              ) : datasets.length === 0 ? (
                <div className="text-sm text-slate-500 p-8 text-center flex flex-col items-center gap-3">
                  <Database size={24} className="text-slate-600" />
                  No datasets generated yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {datasets.slice(0, 5).map((ds: any) => (
                    <div key={ds.id} className="flex items-center justify-between p-3 rounded-lg border border-slate-700 bg-slate-800/50">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                          <Database size={14} />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-200">Dataset {ds.id.slice(0, 6)}</p>
                          <div className="flex flex-wrap items-center gap-1 mt-1 text-[10px]">
                            <span className="bg-brand-500/10 text-brand-400 px-1.5 py-0.5 rounded border border-brand-500/15 font-semibold uppercase">{ds.export_format || 'kitti'}</span>
                            <span className="text-slate-500">·</span>
                            <span className="text-slate-400">{ds.frame_count}f</span>
                            {ds.rgb_count > 0 && (
                              <>
                                <span className="text-slate-500">·</span>
                                <span className="text-emerald-400 font-medium">{ds.rgb_count} RGB</span>
                              </>
                            )}
                            {ds.lidar_count > 0 && (
                              <>
                                <span className="text-slate-500">·</span>
                                <span className="text-cyan-400 font-medium">{ds.lidar_count} LiDAR</span>
                              </>
                            )}
                            {ds.annotation_count > 0 && (
                              <>
                                <span className="text-slate-500">·</span>
                                <span className="text-violet-400 font-medium">{ds.annotation_count} Annots</span>
                              </>
                            )}
                          </div>
                          <p className="text-[10px] text-slate-500 mt-1">{relativeTime(ds.created_at)}</p>
                        </div>
                      </div>
                      <button onClick={() => downloadDataset(ds.id)} className="btn-secondary px-3 py-1.5 text-xs">
                        <Download size={14} /> Download ZIP
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { to: '/generate', icon: Cpu,       title: 'Generate Dataset',   desc: 'Configure country, scenario & export format' },
            { to: '/quality',  icon: BarChart3,  title: 'Quality Analyzer',   desc: 'Coverage, diversity & recommendation scores' },
            { to: '/countries',icon: Globe,      title: 'Country Profiles',   desc: 'Vehicle mix, weather bias, speed limits' },
          ].map(({ to, icon: Icon, title, desc }) => (
            <Link key={to} to={to} className="card-hover p-5 group flex items-start gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 group-hover:bg-brand-500/20 transition-colors">
                <Icon size={18} className="text-slate-400 group-hover:text-brand-400 transition-colors" />
              </div>
              <div>
                <p className="font-semibold text-slate-200 text-sm group-hover:text-white transition-colors">{title}</p>
                <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{desc}</p>
              </div>
              <ArrowRight size={15} className="ml-auto text-slate-600 group-hover:text-brand-400 transition-colors mt-0.5" />
            </Link>
          ))}
        </div>
        </>
        )}
      </div>
    </div>
  )
}
