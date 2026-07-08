import { useInventorySummary } from '../hooks/useInventory'
import { useCostSummary } from '../hooks/useCosts'
import { useIdleResources } from '../hooks/useMetrics'
import { Server, DollarSign, AlertTriangle, Activity } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { InventorySummary } from '../types/inventory'

export function DashboardPage() {
  const { data: inv } = useInventorySummary()
  const { data: cost } = useCostSummary()
  const { data: idle } = useIdleResources()
  const navigate = useNavigate()

  const invTyped = inv as InventorySummary | undefined
  const idleCount = Array.isArray(idle) ? idle.length : 0

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Card icon={Server} label="Total Resources" value={invTyped?.total_resources ?? '...'} color="blue" onClick={() => navigate('/inventory')} />
        <Card icon={DollarSign} label="Est. Monthly Cost" value={invTyped ? `$${invTyped.total_monthly_cost.toFixed(0)}` : '...'} color="green" onClick={() => navigate('/costs')} />
        <Card icon={AlertTriangle} label="Idle Resources" value={idleCount ?? '...'} color="yellow" onClick={() => navigate('/metrics')} />
        <Card icon={Activity} label="Cost Trend" value={cost ? `${cost.trend_pct > 0 ? '+' : ''}${cost.trend_pct}%` : '...'} color={cost?.trend_direction === 'up' ? 'red' : 'green'} onClick={() => navigate('/costs')} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Resources by Service</h3>
          {invTyped ? (
            <div className="space-y-2">
              {Object.entries(invTyped.by_service_type).sort(([, a], [, b]) => (b as number) - (a as number)).slice(0, 6).map(([type, count]) => (
                <div key={type} className="flex items-center gap-2">
                  <span className="text-sm text-gray-600 w-24 truncate">{type}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-3">
                    <div className="bg-brand-500 rounded-full h-3" style={{ width: `${((count as number) / invTyped.total_resources) * 100}%` }} />
                  </div>
                  <span className="text-sm text-gray-500 w-8 text-right">{count as number}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-gray-400 text-sm">Loading...</p>}
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Cost by Service</h3>
          {invTyped ? (
            <div className="space-y-2">
              {Object.entries(invTyped.cost_by_service_type).sort(([, a], [, b]) => (b as number) - (a as number)).slice(0, 6).map(([type, costVal]) => (
                <div key={type} className="flex items-center gap-2">
                  <span className="text-sm text-gray-600 w-24 truncate">{type}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-3">
                    <div className="bg-green-500 rounded-full h-3" style={{ width: `${((costVal as number) / invTyped.total_monthly_cost) * 100}%` }} />
                  </div>
                  <span className="text-sm text-gray-500 w-16 text-right">${(costVal as number).toFixed(0)}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-gray-400 text-sm">Loading...</p>}
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg border border-gray-200 text-center">
        <h3 className="text-lg font-medium text-gray-700 mb-2">AI-Powered Cloud Analysis</h3>
        <p className="text-sm text-gray-500 mb-4">Generate comprehensive insights across security, cost, and operations using MaaS</p>
        <button
          onClick={() => navigate('/insights')}
          className="bg-brand-600 text-white px-6 py-2 rounded-lg hover:bg-brand-700 transition-colors"
        >
          Generate AI Insights
        </button>
      </div>
    </div>
  )
}

function Card({ icon: Icon, label, value, color, onClick }: { icon: typeof Server; label: string; value: string | number; color: string; onClick: () => void }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200',
    red: 'bg-red-50 text-red-600 border-red-200',
  }
  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-lg border cursor-pointer hover:shadow-md transition-shadow ${colors[color] || colors.blue}`}
    >
      <div className="flex items-center gap-2 mb-1">
        <Icon size={16} />
        <span className="text-xs font-medium opacity-75">{label}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  )
}
