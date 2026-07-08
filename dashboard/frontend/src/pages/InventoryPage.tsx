import { useState } from 'react'
import { useInventorySummary, useInventory } from '../hooks/useInventory'
import { InventoryTable, InventoryByStatusChart, InventoryByEnvChart } from '../components/inventory/InventoryComponents'
import { FilterBar } from '../components/filters/FilterBar'
import { ChevronLeft, ChevronRight } from 'lucide-react'

export function InventoryPage() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [page, setPage] = useState(1)
  const { data: summary } = useInventorySummary()
  const { data: inventory } = useInventory({ ...filters, page, page_size: 50 })

  const handleFilterChange = (newFilters: Record<string, string>) => {
    setFilters(newFilters)
    setPage(1)
  }

  return (
    <div className="space-y-4">
      <FilterBar onFilter={handleFilterChange} showServiceType showOwner showEnvironment />

      {summary && (
        <div className="grid grid-cols-2 gap-4">
          <InventoryByStatusChart summary={summary} />
          <InventoryByEnvChart summary={summary} />
        </div>
      )}

      {inventory && <InventoryTable items={inventory.items} />}

      {inventory && inventory.total_pages > 1 && (
        <div className="flex items-center justify-between bg-white px-4 py-3 rounded-lg border border-gray-200">
          <span className="text-sm text-gray-500">
            {inventory.total} total resources
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={inventory.page <= 1}
              className="p-1.5 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-sm font-medium text-gray-700">
              {inventory.page} / {inventory.total_pages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(inventory.total_pages, p + 1))}
              disabled={inventory.page >= inventory.total_pages}
              className="p-1.5 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
