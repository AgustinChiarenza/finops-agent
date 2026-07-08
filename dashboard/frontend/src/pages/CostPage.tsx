import { useState } from 'react'
import { useCostSummary, useDailyCosts, useCostsByService, useCostsByOwner, useCostAnomalies } from '../hooks/useCosts'
import { CostSummaryCards } from '../components/costs/CostSummaryCards'
import { CostTrendChart } from '../components/costs/CostTrendChart'
import { CostByServiceChart } from '../components/costs/CostByServiceChart'
import { CostByOwnerChart } from '../components/costs/CostByOwnerChart'
import { CostAnomalyTable } from '../components/costs/CostAnomalyTable'
import { FilterBar } from '../components/filters/FilterBar'

export function CostPage() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const { data: summary } = useCostSummary(filters)
  const { data: daily } = useDailyCosts(filters)
  const { data: byService } = useCostsByService(filters)
  const { data: byOwner } = useCostsByOwner(filters)
  const { data: anomalies } = useCostAnomalies(filters)

  return (
    <div className="space-y-4">
      <FilterBar onFilter={setFilters} showServiceType showOwner showEnvironment />

      <CostSummaryCards data={summary} />

      <div className="grid grid-cols-2 gap-4">
        {daily && <CostTrendChart data={daily} />}
        {byService && <CostByServiceChart data={byService} />}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {byOwner && <CostByOwnerChart data={byOwner} />}
        {anomalies && <CostAnomalyTable data={anomalies} />}
      </div>
    </div>
  )
}
