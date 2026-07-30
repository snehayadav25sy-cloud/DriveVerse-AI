import { RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts'

interface QualityGaugeProps {
  score: number   // 0 – 100
  label?: string
  title?: string
  size?: number
}

function scoreColor(score: number) {
  if (score >= 80) return '#00ff94'
  if (score >= 60) return '#2aa5ff'
  if (score >= 40) return '#f59e0b'
  return '#ef4444'
}

function scoreLabel(score: number) {
  if (score >= 80) return 'Excellent'
  if (score >= 60) return 'Good'
  if (score >= 40) return 'Fair'
  return 'Poor'
}

export default function QualityGauge({ score, label = 'Quality Score', size = 180 }: QualityGaugeProps) {
  const color = scoreColor(score)
  const data = [{ value: score, fill: color }]

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <RadialBarChart
          width={size}
          height={size}
          cx={size / 2}
          cy={size / 2}
          innerRadius={size * 0.35}
          outerRadius={size * 0.48}
          data={data}
          startAngle={225}
          endAngle={-45}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar
            dataKey="value"
            angleAxisId={0}
            background={{ fill: '#1e293b' }}
            cornerRadius={6}
          />
        </RadialBarChart>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-white">{score.toFixed(0)}</span>
          <span className="text-xs font-semibold mt-0.5" style={{ color }}>{scoreLabel(score)}</span>
        </div>
      </div>
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</p>
    </div>
  )
}
