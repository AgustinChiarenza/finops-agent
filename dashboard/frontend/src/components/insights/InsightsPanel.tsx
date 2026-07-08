import { InsightCard } from './InsightCard'
import type { InsightResult } from '../../types/insights'

export function InsightsPanel({ insight, loading }: { insight: InsightResult | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" />
        <span className="ml-3 text-gray-500">Analyzing with AI...</span>
      </div>
    )
  }

  if (!insight) {
    return <p className="text-gray-400 text-sm p-4">Click "Generate Analysis" to run AI-powered analysis</p>
  }

  const findings = insight.findings || insight.anomalies?.map(a => ({
    severity: 'high',
    title: `Cost anomaly: ${a.resource_name}`,
    description: `Expected $${a.expected_cost.toFixed(2)}, actual $${a.actual_cost.toFixed(2)} (+${a.deviation_pct}%)`,
    affected_resources: [a.resource_id],
    recommendation: a.recommendation,
    confidence: 0.8,
  })) || insight.risks?.map(r => ({
    severity: r.severity,
    title: r.title,
    description: r.description,
    affected_resources: r.affected_resources,
    recommendation: r.recommendation,
    confidence: 0.7,
  })) || []

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <p className="text-sm text-gray-700">{insight.summary}</p>
        {insight.risk_score !== undefined && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-gray-500">Risk Score:</span>
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className={`rounded-full h-2 ${insight.risk_score > 70 ? 'bg-red-500' : insight.risk_score > 40 ? 'bg-yellow-500' : 'bg-green-500'}`}
                style={{ width: `${insight.risk_score}%` }}
              />
            </div>
            <span className="text-xs font-bold">{insight.risk_score}/100</span>
          </div>
        )}
        {insight.estimated_monthly_savings_usd !== undefined && insight.estimated_monthly_savings_usd > 0 && (
          <p className="mt-2 text-sm text-green-700 font-medium">
            Estimated monthly savings: ${insight.estimated_monthly_savings_usd.toFixed(2)}
          </p>
        )}
      </div>
      {findings.map((f, i) => (
        <InsightCard
          key={i}
          severity={f.severity}
          title={f.title}
          description={f.description}
          affectedResources={f.affected_resources}
          recommendation={f.recommendation}
          confidence={f.confidence}
        />
      ))}
      {insight.recommendations && insight.recommendations.length > 0 && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h4 className="font-medium text-gray-700 mb-2">General Recommendations</h4>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
            {insight.recommendations.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}
      <p className="text-xs text-gray-400">Generated at: {insight.generated_at}</p>
    </div>
  )
}
