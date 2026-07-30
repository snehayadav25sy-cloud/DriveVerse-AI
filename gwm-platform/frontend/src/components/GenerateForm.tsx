import { useForm, Controller } from 'react-hook-form'
import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Loader2, Sparkles, CheckCircle2, Map, Film, Layers, FileJson } from 'lucide-react'
import { generateDataset, VALID_MAPS } from '../services/generator'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import type { Job } from '../types'

// ── Sensor options ──────────────────────────────────────────────────────────
const SENSOR_OPTIONS = [
  {
    key: 'rgb',
    label: 'RGB Camera',
    desc: '1280×720 · 90° FOV · 10 FPS',
    icon: <Film size={14} />,
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10 border-emerald-500/30',
    activeBg: 'bg-emerald-500/20 border-emerald-400',
  },
  {
    key: 'lidar',
    label: 'LiDAR',
    desc: '32 ch · 100 m · 10 Hz · 100k pts/s',
    icon: <Layers size={14} />,
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/10 border-cyan-500/30',
    activeBg: 'bg-cyan-500/20 border-cyan-400',
  },
  {
    key: 'radar',
    label: 'Radar',
    desc: '30° hFOV · 100 m range · Range & Velocity',
    icon: <Layers size={14} />,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/30',
    activeBg: 'bg-amber-500/20 border-amber-400',
  },
  {
    key: 'depth',
    label: 'Depth Camera',
    desc: '800×600 · 16-bit uint16 depth in cm',
    icon: <Film size={14} />,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10 border-blue-500/30',
    activeBg: 'bg-blue-500/20 border-blue-400',
  },
  {
    key: 'semantic',
    label: 'Semantic Segmentation',
    desc: '800×600 · Per-pixel class ID masks',
    icon: <Film size={14} />,
    color: 'text-purple-400',
    bg: 'bg-purple-500/10 border-purple-500/30',
    activeBg: 'bg-purple-500/20 border-purple-400',
  },
  {
    key: 'instance',
    label: 'Instance Segmentation',
    desc: '800×600 · Unique per-actor instance IDs',
    icon: <Film size={14} />,
    color: 'text-pink-400',
    bg: 'bg-pink-500/10 border-pink-500/30',
    activeBg: 'bg-pink-500/20 border-pink-400',
  },
  {
    key: 'optical_flow',
    label: 'Optical Flow',
    desc: '800×600 · 2D pixel motion vectors (.npy)',
    icon: <Film size={14} />,
    color: 'text-orange-400',
    bg: 'bg-orange-500/10 border-orange-500/30',
    activeBg: 'bg-orange-500/20 border-orange-400',
  },
]

// ── Export formats ─────────────────────────────────────────────────────────
const FORMAT_OPTIONS = [
  {
    key: 'kitti',
    label: 'KITTI',
    desc: 'Standard camera/velodyne annotation layout',
  },
  {
    key: 'coco',
    label: 'COCO JSON',
    desc: 'Instances & categories annotation format',
  },
  {
    key: 'nuscenes',
    label: 'nuScenes',
    desc: 'AV sweep and scene synchronization metadata schema',
  },
]

// ── Zod schema ───────────────────────────────────────────────────────────────
const schema = z.object({
  project_id:    z.string().min(1, 'Select a project'),
  map:           z.enum(['Town01', 'Town02', 'Town03']),
  sensors:       z.array(z.string()).min(1, 'Select at least one sensor'),
  frames:        z.number().int().min(25).max(2000),
  export_format: z.enum(['kitti', 'coco', 'nuscenes']),
})
type FormData = z.infer<typeof schema>

interface GenerateFormProps {
  onJobCreated?: (job: Job) => void
  /** Optional: pre-filled values injected by the AI Prompt Engine */
  initialValues?: {
    map?: string
    sensors?: string[]
    frames?: number
    export_format?: string
  }
  /** Optional: exposes the loaded project list to the parent */
  onProjectsLoaded?: (projects: Array<{ id: string; name: string }>) => void
}

export default function GenerateForm({ onJobCreated, initialValues, onProjectsLoaded }: GenerateFormProps) {
  const navigate = useNavigate()

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await api.get('/projects')
      return res.data
    },
  })

  // Expose the loaded project list to the parent (for PromptBar submit flow)
  useEffect(() => {
    if (projects.length > 0) onProjectsLoaded?.(projects as Array<{ id: string; name: string }>)
  }, [projects, onProjectsLoaded])

  const { register, handleSubmit, watch, control, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { map: 'Town01', sensors: ['rgb'], frames: 500, export_format: 'kitti' },
  })

  // When PromptBar injects values, reset the form to those values
  useEffect(() => {
    if (!initialValues) return
    reset(prev => ({
      ...prev,
      ...(initialValues.map           && { map: initialValues.map as 'Town01' | 'Town02' | 'Town03' }),
      ...(initialValues.sensors?.length && { sensors: initialValues.sensors }),
      ...(initialValues.frames          && { frames: initialValues.frames }),
      ...(initialValues.export_format   && { export_format: initialValues.export_format as 'kitti' | 'coco' | 'nuscenes' }),
    }))
  }, [initialValues, reset])

  const frames = watch('frames')
  const selectedSensors = watch('sensors') ?? []
  const exportFormat = watch('export_format')

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      generateDataset({
        project_id: data.project_id,
        map: data.map,
        sensors: data.sensors,
        frames: data.frames,
        export_format: data.export_format,
      }),
    onSuccess: (job) => {
      onJobCreated?.(job)
      setTimeout(() => navigate('/jobs'), 1000)
    },
  })

  const onSubmit = (data: FormData) => mutation.mutate(data)

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Project */}
      <div>
        <label className="label">Project</label>
        <select className="select" {...register('project_id')}>
          <option value="">— Select a project —</option>
          {projects.map((p: any) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
        {errors.project_id && <p className="text-xs text-red-400 mt-1">{errors.project_id.message}</p>}
      </div>

      {/* Map */}
      <div>
        <label className="label flex items-center gap-1.5"><Map size={13} /> CARLA Map</label>
        <select className="select" {...register('map')}>
          {VALID_MAPS.map(m => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
        {errors.map && <p className="text-xs text-red-400 mt-1">{errors.map.message}</p>}
      </div>

      {/* Sensors — multi-select checkboxes */}
      <div>
        <label className="label flex items-center gap-1.5"><Layers size={13} /> Sensors</label>
        <p className="text-[11px] text-slate-500 mb-3">Select one or more sensors. Selected sensors capture in synchronous lockstep.</p>
        <Controller
          control={control}
          name="sensors"
          render={({ field }) => (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {SENSOR_OPTIONS.map(opt => {
                const isActive = field.value?.includes(opt.key as any)
                return (
                  <button
                    key={opt.key}
                    type="button"
                    onClick={() => {
                      const current = field.value ?? []
                      const next = isActive
                        ? current.filter(s => s !== opt.key)
                        : [...current, opt.key as 'rgb' | 'lidar']
                      field.onChange(next)
                    }}
                    className={`
                      relative flex flex-col items-start gap-1.5 p-4 rounded-xl border-2 text-left
                      transition-all duration-200 cursor-pointer select-none
                      ${isActive ? opt.activeBg : opt.bg + ' opacity-60 hover:opacity-90'}
                    `}
                  >
                    {/* Checkmark */}
                    <span className={`absolute top-2.5 right-2.5 h-4 w-4 rounded-full border-2 flex items-center justify-center transition-all
                      ${isActive ? 'border-current bg-current' : 'border-slate-600 bg-transparent'}`}>
                      {isActive && <CheckCircle2 size={10} className="text-slate-950" />}
                    </span>
                    <span className={`${opt.color} flex items-center gap-1.5 font-semibold text-sm`}>
                      {opt.icon} {opt.label}
                    </span>
                    <span className="text-[10px] text-slate-500 leading-tight">{opt.desc}</span>
                  </button>
                )
              })}
            </div>
          )}
        />
        {errors.sensors && <p className="text-xs text-red-400 mt-2">{errors.sensors.message as string}</p>}
      </div>

      {/* Export Format */}
      <div>
        <label className="label flex items-center gap-1.5"><FileJson size={13} /> Export Format</label>
        <select className="select" {...register('export_format')}>
          {FORMAT_OPTIONS.map(opt => (
            <option key={opt.key} value={opt.key}>
              {opt.label} — {opt.desc}
            </option>
          ))}
        </select>
        {errors.export_format && <p className="text-xs text-red-400 mt-1">{errors.export_format.message}</p>}

        {/* Output preview */}
        {selectedSensors.length > 0 && (
          <div className="mt-4 px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 font-mono space-y-2">
            <div className="text-slate-300 font-semibold border-b border-slate-800 pb-1.5">ZIP ARCHIVE PREVIEW</div>
            <div className="space-y-1">
              <div>Canonical Internal Output:</div>
              <div className="pl-4 flex flex-wrap gap-2 text-xs">
                {selectedSensors.includes('rgb') && <span className="bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20">images/</span>}
                {selectedSensors.includes('lidar') && <span className="bg-cyan-500/10 text-cyan-400 px-1.5 py-0.5 rounded border border-cyan-500/20">pointcloud/</span>}
                {selectedSensors.includes('radar') && <span className="bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded border border-amber-500/20">radar.csv</span>}
                {selectedSensors.includes('depth') && <span className="bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded border border-blue-500/20">depth/</span>}
                {selectedSensors.includes('semantic') && <span className="bg-purple-500/10 text-purple-400 px-1.5 py-0.5 rounded border border-purple-500/20">semantic/</span>}
                {selectedSensors.includes('instance') && <span className="bg-pink-500/10 text-pink-400 px-1.5 py-0.5 rounded border border-pink-500/20">instance/</span>}
                {selectedSensors.includes('optical_flow') && <span className="bg-orange-500/10 text-orange-400 px-1.5 py-0.5 rounded border border-orange-500/20">optical_flow/</span>}
                <span className="bg-brand-500/10 text-brand-400 px-1.5 py-0.5 rounded border border-brand-500/20">labels/</span>
                <span className="bg-brand-500/10 text-brand-400 px-1.5 py-0.5 rounded border border-brand-500/20">metadata/</span>
                <span className="bg-brand-500/10 text-brand-400 px-1.5 py-0.5 rounded border border-brand-500/20">calibration/</span>
                <span className="bg-brand-500/10 text-brand-400 px-1.5 py-0.5 rounded border border-brand-500/20">sync_report.json</span>
              </div>
            </div>
            {exportFormat === 'kitti' && (
              <div className="space-y-1 pt-1.5 border-t border-slate-800/50">
                <div>KITTI Compliant Export:</div>
                <div className="pl-4 flex flex-wrap gap-2 text-xs">
                  {selectedSensors.includes('rgb') && <span className="bg-violet-500/10 text-violet-400 px-1.5 py-0.5 rounded border border-violet-500/20">kitti/image_2/</span>}
                  {selectedSensors.includes('lidar') && <span className="bg-violet-500/10 text-violet-400 px-1.5 py-0.5 rounded border border-violet-500/20">kitti/velodyne/</span>}
                  <span className="bg-violet-500/10 text-violet-400 px-1.5 py-0.5 rounded border border-violet-500/20">kitti/label_2/</span>
                  <span className="bg-violet-500/10 text-violet-400 px-1.5 py-0.5 rounded border border-violet-500/20">kitti/calib/</span>
                </div>
              </div>
            )}
            {exportFormat === 'nuscenes' && (
              <div className="space-y-1 pt-1.5 border-t border-slate-800/50">
                <div>nuScenes Compliant Export:</div>
                <div className="pl-4 flex flex-wrap gap-2 text-xs">
                  <span className="bg-violet-500/10 text-violet-400 px-1.5 py-0.5 rounded border border-violet-500/20">nuscenes/v1.0-mini/scene.json</span>
                  <span className="bg-violet-500/10 text-violet-400 px-1.5 py-0.5 rounded border border-violet-500/20">nuscenes/v1.0-mini/sample.json</span>
                  <span className="bg-violet-500/10 text-violet-400 px-1.5 py-0.5 rounded border border-violet-500/20">nuscenes/v1.0-mini/sample_data.json</span>
                </div>
              </div>
            )}
            {exportFormat === 'coco' && (
              <div className="space-y-1 pt-1.5 border-t border-slate-800/50">
                <div>COCO Compliant Export:</div>
                <div className="pl-4 flex flex-wrap gap-2 text-xs">
                  <span className="bg-violet-500/10 text-violet-400 px-1.5 py-0.5 rounded border border-violet-500/20">coco/instances_default.json</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Frame count */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="label mb-0 flex items-center gap-1.5"><Film size={13} /> Frame Count</label>
          <span className="text-xs font-bold text-brand-400">{frames} frames · ~{Math.round(frames / 10)}s</span>
        </div>
        <input
          type="range" min={50} max={2000} step={50}
          className="w-full accent-brand-500 cursor-pointer"
          {...register('frames', { valueAsNumber: true })}
        />
        <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
          <span>50</span><span>500 (default)</span><span>2000</span>
        </div>
        <input
          type="number" min={50} max={2000}
          className="mt-2 w-full px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-brand-500 transition-all"
          {...register('frames', { valueAsNumber: true })}
          placeholder="Or type exact frame count..."
        />
        {errors.frames && <p className="text-xs text-red-400 mt-1">{errors.frames.message}</p>}
      </div>

      {/* Submit */}
      <div className="pt-2">
        {mutation.isSuccess && (
          <div className="flex items-center gap-2 text-emerald-400 text-sm mb-3 animate-fade-in">
            <CheckCircle2 size={16} />
            Job queued! Redirecting to Jobs… <span className="font-mono text-xs">{mutation.data?.id?.slice(0, 8)}…</span>
          </div>
        )}
        {mutation.isError && (
          <p className="text-sm text-red-400 mb-3 animate-fade-in">
            ❌ Failed — check that the backend is running on port 8000.
          </p>
        )}
        <button
          type="submit"
          disabled={mutation.isPending || selectedSensors.length === 0}
          className="btn-primary w-full justify-center py-3 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {mutation.isPending
            ? <><Loader2 size={16} className="animate-spin" /> Queueing job…</>
            : <><Sparkles size={16} /> Generate Dataset ({selectedSensors.join(' + ').toUpperCase() || '—'})</>}
        </button>
      </div>
    </form>
  )
}
