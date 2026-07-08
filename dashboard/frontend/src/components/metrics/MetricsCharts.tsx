import { AreaChart, Area, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import type { MetricTimeseries, MetricSummaryItem, IdleResource } from '../../types/metrics'
import { ZoomableChart } from '../ZoomableChart'

export function CpuMemChart({ data }: { data: MetricTimeseries[] }) {
  const cpu = data.find(d => d.metric_name.toLowerCase().includes('cpu'))
  const mem = data.find(d => d.metric_name.toLowerCase().includes('mem'))

  if (!cpu && !mem) return <p className="text-gray-400 text-sm">No CPU/Memory data</p>

  const merged: Record<string, { timestamp: string; cpu?: number; mem?: number }> = {}
  if (cpu) {
    for (const dp of cpu.datapoints) {
      merged[dp.timestamp] = { ...merged[dp.timestamp], timestamp: dp.timestamp, cpu: dp.value }
    }
  }
  if (mem) {
    for (const dp of mem.datapoints) {
      merged[dp.timestamp] = { ...merged[dp.timestamp], timestamp: dp.timestamp, mem: dp.value }
    }
  }
  const chartData = Object.values(merged).sort((a, b) => a.timestamp.localeCompare(b.timestamp))

  const chart = (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
        <Tooltip />
        {cpu && <Area type="monotone" dataKey="cpu" name="CPU %" stroke="#2563eb" fill="#dbeafe" strokeWidth={2} />}
        {mem && <Area type="monotone" dataKey="mem" name="Memory %" stroke="#059669" fill="#d1fae5" strokeWidth={2} />}
        <Legend />
      </AreaChart>
    </ResponsiveContainer>
  )

  return (
    <ZoomableChart title="CPU / Memory Utilization">
      <div className="h-[280px]">{chart}</div>
    </ZoomableChart>
  )
}

export function NetworkChart({ data }: { data: MetricTimeseries[] }) {
  const netIn = data.find(d => d.metric_name.toLowerCase().includes('network_in') || d.metric_name.toLowerCase().includes('networkin'))
  const netOut = data.find(d => d.metric_name.toLowerCase().includes('network_out') || d.metric_name.toLowerCase().includes('networkout'))

  if (!netIn && !netOut) return <p className="text-gray-400 text-sm">No network data</p>

  const merged: Record<string, { timestamp: string; in?: number; out?: number }> = {}
  if (netIn) {
    for (const dp of netIn.datapoints) {
      merged[dp.timestamp] = { ...merged[dp.timestamp], timestamp: dp.timestamp, in: dp.value }
    }
  }
  if (netOut) {
    for (const dp of netOut.datapoints) {
      merged[dp.timestamp] = { ...merged[dp.timestamp], timestamp: dp.timestamp, out: dp.value }
    }
  }
  const chartData = Object.values(merged).sort((a, b) => a.timestamp.localeCompare(b.timestamp))

  const chart = (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        {netIn && <Line type="monotone" dataKey="in" name="In" stroke="#2563eb" strokeWidth={2} dot={false} />}
        {netOut && <Line type="monotone" dataKey="out" name="Out" stroke="#dc2626" strokeWidth={2} dot={false} />}
        <Legend />
      </LineChart>
    </ResponsiveContainer>
  )

  return (
    <ZoomableChart title="Network I/O">
      <div className="h-[280px]">{chart}</div>
    </ZoomableChart>
  )
}

export function MetricsSummaryTable({ data }: { data: MetricSummaryItem[] }) {
  if (!data.length) return <p className="text-gray-400 text-sm">No metrics summary</p>

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Metrics Summary</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-2 px-3 text-gray-500 font-medium">Resource</th>
              <th className="text-left py-2 px-3 text-gray-500 font-medium">Metric</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium">Avg</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium">Max</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium">P95</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 20).map((m, i) => (
              <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="py-2 px-3 font-mono text-xs">{m.resource_id}</td>
                <td className="py-2 px-3">{m.metric_name}</td>
                <td className="py-2 px-3 text-right">{m.avg.toFixed(2)}</td>
                <td className="py-2 px-3 text-right">{m.max.toFixed(2)}</td>
                <td className="py-2 px-3 text-right">{m.p95.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function IdleResourcesTable({ data }: { data: IdleResource[] }) {
  if (!data.length) return <p className="text-gray-400 text-sm">No idle resources detected</p>

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Idle Resources</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-2 px-3 text-gray-500 font-medium">Resource</th>
              <th className="text-left py-2 px-3 text-gray-500 font-medium">Type</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium">Monthly Cost</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium">Avg CPU</th>
              <th className="text-left py-2 px-3 text-gray-500 font-medium">Reason</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r, i) => (
              <tr key={i} className="border-b border-gray-50 hover:bg-yellow-50">
                <td className="py-2 px-3 font-mono text-xs">{r.resource_name}</td>
                <td className="py-2 px-3">{r.service_type}</td>
                <td className="py-2 px-3 text-right">${r.monthly_cost.toFixed(2)}</td>
                <td className="py-2 px-3 text-right">{r.avg_cpu.toFixed(1)}%</td>
                <td className="py-2 px-3 text-xs text-gray-500">{r.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
