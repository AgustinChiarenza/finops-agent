import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { InventoryPage } from './pages/InventoryPage'
import { CtsPage } from './pages/CtsPage'
import { CostPage } from './pages/CostPage'
import { MetricsPage } from './pages/MetricsPage'
import { InsightsPage } from './pages/InsightsPage'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/cts" element={<CtsPage />} />
          <Route path="/costs" element={<CostPage />} />
          <Route path="/metrics" element={<MetricsPage />} />
          <Route path="/insights" element={<InsightsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
