import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'
import type { ResourceItem, InventorySummary } from '../../types/inventory'

const COLORS = ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2', '#4f46e5']

export function InventoryTable({ items }: { items: ResourceItem[] }) {
  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="text-left py-2 px-3 text-gray-500 font-medium">Name</th>
            <th className="text-left py-2 px-3 text-gray-500 font-medium">Type</th>
            <th className="text-left py-2 px-3 text-gray-500 font-medium">Env</th>
            <th className="text-left py-2 px-3 text-gray-500 font-medium">Owner</th>
            <th className="text-left py-2 px-3 text-gray-500 font-medium">Status</th>
            <th className="text-left py-2 px-3 text-gray-500 font-medium">Region</th>
            <th className="text-right py-2 px-3 text-gray-500 font-medium">Monthly Cost</th>
          </tr>
        </thead>
        <tbody>
          {items.map((r, i) => (
            <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
              <td className="py-2 px-3 font-medium">{r.resource_name}</td>
              <td className="py-2 px-3">{r.service_type}</td>
              <td className="py-2 px-3">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  r.environment === 'production' ? 'bg-green-100 text-green-700' :
                  r.environment === 'staging' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{r.environment}</span>
              </td>
              <td className="py-2 px-3">{r.owner}</td>
              <td className="py-2 px-3">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  r.status === 'ACTIVE' ? 'bg-green-100 text-green-700' :
                  r.status === 'STOPPED' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{r.status}</span>
              </td>
              <td className="py-2 px-3 text-xs text-gray-500">{r.region}</td>
              <td className="py-2 px-3 text-right">${r.monthly_cost.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function InventoryByStatusChart({ summary }: { summary: InventorySummary }) {
  const data = Object.entries(summary.by_status).map(([name, value]) => ({ name, value }))

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <h3 className="text-sm font-medium text-gray-700 mb-3">By Status</h3>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
            {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function InventoryByEnvChart({ summary }: { summary: InventorySummary }) {
  const data = Object.entries(summary.by_environment).map(([name, value]) => ({ name, value }))

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <h3 className="text-sm font-medium text-gray-700 mb-3">By Environment</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="value" name="Resources" fill="#2563eb" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
