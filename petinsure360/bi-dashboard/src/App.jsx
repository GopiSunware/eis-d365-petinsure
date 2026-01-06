import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { BarChart3, Users, FileText, TrendingUp, AlertTriangle, DollarSign, RefreshCw, Database, Bot, Upload, GitCompare } from 'lucide-react'

// Pages
import DashboardPage from './pages/DashboardPage'
import CustomersPage from './pages/CustomersPage'
import ClaimsPage from './pages/ClaimsPage'
import RisksPage from './pages/RisksPage'
import PipelinePage from './pages/PipelinePage'
import AgentPipelinePage from './pages/AgentPipelinePage'
import ComparisonPage from './pages/ComparisonPage'
import DocGenAdminPage from './pages/DocGenAdminPage'

function App() {
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const location = useLocation()

  const navItems = [
    { path: '/', icon: BarChart3, label: 'Executive Dashboard' },
    { path: '/customers', icon: Users, label: 'Customer 360' },
    { path: '/claims', icon: FileText, label: 'Claims Analytics' },
    { path: '/risks', icon: AlertTriangle, label: 'Risk Analysis' },
    { path: '/pipeline', icon: Database, label: 'Legacy Pipeline' },
    { path: '/agent-pipeline', icon: Bot, label: 'Agent Pipeline' },
    { path: '/comparison', icon: GitCompare, label: 'Rule vs Agent' },
    { path: '/docgen', icon: Upload, label: 'DocGen Admin' },
  ]

  const handleRefresh = () => {
    setLastUpdated(new Date())
    window.location.reload()
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <BarChart3 className="h-8 w-8 text-blue-400" />
              <div>
                <h1 className="text-lg font-bold">PetInsure360</h1>
                <p className="text-xs text-gray-400">BI Analytics Dashboard</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-xs text-gray-400">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
              <button
                onClick={handleRefresh}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                title="Refresh data"
              >
                <RefreshCw className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-sm min-h-[calc(100vh-4rem)] sticky top-0">
          <nav className="p-4 space-y-1">
            {navItems.map(({ path, icon: Icon, label }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  location.pathname === path
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span className="font-medium">{label}</span>
              </Link>
            ))}
          </nav>

          {/* Data Source Info */}
          <div className="p-4 mt-4 border-t">
            <p className="text-xs text-gray-500 font-semibold uppercase mb-2">Data Source</p>
            <div className="space-y-1 text-xs text-gray-600">
              <p>Gold Layer: Delta Lake</p>
              <p>Platform: Azure Databricks</p>
              <p>Refresh: On-demand</p>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/customers" element={<CustomersPage />} />
            <Route path="/claims" element={<ClaimsPage />} />
            <Route path="/risks" element={<RisksPage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/agent-pipeline" element={<AgentPipelinePage />} />
            <Route path="/comparison" element={<ComparisonPage />} />
            <Route path="/docgen" element={<DocGenAdminPage />} />
          </Routes>
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t py-4">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
          <p>PetInsure360 BI Dashboard | Built on Azure Databricks + Delta Lake + React</p>
          <p className="text-xs mt-1">Demo by Sunware Technologies</p>
        </div>
      </footer>
    </div>
  )
}

export default App
