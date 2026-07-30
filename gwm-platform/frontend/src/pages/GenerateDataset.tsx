/**
 * GenerateDataset.tsx — Build 3 updated
 * ======================================
 * Now features the AI Prompt Engine (PromptBar) above the manual form.
 * When the user accepts a parsed config, it pre-fills GenerateForm.
 */

import { useState } from 'react'
import { Sparkles, Info } from 'lucide-react'
import Navbar from '../components/Navbar'
import GenerateForm from '../components/GenerateForm'
import PromptBar from '../components/PromptBar'
import type { AppliedConfig } from '../components/PromptBar'
import type { Job } from '../types'

export default function GenerateDataset() {
  const [lastJob, setLastJob]           = useState<Job | null>(null)
  const [projects, setProjects]         = useState<Array<{ id: string; name: string }>>([])
  const [injectedValues, setInjected]   = useState<AppliedConfig | undefined>(undefined)

  return (
    <div className="animate-fade-in">
      <Navbar title="Generate Dataset" subtitle="Configure and launch a CARLA simulation job" />

      <div className="p-8 space-y-6">
        {/* ── AI Prompt Engine ── */}
        <PromptBar
          projects={projects}
          onApply={(cfg) => setInjected(cfg)}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          {/* Form */}
          <div className="lg:col-span-2 card p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600/20 to-violet-600/20 border border-brand-500/20">
                <Sparkles size={18} className="text-brand-400" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">New Dataset Job</h2>
                <p className="text-xs text-slate-500">
                  {injectedValues
                    ? '✨ Form pre-filled by AI — review and submit'
                    : 'Manual configuration — or use the AI Prompt Engine above'}
                </p>
              </div>
            </div>
            <GenerateForm
              onJobCreated={(job) => setLastJob(job)}
              initialValues={injectedValues}
              onProjectsLoaded={setProjects}
            />
          </div>

          {/* Info sidebar */}
          <div className="space-y-5">
            {lastJob && (
              <div className="card p-5 border-emerald-500/20 ring-1 ring-emerald-500/20 animate-slide-up">
                <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3">Job Created</p>
                <div className="space-y-2 text-sm">
                  {[
                    ['ID',      lastJob.id.slice(0, 12) + '…'],
                    ['Project', lastJob.project_id.slice(0, 12) + '…'],
                    ['Status',  lastJob.status],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-slate-500">{k}</span>
                      <span className="text-slate-200 font-medium font-mono text-xs">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <Info size={14} className="text-brand-400" />
                <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Export Formats</p>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-400">
                {[
                  ['KITTI',      '2D bbox + class labels'],
                  ['COCO JSON',  'Full annotation with categories'],
                  ['nuScenes',   'AV sweep and scene synchronization metadata'],
                ].map(([fmt, desc]) => (
                  <li key={fmt} className="flex items-start gap-2">
                    <span className="mt-0.5 text-brand-500">·</span>
                    <span><strong className="text-slate-300">{fmt}</strong> — {desc}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="card p-5">
              <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">How It Works</p>
              <ol className="space-y-2 text-xs text-slate-400">
                {[
                  'Describe scenario in plain English (Build 3)',
                  'AI Prompt Engine parses your intent',
                  'Form auto-fills — review & adjust if needed',
                  'Job queued in PostgreSQL',
                  'CARLA simulation runs with selected sensors',
                  'Dataset packaged and ready to download',
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 font-bold flex-shrink-0">{i + 1}</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
