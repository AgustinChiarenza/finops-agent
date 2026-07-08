import { useState } from 'react'
import { useMetricsSummary, useMetricsTimeseries, useIdleResources } from '../hooks/useMetrics'
import { CpuMemChart, NetworkChart, MetricsSummaryTable, IdleResourcesTable } from '../components/metrics/MetricsCharts'

export function MetricsPage() {
  const [selectedResource, setSelectedResource] = useState('')
  const { data: summary } = useMetricsSummary()
  const { data: timeseries } = useMetricsTimeseries({ resource_id: selectedResource })
  const { data: idle } = useIdleResources()

  const resourceIds = summary ? [...new Set((summary as any[]).map((m: any) => m.resource_id as string))] as string[] : []

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 bg-white p-3 rounded-lg border border-gray-200">
        <label className="text-sm text-gray-500">Resource:</label>
        <select
          value={selectedResource}
          onChange={e => setSelectedResource(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1 text-sm flex-1"
        >
          <option value="">Select a resource...</option>
          {resourceIds.map((id: string) => (
            <option key={id} value={id}>{id}</option>
          ))}
        </select>
      </div>

      {selectedResource && timeseries && (
        <div className="grid grid-cols-2 gap-4">
          <CpuMemChart data={timeseries} />
          <NetworkChart data={timeseries} />
        </div>
      )}

      {summary && <MetricsSummaryTable data={summary} />}
      {idle && <IdleResourcesTable data={idle} />}
    </div>
  )
}
