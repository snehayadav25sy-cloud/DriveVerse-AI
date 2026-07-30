/**
 * PromptBar.tsx — Build 3: AI Prompt Engine v1.0
 * ================================================
 * A natural-language input that:
 *   1. Accepts free-text scenario descriptions
 *   2. Calls POST /prompt/parse for a live preview (debounced)
 *   3. Shows per-field confidence chips for map / sensors / frames / format
 *   4. Has an "Apply to Form" callback so GenerateForm can be pre-filled
 *   5. Has a "Submit Now" button that calls /prompt/parse-and-submit
 *
 * Styled to match the existing dark-glass design system.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Sparkles, Loader2, ChevronDown, ChevronUp, CheckCircle2,
  AlertCircle, Lightbulb, ArrowRight, Zap, X
} from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { parsePrompt } from '../services/prompt'
import type { PromptParseResult } from '../services/prompt'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AppliedConfig {
  map: string
  sensors: string[]
  frames: number
  export_format: 'kitti' | 'coco' | 'nuscenes'
}

interface PromptBarProps {
  /** Called when the user clicks "Apply to Form" */
  onApply?: (config: AppliedConfig) => void
  /** Project list for the submit-and-create flow */
  projects?: Array<{ id: string; name: string }>
}

// ── Example prompts carousel ─────────────────────────────────────────────────

const EXAMPLES = [
  'Urban intersection, RGB and LiDAR, 500 frames, KITTI',
  'Highway merge with full sensor suite, 1000 frames, nuScenes',
  'Short suburban clip with depth camera, 200 frames',
  'Town02 residential, camera and radar, 750 frames, COCO',
  'Long rural road capture, all sensors, 2000 frames',
  'Quick urban scene, vision only, 100 frames',
]

// ── Confidence chip component ─────────────────────────────────────────────────

function ConfidenceChip({
  label, value, detected,
}: { label: string; value: number; detected: boolean }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.8
    ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
    : value >= 0.5
    ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
    : 'text-slate-400 bg-slate-800/60 border-slate-700'
  const icon = value >= 0.8 ? (
    <CheckCircle2 size={10} className="text-emerald-400" />
  ) : value >= 0.5 ? (
    <AlertCircle size={10} className="text-amber-400" />
  ) : (
    <AlertCircle size={10} className="text-slate-500" />
  )
  return (
    <div className={`flex items-center gap-1 px-2 py-1 rounded-lg border text-[10px] font-semibold ${color}`}>
      {icon}
      <span>{label}</span>
      {detected && <span className="opacity-60">({pct}%)</span>}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function PromptBar({ onApply, projects = [] }: PromptBarProps) {
  const [prompt, setPrompt]       = useState('')
  const [expanded, setExpanded]   = useState(false)
  const [result, setResult]       = useState<PromptParseResult | null>(null)
  const [appliedMsg, setApplied]  = useState(false)
  const [exampleIdx, setExample]  = useState(0)
  const textareaRef               = useRef<HTMLTextAreaElement>(null)
  const debounceRef               = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Auto-rotate example placeholder
  useEffect(() => {
    const id = setInterval(
      () => setExample(i => (i + 1) % EXAMPLES.length),
      4000,
    )
    return () => clearInterval(id)
  }, [])

  // Parse mutation
  const parseMutation = useMutation({
    mutationFn: parsePrompt,
    onSuccess: (data) => {
      setResult(data)
      setExpanded(true)
    },
  })

  // Debounced parse on input change (500 ms)
  const debouncedParse = useCallback((value: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (value.trim().length < 8) {
      setResult(null)
      return
    }
    debounceRef.current = setTimeout(() => {
      parseMutation.mutate(value)
    }, 500)
  }, [parseMutation])

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const v = e.target.value
    setPrompt(v)
    setApplied(false)
    debouncedParse(v)
  }

  const handleExampleClick = (ex: string) => {
    setPrompt(ex)
    setApplied(false)
    parseMutation.mutate(ex)
    textareaRef.current?.focus()
  }

  const handleApply = () => {
    if (!result || !onApply) return
    onApply({
      map:           result.map,
      sensors:       result.sensors,
      frames:        result.frames,
      export_format: result.export_format as 'kitti' | 'coco' | 'nuscenes',
    })
    setApplied(true)
    setTimeout(() => setApplied(false), 3000)
  }

  const handleClear = () => {
    setPrompt('')
    setResult(null)
    setExpanded(false)
    setApplied(false)
    textareaRef.current?.focus()
  }

  const overallConfidence = result
    ? Object.values(result.confidence).reduce((a, b) => a + b, 0) / 4
    : 0

  return (
    <div className="card p-5 space-y-4 border-brand-500/20 ring-1 ring-brand-500/10">
      {/* Header */}
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600/30 to-violet-600/30 border border-brand-500/20 flex-shrink-0">
          <Sparkles size={16} className="text-brand-400" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
            AI Prompt Engine
            <span className="px-1.5 py-0.5 rounded-md bg-brand-500/15 text-brand-400 text-[9px] font-bold uppercase tracking-wide border border-brand-500/20">
              v1.0
            </span>
          </h3>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Describe a scenario in plain English — we'll configure it automatically.
          </p>
        </div>
      </div>

      {/* Textarea */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={prompt}
          onChange={handleChange}
          rows={3}
          placeholder={`e.g. "${EXAMPLES[exampleIdx]}"`}
          className="w-full bg-slate-900/70 border border-slate-700 rounded-xl px-4 pt-3 pb-8 text-sm text-slate-200 resize-none focus:outline-none focus:border-brand-500/60 focus:ring-1 focus:ring-brand-500/30 transition-all placeholder:text-slate-600 placeholder:text-xs leading-relaxed"
        />
        {/* Bottom toolbar inside textarea */}
        <div className="absolute bottom-2.5 left-3 right-3 flex items-center justify-between pointer-events-none">
          <span className="text-[9px] text-slate-600 font-mono pointer-events-none">
            {prompt.length}/1000 chars
          </span>
          <div className="flex items-center gap-1.5 pointer-events-auto">
            {prompt && (
              <button
                type="button"
                onClick={handleClear}
                className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-slate-500 hover:text-slate-300 transition-colors text-[10px]"
              >
                <X size={9} /> Clear
              </button>
            )}
            {parseMutation.isPending && (
              <span className="flex items-center gap-1 text-[10px] text-brand-400">
                <Loader2 size={10} className="animate-spin" /> Parsing…
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Example chips */}
      <div className="flex flex-wrap gap-1.5">
        <span className="text-[10px] text-slate-600 font-semibold uppercase tracking-wider self-center mr-1">
          Try:
        </span>
        {EXAMPLES.slice(0, 3).map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => handleExampleClick(ex)}
            className="text-[10px] px-2 py-1 rounded-lg border border-slate-700 bg-slate-800/60 text-slate-400 hover:text-slate-200 hover:border-brand-500/40 hover:bg-brand-500/10 transition-all truncate max-w-[200px]"
          >
            {ex}
          </button>
        ))}
      </div>

      {/* Parsed result panel */}
      {result && (
        <div className="border-t border-slate-800 pt-4 space-y-3 animate-slide-up">
          {/* Toggle */}
          <button
            type="button"
            onClick={() => setExpanded(e => !e)}
            className="w-full flex items-center justify-between text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Lightbulb size={12} className="text-amber-400" />
              Parsed Configuration
              <span className="px-1.5 py-0.5 rounded-full bg-slate-800 text-[9px] font-mono">
                {Math.round(overallConfidence * 100)}% confidence
              </span>
            </span>
            {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>

          {expanded && (
            <div className="space-y-3 animate-fade-in">
              {/* Config preview grid */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                {[
                  { label: 'Map',     value: result.map,                    conf: result.confidence.map },
                  { label: 'Format',  value: result.export_format.toUpperCase(), conf: result.confidence.export_format },
                  { label: 'Frames',  value: `${result.frames} frames`,    conf: result.confidence.frames },
                  { label: 'Sensors', value: result.sensors.join(', '),    conf: result.confidence.sensors },
                ].map(({ label, value, conf }) => (
                  <div
                    key={label}
                    className="flex flex-col gap-1 p-2.5 rounded-xl bg-slate-900/60 border border-slate-800"
                  >
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">{label}</span>
                    <span className="text-slate-200 font-semibold text-[11px] truncate">{value}</span>
                    <div className="w-full h-1 rounded-full bg-slate-800 mt-0.5">
                      <div
                        className={`h-1 rounded-full transition-all ${
                          conf >= 0.8 ? 'bg-emerald-500' :
                          conf >= 0.5 ? 'bg-amber-500' : 'bg-slate-600'
                        }`}
                        style={{ width: `${conf * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Confidence chips */}
              <div className="flex flex-wrap gap-1.5">
                <ConfidenceChip label="Map"    value={result.confidence.map}           detected={result.confidence.map > 0} />
                <ConfidenceChip label="Sensors" value={result.confidence.sensors}       detected={result.confidence.sensors > 0} />
                <ConfidenceChip label="Frames" value={result.confidence.frames}         detected={result.confidence.frames > 0} />
                <ConfidenceChip label="Format" value={result.confidence.export_format}  detected={result.confidence.export_format > 0} />
              </div>

              {/* Unrecognised tokens */}
              {result.unrecognised_tokens.length > 0 && (
                <div className="flex items-start gap-1.5 text-[10px] text-amber-400/80 bg-amber-500/5 border border-amber-500/15 rounded-lg px-3 py-2">
                  <AlertCircle size={11} className="mt-0.5 flex-shrink-0" />
                  <span>
                    Unrecognised: <span className="font-mono">{result.unrecognised_tokens.join(', ')}</span>
                    {' '}— ignored, defaults used.
                  </span>
                </div>
              )}

              {/* CTA: Apply to form */}
              {onApply && (
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleApply}
                    disabled={appliedMsg}
                    className="btn-primary flex-1 justify-center py-2.5 text-xs disabled:opacity-60"
                  >
                    {appliedMsg ? (
                      <><CheckCircle2 size={13} /> Applied to Form!</>
                    ) : (
                      <><ArrowRight size={13} /> Apply to Form</>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => setExpanded(false)}
                    className="btn-secondary py-2.5 px-3 text-xs"
                  >
                    <ChevronUp size={13} />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Parse error state */}
      {parseMutation.isError && (
        <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2">
          <AlertCircle size={12} />
          Parse failed — check that the backend is running on port 8000.
        </div>
      )}

      {/* AI Engine badge */}
      <div className="flex items-center gap-1.5 text-[9px] text-slate-600 pt-1 border-t border-slate-800/60">
        <Zap size={9} className="text-slate-700" />
        <span>Zero-shot rule-based NLP · No external API key required</span>
      </div>
    </div>
  )
}
