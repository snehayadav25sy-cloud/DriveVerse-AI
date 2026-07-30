import type { Job } from '../types'
import { Loader2, CheckCircle2, XCircle, Clock, Download } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

interface JobTableProps { jobs: Job[]; loading?: boolean }

// spec statuses: queued | running | completed | failed
const STATUS_MAP: Record<string, { badge: string; icon: React.ReactNode }> = {
  queued:    { badge: 'badge-queued',   icon: <Clock size={10} /> },
  running:   { badge: 'badge-running',  icon: <Loader2 size={10} className="animate-spin" /> },
  completed: { badge: 'badge-complete', icon: <CheckCircle2 size={10} /> },
  failed:    { badge: 'badge-failed',   icon: <XCircle size={10} /> },
}

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

export default function JobTable({ jobs, loading }: JobTableProps) {
  const { token } = useAuth()

  const handleDownload = async (jobId: string) => {
    if (!token) return
    try {
      const res = await fetch(`http://127.0.0.1:8000/jobs/${jobId}/download`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `dataset_${jobId}.zip`
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch {
      alert('Failed to download dataset')
    }
  }

  if (loading) return (
    <div className="space-y-3 p-1">
      {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-12 rounded-xl" />)}
    </div>
  )
  if (!jobs.length) return (
    <div className="text-center py-12 text-slate-500">
      <p className="text-sm">No jobs yet. Generate your first dataset!</p>
    </div>
  )

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800/60">
            {['Job ID', 'Map / Format', 'Sensors', 'Frames', 'Status', 'Progress', 'Created', ''].map((h) => (
              <th key={h} className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/40">
          {jobs.map((job) => {
            const s = STATUS_MAP[job.status] ?? STATUS_MAP.queued
            return (
              <tr key={job.id} className="group hover:bg-slate-800/30 transition-colors duration-150">
                <td className="py-3.5 px-4">
                  <span className="font-mono text-xs text-slate-400 group-hover:text-slate-300">{job.id.slice(0, 8)}…</span>
                </td>
                <td className="py-3.5 px-4">
                  <div className="flex flex-col">
                    <span className="text-slate-300 font-medium text-xs">{job.map}</span>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wide">{job.export_format || 'kitti'}</span>
                  </div>
                </td>
                <td className="py-3.5 px-4">
                  <div className="flex flex-wrap gap-1">
                    {(Array.isArray(job.sensors) ? job.sensors : [job.sensors]).map((s: string) => {
                      const colors: Record<string, string> = {
                        rgb:   'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
                        lidar: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
                        radar: 'text-violet-400 bg-violet-500/10 border-violet-500/30',
                      }
                      return (
                        <span key={s} className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${colors[s] ?? 'text-slate-400 bg-slate-700/30 border-slate-600'}`}>
                          {s}
                        </span>
                      )
                    })}
                  </div>
                </td>
                <td className="py-3.5 px-4">
                  <span className="text-xs text-slate-400">{job.frames}</span>
                </td>
                <td className="py-3.5 px-4">
                  <span className={s.badge}>
                    {s.icon}
                    {job.status}
                  </span>
                </td>
                <td className="py-3.5 px-4 w-40">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 rounded-full bg-slate-800">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-brand-500 to-violet-500 transition-all duration-700"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-500 w-8 text-right">{job.progress.toFixed(0)}%</span>
                  </div>
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-500">{relativeTime(job.created_at)}</td>
                <td className="py-3.5 px-4">
                  {job.status === 'completed' && (
                    <button
                      onClick={() => handleDownload(job.id)}
                      className="btn-primary py-1.5 px-3 text-xs shadow-md shadow-brand-500/20"
                      title="Download ZIP"
                    >
                      <Download size={14} className="mr-1 inline" /> Download
                    </button>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
