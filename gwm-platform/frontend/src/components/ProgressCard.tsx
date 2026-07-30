interface ProgressCardProps {
  label: string
  value: number     // 0 – 100
  color?: string    // tailwind gradient classes
  showValue?: boolean
  size?: 'sm' | 'md'
}

export default function ProgressCard({ label, value, color = 'from-brand-500 to-violet-500', showValue = true, size = 'md' }: ProgressCardProps) {
  const clamped = Math.min(100, Math.max(0, value))
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className={`font-medium text-slate-300 ${size === 'sm' ? 'text-xs' : 'text-sm'}`}>{label}</span>
        {showValue && <span className={`font-bold text-white ${size === 'sm' ? 'text-xs' : 'text-sm'}`}>{clamped.toFixed(1)}%</span>}
      </div>
      <div className={`w-full rounded-full bg-slate-800 ${size === 'sm' ? 'h-1.5' : 'h-2'}`}>
        <div
          className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-700 ease-out`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}
