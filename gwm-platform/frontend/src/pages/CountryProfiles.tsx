import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Navbar from '../components/Navbar'
import {
  fetchCountries,
  createCountry,
  updateCountry,
  deleteCountry,
  getCountry,
} from '../services/countries'
import { FileCode, Check, AlertTriangle, Trash2, Edit3, Plus, X, Globe } from 'lucide-react'

const FLAG_MAP: Record<string, string> = {
  india: '🇮🇳',
  mumbai: '🇮🇳',
  usa: '🇺🇸',
  japan: '🇯🇵',
  dubai: '🇦🇪',
  germany: '🇩🇪',
  uk: '🇬🇧',
  mauritius: '🇲🇺'
}

export default function CountryProfiles() {
  const queryClient = useQueryClient()
  const [isEditorOpen, setIsEditorOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [yamlInput, setYamlInput] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  // 1. Fetch country profiles
  const { data: countries = [], isLoading } = useQuery({
    queryKey: ['countries'],
    queryFn: fetchCountries
  })

  // 2. Mutations
  const saveMutation = useMutation({
    mutationFn: async () => {
      if (editingId) {
        return updateCountry(editingId, yamlInput)
      } else {
        return createCountry(yamlInput)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['countries'] })
      setSuccessMsg(editingId ? 'Profile updated successfully!' : 'Country profile created successfully!')
      setErrorMsg('')
      setTimeout(() => {
        setIsEditorOpen(false)
        setEditingId(null)
        setYamlInput('')
        setSuccessMsg('')
      }, 1000)
    },
    onError: (err: any) => {
      setErrorMsg(err?.response?.data?.detail || 'An error occurred while compiling the YAML.')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: deleteCountry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['countries'] })
    }
  })

  const handleOpenAdd = () => {
    setEditingId(null)
    setYamlInput(`# Define custom geographic scenario presets
id: custom_country
version: 1.0.0
schema_version: 1
extends: usa
author: DriveVerse
updated: "2026-08-06"

supports:
  auto_rickshaw: false
  tram: false
  train: false

rules:
  drive_side: right
  speed_limits:
    highway: 120
    urban: 60
  behavior:
    aggressiveness: 0.6
    horn_frequency: 0.2
    stopping_distance_m: 3.5

vehicle_mix:
  sedan: 0.50
  suv: 0.30
  motorcycle: 0.10
  truck: 0.10
`)
    setErrorMsg('')
    setSuccessMsg('')
    setIsEditorOpen(true)
  }

  const handleOpenEdit = async (id: string) => {
    try {
      const rawProfile = await getCountry(id)
      setYamlInput(JSON.stringify(rawProfile, null, 2))
      setEditingId(id)
      setErrorMsg('')
      setSuccessMsg('')
      setIsEditorOpen(true)
    } catch (e: any) {
      setErrorMsg('Failed to fetch country YAML details.')
    }
  }

  const handleDelete = (id: string) => {
    if (confirm(`Are you sure you want to delete the country profile '${id}'?`)) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="animate-fade-in text-white min-h-screen bg-slate-950">
      <Navbar title="Country Management" subtitle="Manage geographic configurations, driving profiles, and simulator fallback mappings" />

      <div className="p-8 space-y-8 max-w-7xl mx-auto">
        {/* Top Controls */}
        <div className="flex justify-between items-center border-b border-slate-800/80 pb-5">
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Globe className="text-brand-400" size={20} />
              Geographic Registry
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Active profiles compile reality constraints (LHT/RHT, vehicle distribution) into resolved simulator assets.
            </p>
          </div>
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-brand-600 to-cyan-500 hover:opacity-90 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-brand-500/20"
          >
            <Plus size={16} /> Import Profile (YAML)
          </button>
        </div>

        {/* Profiles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
            <div className="col-span-full text-center text-slate-500 py-16">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500 mx-auto mb-4"></div>
              Loading registered countries...
            </div>
          ) : countries.length === 0 ? (
            <div className="col-span-full text-center text-slate-500 py-16 bg-slate-900/40 rounded-2xl border border-dashed border-slate-800">
              No registered profiles found. Click "Import Profile" to add.
            </div>
          ) : (
            countries.map((c) => (
              <div key={c.id} className="card-hover p-6 flex flex-col justify-between border border-slate-800/60 bg-slate-900/60 backdrop-blur-md rounded-2xl gap-5 relative overflow-hidden group">
                {/* Background accent */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/5 rounded-full blur-2xl group-hover:bg-brand-500/10 transition-all"></div>

                <div className="space-y-4">
                  {/* Title & Badge */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="text-3xl">{FLAG_MAP[c.id.toLowerCase()] ?? '🌍'}</span>
                      <div>
                        <h3 className="font-bold text-white text-base capitalize">{c.id}</h3>
                        <p className="text-xs text-slate-500">Version {c.version}</p>
                      </div>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${c.drive_side === 'left' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-brand-500/10 text-brand-400 border border-brand-500/20'}`}>
                      {c.drive_side === 'left' ? 'Left Drive (LHT)' : 'Right Drive (RHT)'}
                    </span>
                  </div>

                  {/* Supports Details */}
                  <div className="space-y-2 pt-2 border-t border-slate-800/60 text-xs">
                    <p className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Asset Capabilities</p>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex items-center gap-1.5 text-slate-400">
                        {c.supports.auto_rickshaw ? <Check size={12} className="text-emerald-400" /> : <X size={12} className="text-rose-400" />}
                        <span>Auto-Rickshaw</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-400">
                        {c.supports.snow_accumulation ? <Check size={12} className="text-emerald-400" /> : <X size={12} className="text-rose-400" />}
                        <span>Snow Accum.</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-400">
                        {c.supports.tram ? <Check size={12} className="text-emerald-400" /> : <X size={12} className="text-rose-400" />}
                        <span>Trams</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-400">
                        {c.supports.train ? <Check size={12} className="text-emerald-400" /> : <X size={12} className="text-rose-400" />}
                        <span>Trains</span>
                      </div>
                    </div>
                  </div>

                  {/* Vehicle Mix Summary */}
                  <div className="space-y-1.5">
                    <p className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] mb-1">Supported Classes</p>
                    <div className="flex flex-wrap gap-1">
                      {c.vehicle_classes.map((cls) => (
                        <span key={cls} className="px-2 py-0.5 rounded-lg text-[10px] font-semibold bg-slate-800 text-slate-300 capitalize border border-slate-700/55">
                          {cls.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Weather Presets */}
                  <div className="space-y-1.5">
                    <p className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] mb-1">Weather Presets</p>
                    <div className="flex flex-wrap gap-1">
                      {c.weather_presets.map((w) => (
                        <span key={w} className="px-2 py-0.5 rounded-lg text-[10px] font-semibold bg-slate-800/40 text-slate-400 border border-slate-800 capitalize">
                          {w.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Edit/Delete Actions */}
                <div className="flex gap-2 border-t border-slate-800/80 pt-4 mt-auto">
                  <button
                    onClick={() => handleOpenEdit(c.id)}
                    className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl border border-slate-700/60 transition-all"
                  >
                    <Edit3 size={12} /> Edit Configuration
                  </button>
                  {/* Only allow deleting custom ones, prevent deleting core preset configurations */}
                  {!['india', 'mumbai', 'usa', 'japan', 'dubai', 'germany', 'uk'].includes(c.id.toLowerCase()) && (
                    <button
                      onClick={() => handleDelete(c.id)}
                      className="p-2 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 hover:border-rose-500/40 text-rose-400 rounded-xl transition-all"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Editor Modal */}
        {isEditorOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh] animate-scale-in">
              {/* Header */}
              <div className="flex justify-between items-center p-5 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <FileCode className="text-brand-400" size={20} />
                  <div>
                    <h3 className="font-bold text-white text-base">
                      {editingId ? `Edit ${editingId.toUpperCase()} Configuration` : 'Import New Country YAML'}
                    </h3>
                    <p className="text-xs text-slate-400">Pydantic V2 compile & check validator runs on submission</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsEditorOpen(false)}
                  className="text-slate-400 hover:text-white transition-all"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Body */}
              <div className="p-6 flex-1 overflow-y-auto space-y-4 flex flex-col min-h-0">
                {errorMsg && (
                  <div className="bg-rose-500/15 text-rose-400 border border-rose-500/30 p-4 rounded-xl flex gap-2.5 items-start text-sm">
                    <AlertTriangle size={16} className="shrink-0 mt-0.5" />
                    <span>{errorMsg}</span>
                  </div>
                )}
                {successMsg && (
                  <div className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 p-4 rounded-xl flex gap-2.5 items-start text-sm">
                    <Check size={16} className="shrink-0 mt-0.5" />
                    <span>{successMsg}</span>
                  </div>
                )}

                <div className="flex-1 min-h-0">
                  <textarea
                    value={yamlInput}
                    onChange={(e) => setYamlInput(e.target.value)}
                    className="w-full h-full min-h-[350px] font-mono text-xs bg-slate-950 border border-slate-850 p-4 rounded-xl text-slate-300 focus:outline-none focus:border-brand-500/80 focus:ring-1 focus:ring-brand-500/80 resize-none transition-all"
                    placeholder="YAML Content here..."
                  ></textarea>
                </div>
              </div>

              {/* Footer */}
              <div className="flex justify-end gap-3 p-5 border-t border-slate-800 bg-slate-900/80">
                <button
                  onClick={() => setIsEditorOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-all border border-slate-750"
                >
                  Cancel
                </button>
                <button
                  onClick={() => saveMutation.mutate()}
                  disabled={saveMutation.isPending}
                  className="px-5 py-2 bg-gradient-to-r from-brand-600 to-cyan-500 hover:opacity-95 text-white rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 shadow-lg shadow-brand-500/15 disabled:opacity-50"
                >
                  {saveMutation.isPending ? 'Validating...' : editingId ? 'Update & Save' : 'Compile & Create'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
