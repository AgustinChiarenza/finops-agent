import type { CostAnomaly } from '../../types/costs'

export function CostAnomalyTable({ data }: { data: CostAnomaly[] }) {
  if (!data.length) return <p className="text-gray-400 text-sm">No anomalies detected</p>

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Cost Anomalies</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-2 px-3 text-gray-500 font-medium">Date</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium">Expected</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium">Actual</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium">Deviation</th>
            </tr>
          </thead>
          <tbody>
            {data.map((a, i) => (
              <tr key={i} className="border-b border-gray-50 hover:bg-red-50">
                <td className="py-2 px-3">{a.date}</td>
                <td className="py-2 px-3 text-right">${a.expected_cost.toFixed(2)}</td>
                <td className="py-2 px-3 text-right text-red-600 font-medium">${a.actual_cost.toFixed(2)}</td>
                <td className="py-2 px-3 text-right">
                  <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-medium">
                    +{a.deviation_pct}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
