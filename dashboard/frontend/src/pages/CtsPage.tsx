import { useQuery } from '@tanstack/react-query'
import { ctsApi } from '../api/cts'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export function CtsPage() {
  const { data: summary } = useQuery({
    queryKey: ['cts', 'summary'],
    queryFn: ctsApi.summary,
  })

  const { data: events } = useQuery({
    queryKey: ['cts', 'security-events'],
    queryFn: ctsApi.securityEvents,
  })

  const { data: traces } = useQuery({
    queryKey: ['cts', 'traces'],
    queryFn: () => ctsApi.traces({ page: 1, page_size: 50 }),
  })

  if (summary?.total_traces === 0) {
    return (
      <div className="bg-white p-8 rounded-lg border border-gray-200 text-center">
        <p className="text-gray-500">No CTS data available in OBS bucket</p>
        <p className="text-sm text-gray-400 mt-2">Upload CTS trace files to the bucket to see audit data</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {summary && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Actions by User</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={Object.entries(summary.actions_by_user).map(([name, count]) => ({ name, count: count as number })).sort((a, b) => b.count - a.count).slice(0, 8)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={80} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Actions by Service</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={Object.entries(summary.actions_by_service).map(([name, count]) => ({ name, count: count as number })).sort((a, b) => b.count - a.count).slice(0, 8)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Activity by Hour</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={Object.entries(summary.actions_by_hour).sort((a, b) => a[0].localeCompare(b[0])).map(([hour, count]) => ({ hour, count }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#059669" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {events && events.length > 0 && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Security Events ({events.length})</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Severity</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Time</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">User</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Description</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Source IP</th>
                </tr>
              </thead>
              <tbody>
                {events.slice(0, 20).map((e: any, i: number) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                        e.severity === 'critical' ? 'bg-red-100 text-red-700' :
                        e.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                        e.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>{e.severity}</span>
                    </td>
                    <td className="py-2 px-3 text-xs text-gray-500">{e.time}</td>
                    <td className="py-2 px-3">{e.user}</td>
                    <td className="py-2 px-3">{e.description}</td>
                    <td className="py-2 px-3 font-mono text-xs">{e.source_ip}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {traces && traces.items && traces.items.length > 0 && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Traces</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Time</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">User</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">API</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Resource</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {traces.items.map((t: any, i: number) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 px-3 text-xs text-gray-500">{t.time}</td>
                    <td className="py-2 px-3">{t.user}</td>
                    <td className="py-2 px-3 font-mono text-xs">{t.api_name}</td>
                    <td className="py-2 px-3">{t.resource_type}/{t.resource_id}</td>
                    <td className="py-2 px-3">
                      <span className={t.response_status >= 400 ? 'text-red-600' : 'text-green-600'}>{t.response_status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
