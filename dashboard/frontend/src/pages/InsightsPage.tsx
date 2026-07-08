import { useState } from 'react'
import { useSecurityInsight, useCostInsight, useOperationalInsight, useComprehensiveInsight } from '../hooks/useInsights'
import { InsightsPanel } from '../components/insights/InsightsPanel'
import type { InsightResult, ComprehensiveInsight } from '../types/insights'

type Tab = 'security' | 'cost' | 'operational' | 'comprehensive'

export function InsightsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('comprehensive')
  const [results, setResults] = useState<Record<string, InsightResult | ComprehensiveInsight | null>>({
    security: null,
    cost: null,
    operational: null,
    comprehensive: null,
  })
  const [error, setError] = useState<string | null>(null)

  const securityMut = useSecurityInsight()
  const costMut = useCostInsight()
  const opsMut = useOperationalInsight()
  const compMut = useComprehensiveInsight()

  const handleGenerate = async (tab: Tab) => {
    setError(null)
    try {
      if (tab === 'security') {
        const res = await securityMut.mutateAsync()
        setResults(prev => ({ ...prev, security: res }))
      } else if (tab === 'cost') {
        const res = await costMut.mutateAsync()
        setResults(prev => ({ ...prev, cost: res }))
      } else if (tab === 'operational') {
        const res = await opsMut.mutateAsync()
        setResults(prev => ({ ...prev, operational: res }))
      } else {
        const res = await compMut.mutateAsync()
        setResults(prev => ({ ...prev, comprehensive: res }))
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      setError(msg)
    }
  }

  const isLoading = securityMut.isPending || costMut.isPending || opsMut.isPending || compMut.isPending

  const tabs: { key: Tab; label: string }[] = [
    { key: 'comprehensive', label: 'Comprehensive' },
    { key: 'security', label: 'Security' },
    { key: 'cost', label: 'Cost' },
    { key: 'operational', label: 'Operational' },
  ]

  const getCurrentInsight = (): InsightResult | null => {
    const r = results[activeTab]
    if (!r) return null
    if (activeTab === 'comprehensive' && 'security' in r) {
      const comp = r as ComprehensiveInsight
      return comp.security || comp.cost || comp.operational || null
    }
    return r as InsightResult
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 bg-white p-2 rounded-lg border border-gray-200">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === key ? 'bg-brand-600 text-white' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {label}
          </button>
        ))}
        <button
          onClick={() => handleGenerate(activeTab)}
          disabled={isLoading}
          className="ml-auto bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Analyzing with AI (this may take 1-2 min)...' : 'Generate Analysis'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm">
          Analysis failed: {error}
        </div>
      )}

      {activeTab === 'comprehensive' && results.comprehensive && 'security' in results.comprehensive ? (
        <ComprehensiveView data={results.comprehensive as ComprehensiveInsight} />
      ) : (
        <InsightsPanel insight={getCurrentInsight()} loading={isLoading} />
      )}
    </div>
  )
}

function ComprehensiveView({ data }: { data: ComprehensiveInsight }) {
  return (
    <div className="space-y-6">
      {data.security && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Security Analysis</h3>
          <InsightsPanel insight={data.security} loading={false} />
        </div>
      )}
      {data.cost && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Cost Analysis</h3>
          <InsightsPanel insight={data.cost} loading={false} />
        </div>
      )}
      {data.operational && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Operational Analysis</h3>
          <InsightsPanel insight={data.operational} loading={false} />
        </div>
      )}
      <p className="text-xs text-gray-400">Generated at: {data.generated_at}</p>
    </div>
  )
}
