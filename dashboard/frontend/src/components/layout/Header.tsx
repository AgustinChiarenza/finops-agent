import { useLocation } from 'react-router-dom'

const titles: Record<string, string> = {
  '/': 'Dashboard Overview',
  '/inventory': 'Resource Inventory',
  '/cts': 'CTS Audit Trail',
  '/costs': 'Cost Analysis',
  '/metrics': 'Cloud Eye Metrics',
  '/insights': 'AI-Powered Insights',
}

export function Header() {
  const location = useLocation()
  const title = titles[location.pathname] || 'Cloud Ops Dashboard'

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center px-6 shrink-0">
      <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
    </header>
  )
}
