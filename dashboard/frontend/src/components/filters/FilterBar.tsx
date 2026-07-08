import { useState } from 'react'

interface FilterBarProps {
  onFilter: (filters: Record<string, string>) => void
  showServiceType?: boolean
  showOwner?: boolean
  showEnvironment?: boolean
}

export function FilterBar({ onFilter, showServiceType, showOwner, showEnvironment }: FilterBarProps) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [serviceType, setServiceType] = useState('')
  const [owner, setOwner] = useState('')
  const [environment, setEnvironment] = useState('')

  const handleApply = () => {
    const filters: Record<string, string> = {}
    if (startDate) filters.start_date = startDate
    if (endDate) filters.end_date = endDate
    if (serviceType) filters.service_type = serviceType
    if (owner) filters.owner = owner
    if (environment) filters.environment = environment
    onFilter(filters)
  }

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4 bg-white p-3 rounded-lg border border-gray-200">
      <div className="flex items-center gap-2">
        <label className="text-xs text-gray-500">From</label>
        <input
          type="date"
          value={startDate}
          onChange={e => setStartDate(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
        />
      </div>
      <div className="flex items-center gap-2">
        <label className="text-xs text-gray-500">To</label>
        <input
          type="date"
          value={endDate}
          onChange={e => setEndDate(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
        />
      </div>
      {showServiceType && (
        <input
          placeholder="Service type"
          value={serviceType}
          onChange={e => setServiceType(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm w-32"
        />
      )}
      {showOwner && (
        <input
          placeholder="Owner"
          value={owner}
          onChange={e => setOwner(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm w-32"
        />
      )}
      {showEnvironment && (
        <select
          value={environment}
          onChange={e => setEnvironment(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
        >
          <option value="">All envs</option>
          <option value="production">Production</option>
          <option value="staging">Staging</option>
          <option value="development">Development</option>
        </select>
      )}
      <button
        onClick={handleApply}
        className="bg-brand-600 text-white px-3 py-1 rounded text-sm hover:bg-brand-700"
      >
        Apply
      </button>
    </div>
  )
}
