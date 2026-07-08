import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { DailyCostPoint } from '../../types/costs'
import { ZoomableChart } from '../ZoomableChart'

export function CostTrendChart({ data }: { data: DailyCostPoint[] }) {
  if (!data.length) return <p className="text-gray-400 text-sm">No cost data</p>

  const chart = (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `$${v}`} />
        <Tooltip formatter={(v: number) => [`$${v.toFixed(2)}`, 'Cost']} />
        <Area type="monotone" dataKey="cost" stroke="#2563eb" fill="#dbeafe" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  )

  return (
    <ZoomableChart title="Daily Cost Trend">
      <div className="h-[280px]">{chart}</div>
    </ZoomableChart>
  )
}
