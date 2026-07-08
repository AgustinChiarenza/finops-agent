import { TrendingUp, TrendingDown, Minus, AlertTriangle, DollarSign } from 'lucide-react'
import type { CostSummary } from '../../types/costs'

export function CostSummaryCards({ data }: { data: CostSummary | undefined }) {
  if (!data) return null

  const TrendIcon = data.trend_direction === 'up' ? TrendingUp : data.trend_direction === 'down' ? TrendingDown : Minus
  const trendColor = data.trend_direction === 'up' ? 'text-red-500' : data.trend_direction === 'down' ? 'text-green-500' : 'text-gray-400'

  return (
    <div className="grid grid-cols-4 gap-4 mb-4">
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
          <DollarSign size={14} /> Accumulated Cost
        </div>
        <p className="text-2xl font-bold">${data.total_cost.toFixed(2)}</p>
      </div>
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
          <DollarSign size={14} /> Daily Average
        </div>
        <p className="text-2xl font-bold">${data.average_daily.toFixed(2)}</p>
      </div>
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">Trend</div>
        <div className="flex items-center gap-2">
          <TrendIcon size={20} className={trendColor} />
          <p className="text-2xl font-bold">{data.trend_pct > 0 ? '+' : ''}{data.trend_pct}%</p>
        </div>
      </div>
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
          <AlertTriangle size={14} /> Anomalies
        </div>
        <p className="text-2xl font-bold">{data.anomaly_count}</p>
      </div>
    </div>
  )
}
