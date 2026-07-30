import { useQuery } from '@tanstack/react-query'
import { RefreshCw, Briefcase } from 'lucide-react'
import Navbar from '../components/Navbar'
import JobTable from '../components/JobTable'
import { fetchJobs } from '../services/jobs'

export default function Jobs() {
  const { data: jobs = [], isLoading, isFetching, refetch } = useQuery({
    queryKey: ['jobs'],
    queryFn: fetchJobs,
    refetchInterval: 3000,
  })

  const counts = {
    all:      jobs.length,
    running:  jobs.filter((j) => j.status === 'running').length,
    complete: jobs.filter((j) => j.status === 'completed').length,
    failed:   jobs.filter((j) => j.status === 'failed').length,
  }

  return (
    <div className="animate-fade-in">
      <Navbar title="Simulations" subtitle="Live simulation job monitor" />

      <div className="p-8 space-y-6">
        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total',    value: counts.all,      color: 'text-slate-300',   bg: 'bg-slate-800/60' },
            { label: 'Running',  value: counts.running,  color: 'text-amber-400',   bg: 'bg-amber-500/10' },
            { label: 'Complete', value: counts.complete, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
            { label: 'Failed',   value: counts.failed,   color: 'text-red-400',     bg: 'bg-red-500/10' },
          ].map(({ label, value, color, bg }) => (
            <div key={label} className={`card p-4 ${bg}`}>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</p>
              <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
            </div>
          ))}
        </div>

        {/* Table */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Briefcase size={17} className="text-brand-400" />
              <h2 className="section-title">All Jobs</h2>
              {isFetching && <span className="text-xs text-slate-500 animate-pulse">refreshing…</span>}
            </div>
            <button onClick={() => refetch()} className="btn-ghost text-xs gap-1.5">
              <RefreshCw size={13} className={isFetching ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
          <JobTable jobs={jobs} loading={isLoading} />
        </div>
      </div>
    </div>
  )
}
