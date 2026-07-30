import type { LucideIcon } from 'lucide-react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface StatCardProps {
  label: string
  value: string | number
  icon: LucideIcon
  trend?: number           // positive = up, negative = down, 0 = flat
  trendLabel?: string
  accent?: 'cyan' | 'violet' | 'green' | 'amber'
  loading?: boolean
}

const ACCENT = {
  cyan:   { ring: 'ring-neon-cyan/20',   bg: 'from-neon-cyan/10 to-transparent',   icon: 'text-neon-cyan',   glow: 'shadow-glow-cyan' },
  violet: { ring: 'ring-violet-500/20',  bg: 'from-violet-500/10 to-transparent',  icon: 'text-violet-400',  glow: 'shadow-glow-violet' },
  green:  { ring: 'ring-neon-green/20',  bg: 'from-neon-green/10 to-transparent',  icon: 'text-neon-green',  glow: 'shadow-glow-green' },
  amber:  { ring: 'ring-amber-500/20',   bg: 'from-amber-500/10 to-transparent',   icon: 'text-amber-400',   glow: '' },
}

export default function StatCard({ label, value, icon: Icon, trend, trendLabel, accent = 'cyan', loading }: StatCardProps) {
  const a = ACCENT[accent]
  if (loading) return (
    <div className="card p-5 animate-fade-in">
      <div className="skeleton h-4 w-24 mb-3" />
      <div className="skeleton h-8 w-16 mb-2" />
      <div className="skeleton h-3 w-20" />
    </div>
  )

  const TrendIcon = trend === undefined ? Minus : trend > 0 ? TrendingUp : TrendingDown
  const trendColor = trend === undefined ? 'text-slate-500' : trend > 0 ? 'text-emerald-400' : 'text-red-400'

  return (
    <div className={`card-hover p-5 ring-1 ${a.ring} animate-fade-in`}>
      <div className="flex items-start justify-between mb-4">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</p>
        <div className={`flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br ${a.bg} ring-1 ${a.ring} ${a.glow}`}>
          <Icon size={17} className={a.icon} />
        </div>
      </div>
      <p className="text-3xl font-bold text-white tracking-tight mb-1">{value}</p>
      {trendLabel && (
        <div className={`flex items-center gap-1 text-xs font-medium ${trendColor}`}>
          <TrendIcon size={12} />
          <span>{trendLabel}</span>
        </div>
      )}
    </div>
  )
}
