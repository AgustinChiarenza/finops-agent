import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { CostByService } from '../../types/costs'
import { ZoomableChart } from '../ZoomableChart'

const COLORS = ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2', '#4f46e5', '#ca8a04']

export function CostByServiceChart({ data }: { data: CostByService[] }) {
  if (!data.length) return <p className="text-gray-400 text-sm">No data</p>

  const chart = (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={v => `$${v}`} />
        <YAxis dataKey="service_type" type="category" tick={{ fontSize: 11 }} width={80} />
        <Tooltip formatter={(v: number) => [`$${v.toFixed(2)}`, 'Cost']} />
        <Bar dataKey="total_cost" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )

  return (
    <ZoomableChart title="Cost by Service">
      <div className="h-[280px]">{chart}</div>
    </ZoomableChart>
  )
}
