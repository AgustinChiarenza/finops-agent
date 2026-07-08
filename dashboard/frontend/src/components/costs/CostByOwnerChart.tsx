import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import type { CostByOwner } from '../../types/costs'
import { ZoomableChart } from '../ZoomableChart'

const COLORS = ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2']

export function CostByOwnerChart({ data }: { data: CostByOwner[] }) {
  if (!data.length) return <p className="text-gray-400 text-sm">No data</p>

  const chart = (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="total_cost"
          nameKey="owner"
          cx="50%"
          cy="50%"
          outerRadius={90}
          label={({ owner, percentage }) => `${owner} (${percentage}%)`}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(v: number) => [`$${v.toFixed(2)}`, 'Cost']} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )

  return (
    <ZoomableChart title="Cost by Owner">
      <div className="h-[280px]">{chart}</div>
    </ZoomableChart>
  )
}
