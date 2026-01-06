import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { io } from 'socket.io-client'
import { Home, User, PawPrint, FileText, AlertCircle, Menu, X, LogIn, LogOut, Sparkles, Upload } from 'lucide-react'

// Pages
import HomePage from './pages/HomePage'
import RegisterPage from './pages/RegisterPage'
import LoginPage from './pages/LoginPage'
import AddPetPage from './pages/AddPetPage'
import PolicyPage from './pages/PolicyPage'
import ClaimPage from './pages/ClaimPage'
import PetSelectPage from './pages/PetSelectPage'
import UploadDocsPage from './pages/UploadDocsPage'

// Socket connection - connects to PetInsure360 backend
const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:3002'
const socket = io(SOCKET_URL, {
  transports: ['websocket', 'polling'],
  autoConnect: false
})

function App() {
  const [isConnected, setIsConnected] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [user, setUser] = useState(null)
  const location = useLocation()
  const navigate = useNavigate()

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
    // Connect to WebSocket
    socket.connect()

    socket.on('connect', () => {
      setIsConnected(true)
      console.log('Connected to PetInsure360 server')
    })

    socket.on('disconnect', () => {
      setIsConnected(false)
    })

    socket.on('customer_created', (data) => {
      addNotification('success', `Customer ${data.name} registered!`)
    })

    socket.on('pet_added', (data) => {
      addNotification('success', `Pet ${data.pet_name} added!`)
    })

    socket.on('policy_created', (data) => {
      addNotification('success', `Policy ${data.policy_number} created!`)
    })

    socket.on('claim_submitted', (data) => {
      addNotification('info', `Claim ${data.claim_number} submitted`)
    })

    socket.on('claim_status_update', (data) => {
      addNotification('info', `Claim ${data.claim_number}: ${data.status}`)
    })

    // DocGen events
    socket.on('docgen_upload', (data) => {
      addNotification('info', data.message || 'Documents uploaded')
    })

    socket.on('docgen_status', (data) => {
      addNotification('info', data.message || 'Processing documents...')
    })

    socket.on('docgen_completed', (data) => {
      if (data.claim_number) {
        addNotification('success', data.message || `Claim ${data.claim_number} created!`)
      } else {
        addNotification('info', data.message || 'Document processing completed')
      }
    })

    socket.on('docgen_failed', (data) => {
      addNotification('error', data.message || 'Document processing failed')
    })

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('customer_created')
      socket.off('pet_added')
      socket.off('policy_created')
      socket.off('claim_submitted')
      socket.off('claim_status_update')
      socket.off('docgen_upload')
      socket.off('docgen_status')
      socket.off('docgen_completed')
      socket.off('docgen_failed')
      socket.disconnect()
    }
  }, [])

  const addNotification = (type, message) => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, type, message }])
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

  const navItems = user ? [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/pet-select', icon: Sparkles, label: 'Pet Recommendations' },
    { path: '/add-pet', icon: PawPrint, label: 'Add Pet' },
    { path: '/policy', icon: FileText, label: 'Buy Policy' },
    { path: '/claim', icon: AlertCircle, label: 'Submit Claim' },
    { path: '/upload-docs', icon: Upload, label: 'Submit Claim with Documents' },
  ] : [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/pet-select', icon: Sparkles, label: 'Pet Recommendations' },
    { path: '/register', icon: User, label: 'Register' },
    { path: '/login', icon: LogIn, label: 'Sign In' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <PawPrint className="h-8 w-8 text-pet-orange" />
                <span className="text-xl font-bold text-gray-900">PetInsure360</span>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-4">
              {navItems.map(({ path, icon: Icon, label }) => (
                <Link
                  key={path}
                  to={path}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors ${
                    location.pathname === path
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </Link>
              ))}

              {/* User Menu / Login Button */}
              {user ? (
                <div className="flex items-center space-x-3 ml-4 pl-4 border-l border-gray-200">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {user.full_name || `${user.first_name} ${user.last_name}`}
                    </p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center space-x-1 px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors"
                    title="Sign Out"
                  >
                    <LogOut className="h-4 w-4" />
                  </button>
                </div>
              ) : null}

              <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
                   title={isConnected ? 'Connected' : 'Disconnected'} />
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-lg text-gray-600 hover:bg-gray-100"
              >
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {user && (
                <div className="px-3 py-3 border-b border-gray-200 mb-2">
                  <p className="font-medium text-gray-900">
                    {user.full_name || `${user.first_name} ${user.last_name}`}
                  </p>
                  <p className="text-sm text-gray-500">{user.email}</p>
                </div>
              )}

              {navItems.map(({ path, icon: Icon, label }) => (
                <Link
                  key={path}
                  to={path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
                    location.pathname === path
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{label}</span>
                </Link>
              ))}

              {user && (
                <button
                  onClick={() => {
                    handleLogout()
                    setMobileMenuOpen(false)
                  }}
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 w-full"
                >
                  <LogOut className="h-5 w-5" />
                  <span>Sign Out</span>
                </button>
              )}
            </div>
          </div>
        )}
      </nav>

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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<HomePage user={user} />} />
          <Route path="/pet-select" element={<PetSelectPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
          <Route path="/add-pet" element={<AddPetPage user={user} />} />
          <Route path="/policy" element={<PolicyPage user={user} />} />
          <Route path="/claim" element={<ClaimPage user={user} />} />
          <Route path="/upload-docs" element={<UploadDocsPage user={user} addNotification={addNotification} />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-500 text-sm">
            <p>PetInsure360 - Pet Insurance Data Platform Demo</p>
            <p className="mt-1">Built by Gopinath Varadharajan | Azure + Databricks + React</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
