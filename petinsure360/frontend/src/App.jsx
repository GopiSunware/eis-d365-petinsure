import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect, useCallback } from 'react'
import { Home, User, PawPrint, FileText, AlertCircle, Menu, X, LogIn, LogOut, Sparkles, Upload, Calculator, RefreshCw } from 'lucide-react'

// Chat Components
import { ChatSidebar } from './components/ChatSidebar'
import ChatToggle from './components/ChatToggle'

// Pages
import HomePage from './pages/HomePage'
import RegisterPage from './pages/RegisterPage'
import LoginPage from './pages/LoginPage'
import AddPetPage from './pages/AddPetPage'
import PolicyPage from './pages/PolicyPage'
import ClaimPage from './pages/ClaimPage'
import PetSelectPage from './pages/PetSelectPage'
import UploadDocsPage from './pages/UploadDocsPage'
import QuotePage from './pages/QuotePage'

// WebSocket hook
import { useWebSocket } from './hooks/useWebSocket'

// WebSocket URL - connects to PetInsure360 backend
const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'ws://localhost:3002/ws'

function App() {
  const [notifications, setNotifications] = useState([])
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [user, setUser] = useState(null)
  const [chatOpen, setChatOpen] = useState(true) // Open by default
  const [chatWidth, setChatWidth] = useState(() => Math.floor(window.innerWidth * 0.20))
  const [recentActivity, setRecentActivity] = useState([])
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const location = useLocation()
  const navigate = useNavigate()

  // Initialize WebSocket connection
  const { isConnected, connect, on, off } = useWebSocket(SOCKET_URL)

  // Get current page name for chat context
  const getCurrentPage = useCallback(() => {
    const path = location.pathname
    if (path === '/') return 'dashboard'
    if (path === '/claim') return 'claims'
    if (path === '/policy') return 'policies'
    if (path.includes('pet')) return 'pets'
    return 'dashboard'
  }, [location.pathname])

  // Load user from localStorage on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('petinsure_user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (e) {
        localStorage.removeItem('petinsure_user')
      }
    }
  }, [])

  useEffect(() => {
    // Connect to native WebSocket
    connect()

    // Setup event handlers
    on('connect', () => {
      console.log('Connected to PetInsure360 server')
    })

    on('connected', () => {
      console.log('WebSocket handshake complete')
    })

    on('disconnect', () => {
      console.log('Disconnected from server')
    })

    on('customer_created', (data) => {
      addNotification('success', `Customer ${data.name} registered!`)
    })

    on('pet_added', (data) => {
      addNotification('success', `Pet ${data.pet_name} added!`)
    })

    on('policy_created', (data) => {
      addNotification('success', `Policy ${data.policy_number} created!`)
    })

    on('claim_submitted', (data) => {
      addNotification('info', `Claim ${data.claim_number} submitted`)
    })

    on('claim_status_update', (data) => {
      addNotification('info', `Claim ${data.claim_number}: ${data.status}`)
    })

    // DocGen events
    on('docgen_upload', (data) => {
      addNotification('info', data.message || 'Documents uploaded')
    })

    on('docgen_status', (data) => {
      addNotification('info', data.message || 'Processing documents...')
    })

    on('docgen_completed', (data) => {
      if (data.claim_number) {
        addNotification('success', data.message || `Claim ${data.claim_number} created!`)
      } else {
        addNotification('info', data.message || 'Document processing completed')
      }
    })

    on('docgen_failed', (data) => {
      addNotification('error', data.message || 'Document processing failed')
    })

    return () => {
      // Cleanup event handlers
      off('connect')
      off('connected')
      off('disconnect')
      off('customer_created')
      off('pet_added')
      off('policy_created')
      off('claim_submitted')
      off('claim_status_update')
      off('docgen_upload')
      off('docgen_status')
      off('docgen_completed')
      off('docgen_failed')
    }
  }, [connect, on, off])

  const addNotification = (type, message) => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, type, message }])
    // Track recent activity for chat context
    setRecentActivity(prev => [message, ...prev].slice(0, 10))
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id))
    }, 5000)
  }

  const handleLogin = (userData) => {
    setUser(userData)
    localStorage.setItem('petinsure_user', JSON.stringify(userData))
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('petinsure_user')
    navigate('/')
  }

  const handleRefresh = () => {
    setLastUpdated(new Date())
    window.location.reload()
  }

  const navItems = user ? [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/pet-select', icon: Sparkles, label: 'Pet Recommendations' },
    { path: '/quote', icon: Calculator, label: 'Get a Quote' },
    { path: '/add-pet', icon: PawPrint, label: 'Add Pet' },
    { path: '/policy', icon: FileText, label: 'Buy Policy' },
    { path: '/claim', icon: AlertCircle, label: 'Submit Claim' },
    { path: '/upload-docs', icon: Upload, label: 'Upload Documents', subtitle: 'Creates new claim' },
  ] : [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/pet-select', icon: Sparkles, label: 'Pet Recommendations' },
    { path: '/quote', icon: Calculator, label: 'Get a Quote' },
    { path: '/register', icon: User, label: 'Register' },
    { path: '/login', icon: LogIn, label: 'Sign In' },
  ]

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gray-900 text-white">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <PawPrint className="h-8 w-8 text-orange-400" />
              <div>
                <h1 className="text-lg font-bold">PetInsure360</h1>
                <p className="text-xs text-gray-400">Customer Portal</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-xs text-gray-400">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <span className="text-xs text-gray-400">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
              <button
                onClick={handleRefresh}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                title="Refresh"
              >
                <RefreshCw className="h-5 w-5" />
              </button>

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-lg hover:bg-gray-800"
              >
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`
          ${mobileMenuOpen ? 'block' : 'hidden'} md:block
          w-64 bg-white shadow-sm min-h-[calc(100vh-4rem)] sticky top-0
          ${mobileMenuOpen ? 'fixed inset-0 z-40 mt-16' : ''}
        `}>
          {/* User Info */}
          {user && (
            <div className="p-4 border-b bg-gradient-to-r from-orange-50 to-orange-100">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 rounded-full bg-orange-500 text-white flex items-center justify-center font-bold">
                  {(user.first_name?.[0] || user.full_name?.[0] || 'U').toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {user.full_name || `${user.first_name} ${user.last_name}`}
                  </p>
                  <p className="text-xs text-gray-500 truncate">{user.email}</p>
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="p-4 space-y-1">
            {navItems.map(({ path, icon: Icon, label, subtitle }) => (
              <Link
                key={path}
                to={path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  location.pathname === path
                    ? 'bg-orange-50 text-orange-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className="h-5 w-5" />
                <div>
                  <span className="font-medium">{label}</span>
                  {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
                </div>
              </Link>
            ))}

            {/* Logout Button */}
            {user && (
              <button
                onClick={() => {
                  handleLogout()
                  setMobileMenuOpen(false)
                }}
                className="flex items-center space-x-3 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 w-full mt-4"
              >
                <LogOut className="h-5 w-5" />
                <span className="font-medium">Sign Out</span>
              </button>
            )}
          </nav>

          {/* Platform Info */}
          <div className="p-4 mt-4 border-t">
            <p className="text-xs text-gray-500 font-semibold uppercase mb-2">Platform</p>
            <div className="space-y-1 text-xs text-gray-600">
              <p>Backend: FastAPI + Socket.IO</p>
              <p>Data: Azure ADLS Gen2</p>
              <p>Analytics: Databricks</p>
            </div>
          </div>
        </aside>

        {/* Mobile overlay */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        {/* Main Content */}
        <main
          id="main-content"
          className="flex-1 p-6 transition-all duration-300"
          style={{ marginRight: chatOpen ? `${chatWidth}px` : '0px' }}
        >
          <Routes>
            <Route path="/" element={<HomePage user={user} />} />
            <Route path="/pet-select" element={<PetSelectPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/add-pet" element={<AddPetPage user={user} />} />
            <Route path="/policy" element={<PolicyPage user={user} />} />
            <Route path="/claim" element={<ClaimPage user={user} />} />
            <Route path="/upload-docs" element={<UploadDocsPage user={user} addNotification={addNotification} />} />
            <Route path="/quote" element={<QuotePage user={user} />} />
          </Routes>
        </main>
      </div>

      {/* Notifications */}
      <div className="fixed top-20 right-4 z-50 space-y-2">
        {notifications.map(({ id, type, message }) => (
          <div
            key={id}
            className={`px-4 py-3 rounded-lg shadow-lg animate-pulse ${
              type === 'success' ? 'bg-green-500 text-white' :
              type === 'error' ? 'bg-red-500 text-white' :
              'bg-blue-500 text-white'
            }`}
          >
            {message}
          </div>
        ))}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t py-4">
        <div className="max-w-full mx-auto px-4 text-center text-sm text-gray-500">
          <p>PetInsure360 Customer Portal | Built on Azure + Databricks + React</p>
          <p className="text-xs mt-1">Demo by Sunware Technologies</p>
        </div>
      </footer>

      {/* Chat Sidebar */}
      <ChatSidebar
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        onWidthChange={setChatWidth}
        currentPage={getCurrentPage()}
        customerData={user}
        recentActivity={recentActivity}
      />

      {/* Chat Toggle Button */}
      <ChatToggle onClick={() => setChatOpen(true)} isOpen={chatOpen} />
    </div>
  )
}

export default App
