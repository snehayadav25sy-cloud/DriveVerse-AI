/**
 * ScenarioCard.tsx — Build 3.1: Reusable Scenario JSON display card
 * ===================================================================
 * Displays a ScenarioConfig in a structured, beautiful card.
 * Used by PromptBar, GeneratePrompt, PromptHistory, ScenarioPreview.
 */

import { useState } from 'react'
import {
  MapPin, Car,
  ChevronDown, ChevronUp, CheckCircle2, AlertCircle, Info,
  Gauge, Clock, HardDrive, Cpu
} from 'lucide-react'
import type { ScenarioConfig, ValidationIssue } from '../services/prompt'

interface ScenarioCardProps {
  scenario: Partial<ScenarioConfig>
  compact?: boolean
  showValidation?: boolean
  showEstimate?: boolean
  className?: string
}

const WEATHER_ICONS: Record<string, string> = {
  Clear: '☀️', Rain: '🌧', Fog: '🌫', Snow: '❄️', Storm: '⛈', Overcast: '☁️',
}
const TIME_ICONS: Record<string, string> = {
  Day: '☀️', Night: '🌙', Dusk: '🌅', Dawn: '🌄',
}
const SENSOR_COLORS: Record<string, string> = {
  rgb: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  lidar: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  radar: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  depth: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  semantic: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  instance: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
  optical_flow: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
}

function ConfidenceBar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100)
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-slate-600'
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-500 w-16 truncate">{label}</span>
      <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-[10px] font-mono ${pct >= 80 ? 'text-emerald-400' : pct >= 50 ? 'text-amber-400' : 'text-slate-500'}`}>
        {pct}%
      </span>
    </div>
  )
}

function IssueRow({ issue }: { issue: ValidationIssue }) {
  const styles = {
    error:   { icon: <AlertCircle size={11} className="text-red-400 shrink-0" />,   text: 'text-red-300',   bg: 'bg-red-500/10 border-red-500/20' },
    warning: { icon: <AlertCircle size={11} className="text-amber-400 shrink-0" />, text: 'text-amber-300', bg: 'bg-amber-500/10 border-amber-500/20' },
    info:    { icon: <Info size={11} className="text-blue-400 shrink-0" />,         text: 'text-blue-300',  bg: 'bg-blue-500/10 border-blue-500/20' },
  }[issue.level] || { icon: null, text: 'text-slate-400', bg: 'bg-slate-800' }

  return (
    <div className={`flex items-start gap-1.5 px-2 py-1.5 rounded-lg border text-xs ${styles.bg}`}>
      {styles.icon}
      <span className={styles.text}>{issue.message}</span>
    </div>
  )
}

export default function ScenarioCard({
  scenario, compact = false, showValidation = true, showEstimate = false, className = ''
}: ScenarioCardProps) {
  const [expanded, setExpanded] = useState(!compact)
  const [showJson, setShowJson] = useState(false)

  const totalVehicles = scenario.vehicles
    ? Object.values(scenario.vehicles).reduce((a, b) => a + b, 0)
    : 0

  const hasConfidence = scenario.confidence && Object.keys(scenario.confidence).length > 0
  const validationIssues = [
    ...(scenario.validation?.errors ?? []),
    ...(scenario.validation?.warnings ?? []),
    ...(scenario.validation?.infos ?? []),
  ]

  return (
    <div className={`bg-slate-800/60 border border-slate-700/50 rounded-xl overflow-hidden ${className}`}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-slate-700/30 transition-colors"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center gap-2.5">
          <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-brand-600/20">
            <MapPin size={12} className="text-brand-400" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-200">
              {scenario.carla_map ?? scenario.road_type ?? 'Scenario'}
              {scenario.translation && (
                <span className="ml-1.5 text-[10px] text-slate-500 font-normal">
                  ({scenario.translation.source})
                </span>
              )}
            </p>
            <p className="text-[10px] text-slate-500">
              {[scenario.weather, scenario.time_of_day, scenario.traffic_density].filter(Boolean).join(' · ') || 'Parsed configuration'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {scenario.validation_passed === true && (
            <CheckCircle2 size={13} className="text-emerald-400" />
          )}
          {scenario.validation?.errors && scenario.validation.errors.length > 0 && (
            <span className="flex items-center gap-1 text-[10px] text-red-400 bg-red-500/10 border border-red-500/20 rounded-full px-2 py-0.5">
              <AlertCircle size={9} /> {scenario.validation.errors.length} error{scenario.validation.errors.length > 1 ? 's' : ''}
            </span>
          )}
          {expanded ? <ChevronUp size={13} className="text-slate-500" /> : <ChevronDown size={13} className="text-slate-500" />}
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-slate-700/40 pt-3">

          {/* Quick stats row */}
          <div className="grid grid-cols-4 gap-2">
            {[
              { icon: '🌍', label: 'Map', value: scenario.carla_map ?? '—' },
              { icon: WEATHER_ICONS[scenario.weather ?? ''] ?? '—', label: 'Weather', value: scenario.weather ?? '—' },
              { icon: TIME_ICONS[scenario.time_of_day ?? ''] ?? '—', label: 'Time', value: scenario.time_of_day ?? '—' },
              { icon: '📸', label: 'Frames', value: scenario.frames?.toString() ?? '—' },
            ].map(({ icon, label, value }) => (
              <div key={label} className="bg-slate-900/50 rounded-lg p-2 text-center">
                <p className="text-base leading-none mb-1">{icon}</p>
                <p className="text-[9px] text-slate-500 mb-0.5">{label}</p>
                <p className="text-[11px] font-semibold text-slate-200 truncate">{value}</p>
              </div>
            ))}
          </div>

          {/* Sensors */}
          {scenario.sensors && scenario.sensors.length > 0 && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">Sensors</p>
              <div className="flex flex-wrap gap-1.5">
                {scenario.sensors.map(s => (
                  <span
                    key={s}
                    className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${SENSOR_COLORS[s] ?? 'bg-slate-700/50 text-slate-400 border-slate-700'}`}
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Vehicle mix */}
          {scenario.vehicles && totalVehicles > 0 && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">
                <Car size={9} className="inline mr-1" />
                Vehicles ({totalVehicles}) · Pedestrians ({scenario.pedestrians ?? 0})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(scenario.vehicles)
                  .filter(([, v]) => v > 0)
                  .map(([k, v]) => (
                    <span key={k} className="text-[10px] bg-slate-700/50 text-slate-300 px-2 py-0.5 rounded-full">
                      {v} {k}
                    </span>
                  ))}
              </div>
            </div>
          )}

          {/* Confidence bars */}
          {hasConfidence && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">Confidence</p>
              <div className="space-y-1">
                {Object.entries(scenario.confidence!).map(([key, val]) => (
                  <ConfidenceBar key={key} label={key} value={val} />
                ))}
              </div>
            </div>
          )}

          {/* Optimizer changes */}
          {scenario.optimizer_changes && scenario.optimizer_changes.length > 0 && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">
                ✨ Optimizer applied {scenario.optimizer_changes.length} change{scenario.optimizer_changes.length > 1 ? 's' : ''}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {scenario.optimizer_changes.map((c, i) => (
                  <span key={i} className="text-[10px] bg-violet-500/10 text-violet-300 border border-violet-500/20 px-2 py-0.5 rounded-full">
                    {c.field}: {c.to_value}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Translation note */}
          {scenario.translation && (
            <div className={`text-[10px] px-2 py-1.5 rounded-lg border ${
              scenario.translation.confidence >= 0.8
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                : scenario.translation.confidence >= 0.6
                  ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                  : 'bg-slate-700/50 text-slate-400 border-slate-700'
            }`}>
              🗺 {scenario.translation.note}
            </div>
          )}

          {/* Validation */}
          {showValidation && validationIssues.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Validation</p>
              {validationIssues.map((issue, i) => (
                <IssueRow key={i} issue={issue} />
              ))}
            </div>
          )}

          {/* Estimate */}
          {showEstimate && scenario.estimate && (
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-900/50 rounded-lg p-2">
                <p className="text-[9px] text-slate-500 mb-0.5 flex items-center gap-1"><Clock size={9} /> Duration</p>
                <p className="text-[11px] font-semibold text-slate-200">
                  ~{Math.round(scenario.estimate.estimated_duration_seconds)}s
                </p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-2">
                <p className="text-[9px] text-slate-500 mb-0.5 flex items-center gap-1"><HardDrive size={9} /> Disk</p>
                <p className="text-[11px] font-semibold text-slate-200">
                  ~{Math.round(scenario.estimate.estimated_disk_mb)} MB
                </p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-2">
                <p className="text-[9px] text-slate-500 mb-0.5 flex items-center gap-1"><Cpu size={9} /> GPU VRAM</p>
                <p className="text-[11px] font-semibold text-slate-200">
                  ~{Math.round(scenario.estimate.estimated_gpu_vram_mb)} MB
                </p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-2">
                <p className="text-[9px] text-slate-500 mb-0.5 flex items-center gap-1"><Gauge size={9} /> Format</p>
                <p className="text-[11px] font-semibold text-slate-200 uppercase">
                  {scenario.export_format ?? '—'}
                </p>
              </div>
            </div>
          )}

          {/* Raw JSON toggle */}
          <button
            onClick={() => setShowJson(v => !v)}
            className="flex items-center gap-1.5 text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
          >
            {showJson ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            {showJson ? 'Hide' : 'Show'} raw JSON
          </button>
          {showJson && (
            <pre className="bg-slate-900/80 border border-slate-700/50 rounded-lg p-3 text-[10px] text-slate-400 overflow-x-auto max-h-48">
              {JSON.stringify(scenario, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
