import { AlertTriangle, AlertCircle, Info, ShieldAlert } from 'lucide-react'

const severityConfig: Record<string, { color: string; bg: string; Icon: typeof AlertTriangle }> = {
  critical: { color: 'text-red-700', bg: 'bg-red-50 border-red-200', Icon: ShieldAlert },
  high: { color: 'text-orange-700', bg: 'bg-orange-50 border-orange-200', Icon: AlertTriangle },
  medium: { color: 'text-yellow-700', bg: 'bg-yellow-50 border-yellow-200', Icon: AlertCircle },
  low: { color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200', Icon: Info },
}

interface InsightCardProps {
  severity: string
  title: string
  description: string
  affectedResources?: string[]
  recommendation?: string
  confidence?: number
}

export function InsightCard({ severity, title, description, affectedResources, recommendation, confidence }: InsightCardProps) {
  const config = severityConfig[severity] || severityConfig.medium
  const { Icon } = config

  return (
    <div className={`p-4 rounded-lg border ${config.bg}`}>
      <div className="flex items-start gap-3">
        <Icon size={20} className={config.color + ' mt-0.5 shrink-0'} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${config.color} ${config.bg}`}>{severity}</span>
            <h4 className="font-medium text-gray-900">{title}</h4>
            {confidence !== undefined && (
              <span className="text-xs text-gray-400 ml-auto">Confidence: {(confidence * 100).toFixed(0)}%</span>
            )}
          </div>
          <p className="text-sm text-gray-600 mb-2">{description}</p>
          {affectedResources && affectedResources.length > 0 && (
            <div className="mb-2">
              <p className="text-xs text-gray-500 font-medium">Affected resources:</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {affectedResources.map((r, i) => (
                  <span key={i} className="bg-white px-2 py-0.5 rounded text-xs font-mono border border-gray-200">{r}</span>
                ))}
              </div>
            </div>
          )}
          {recommendation && (
            <p className="text-sm text-green-700"><strong>Fix:</strong> {recommendation}</p>
          )}
        </div>
      </div>
    </div>
  )
}
