import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Shield,
  DollarSign,
  Activity,
  Server,
  Brain,
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inventory', icon: Server, label: 'Inventory' },
  { to: '/cts', icon: Shield, label: 'CTS Audit' },
  { to: '/costs', icon: DollarSign, label: 'Costs' },
  { to: '/metrics', icon: Activity, label: 'Metrics' },
  { to: '/insights', icon: Brain, label: 'AI Insights' },
]

export function Sidebar() {
  return (
    <aside className="w-56 bg-brand-900 text-white flex flex-col shrink-0">
      <div className="p-4 border-b border-brand-700">
        <h1 className="text-lg font-bold">Cloud Ops</h1>
        <p className="text-xs text-brand-100">Huawei Cloud Dashboard</p>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-brand-600 text-white'
                  : 'text-brand-100 hover:bg-brand-700 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
