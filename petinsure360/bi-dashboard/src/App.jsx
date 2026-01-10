import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { useState, useEffect, useCallback } from 'react'
import { BarChart3, Users, FileText, TrendingUp, AlertTriangle, DollarSign, RefreshCw, Database, Bot, Upload, GitCompare, Settings } from 'lucide-react'

// Chat Components
import { ChatSidebar } from './components/ChatSidebar'
import ChatToggle from './components/ChatToggle'

// Pages
import DashboardPage from './pages/DashboardPage'
import CustomersPage from './pages/CustomersPage'
import ClaimsPage from './pages/ClaimsPage'
import RisksPage from './pages/RisksPage'
import PipelinePage from './pages/PipelinePage'
import AgentPipelinePage from './pages/AgentPipelinePage'
import ComparisonPage from './pages/ComparisonPage'
import DocGenAdminPage from './pages/DocGenAdminPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [chatOpen, setChatOpen] = useState(true) // Open by default
  const [chatWidth, setChatWidth] = useState(() => Math.floor(window.innerWidth * 0.20))
  const [recentActivity, setRecentActivity] = useState([])
  const location = useLocation()

  // Get current page name for chat context
  const getCurrentPage = useCallback(() => {
    const path = location.pathname
    if (path === '/') return 'executive-dashboard'
    if (path === '/customers') return 'customer-360'
    if (path === '/claims') return 'claims-analytics'
    if (path === '/risks') return 'risk-analysis'
    if (path === '/pipeline') return 'legacy-pipeline'
    if (path === '/agent-pipeline') return 'agent-pipeline'
    if (path === '/comparison') return 'rule-vs-agent'
    if (path === '/docgen') return 'docgen-admin'
    if (path === '/settings') return 'ai-settings'
    return 'dashboard'
  }, [location.pathname])

  // Simulated analyst user for BI Dashboard
  const analystUser = {
    first_name: 'Analyst',
    full_name: 'BI Analyst',
    email: 'analyst@petinsure360.com',
    role: 'analyst'
  }

  const navItems = [
    { path: '/', icon: BarChart3, label: 'Executive Dashboard' },
    { path: '/customers', icon: Users, label: 'Customer 360' },
    { path: '/claims', icon: FileText, label: 'Claims Analytics' },
    { path: '/risks', icon: AlertTriangle, label: 'Risk Analysis' },
    { path: '/pipeline', icon: Database, label: 'Rule Engine Pipeline' },
    { path: '/agent-pipeline', icon: Bot, label: 'Agent Pipeline' },
    { path: '/comparison', icon: GitCompare, label: 'Rule vs Agent' },
    { path: '/docgen', icon: Upload, label: 'DocGen Admin' },
    { path: '/settings', icon: Settings, label: 'AI Settings' },
  ]

  const handleRefresh = () => {
    setLastUpdated(new Date())
    // Add to recent activity
    setRecentActivity(prev => ['Dashboard data refreshed', ...prev].slice(0, 10))
    window.location.reload()
  }

  // Track page navigation as recent activity
  useEffect(() => {
    const pageName = getCurrentPage().replace(/-/g, ' ')
    setRecentActivity(prev => [`Viewing ${pageName}`, ...prev].slice(0, 10))
  }, [location.pathname, getCurrentPage])

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gray-900 text-white">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
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
        <main
          id="main-content"
          className="flex-1 p-6 transition-all duration-300"
          style={{ marginRight: chatOpen ? `${chatWidth}px` : '0px' }}
        >
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/customers" element={<CustomersPage />} />
            <Route path="/claims" element={<ClaimsPage />} />
            <Route path="/risks" element={<RisksPage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/agent-pipeline" element={<AgentPipelinePage />} />
            <Route path="/comparison" element={<ComparisonPage />} />
            <Route path="/docgen" element={<DocGenAdminPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t py-4">
        <div className="max-w-full mx-auto px-4 text-center text-sm text-gray-500">
          <p>PetInsure360 BI Dashboard | Built on Azure Databricks + Delta Lake + React</p>
          <p className="text-xs mt-1">Demo by Sunware Technologies</p>
        </div>
      </footer>

      {/* Chat Sidebar */}
      <ChatSidebar
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        onWidthChange={setChatWidth}
        currentPage={getCurrentPage()}
        customerData={analystUser}
        recentActivity={recentActivity}
        portalType="bi-dashboard"
      />

      {/* Chat Toggle Button */}
      <ChatToggle onClick={() => setChatOpen(true)} isOpen={chatOpen} />
    </div>
  )
}

export default App
