import { useState, useEffect, useCallback } from 'react'
import { TrendingUp, TrendingDown, Users, FileText, DollarSign, Clock, AlertTriangle, CheckCircle, Wifi, WifiOff, RefreshCw } from 'lucide-react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../services/api'
import { connectSocket, subscribeToEvent, BI_EVENTS, getConnectionStatus } from '../services/socket'

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444']

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [kpis, setKpis] = useState([])
  const [segments, setSegments] = useState([])
  const [summary, setSummary] = useState({})
  const [wsConnected, setWsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [notifications, setNotifications] = useState([])

  // Add notification
  const addNotification = useCallback((message, type = 'info') => {
    const id = Date.now()
    setNotifications(prev => [...prev.slice(-4), { id, message, type }])
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id))
    }, 5000)
  }, [])

  // Fetch data with notification
  const fetchData = useCallback(async (showNotification = false) => {
    try {
      const [kpisRes, segmentsRes, summaryRes] = await Promise.all([
        api.get('/api/insights/kpis?limit=12'),
        api.get('/api/insights/segments'),
        api.get('/api/insights/summary')
      ])
      setKpis(kpisRes.data.kpis || [])
      setSegments(segmentsRes.data.segments || [])
      setSummary(summaryRes.data || {})
      setLastUpdate(new Date())
      if (showNotification) {
        addNotification('Dashboard data refreshed', 'success')
      }
    } catch (err) {
      console.error('Error fetching data:', err)
      setDemoData()
    } finally {
      setLoading(false)
    }
  }, [addNotification])

  // Setup WebSocket connection and event handlers
  useEffect(() => {
    // Connect to WebSocket
    connectSocket()

    // Check connection status periodically
    const checkConnection = setInterval(() => {
      const status = getConnectionStatus()
      setWsConnected(status.isConnected)
    }, 2000)

    // Subscribe to real-time events
    const unsubCustomer = subscribeToEvent(BI_EVENTS.CUSTOMER_CREATED, (data) => {
      addNotification(`New customer registered: ${data.first_name} ${data.last_name}`, 'info')
      fetchData(false)
    })

    const unsubPet = subscribeToEvent(BI_EVENTS.PET_ADDED, (data) => {
      addNotification(`New pet added: ${data.pet_name}`, 'info')
      fetchData(false)
    })

    const unsubPolicy = subscribeToEvent(BI_EVENTS.POLICY_CREATED, (data) => {
      addNotification(`New policy created: ${data.policy_number}`, 'success')
      fetchData(false)
    })

    const unsubClaim = subscribeToEvent(BI_EVENTS.CLAIM_SUBMITTED, (data) => {
      addNotification(`New claim submitted: $${data.claim_amount}`, 'warning')
      fetchData(false)
    })

    // Initial data fetch
    fetchData()

    // Cleanup
    return () => {
      clearInterval(checkConnection)
      unsubCustomer()
      unsubPet()
      unsubPolicy()
      unsubClaim()
    }
  }, [fetchData, addNotification])

  const setDemoData = () => {
    setKpis([
      { year_month: '2024-12', total_claims: 1250, total_claim_amount: 425000, total_paid_amount: 289000, approval_rate: 78, loss_ratio: 68 },
      { year_month: '2024-11', total_claims: 1180, total_claim_amount: 398000, total_paid_amount: 271000, approval_rate: 76, loss_ratio: 68 },
      { year_month: '2024-10', total_claims: 1320, total_claim_amount: 445000, total_paid_amount: 302000, approval_rate: 79, loss_ratio: 68 },
      { year_month: '2024-09', total_claims: 1150, total_claim_amount: 385000, total_paid_amount: 262000, approval_rate: 77, loss_ratio: 68 },
      { year_month: '2024-08', total_claims: 1280, total_claim_amount: 432000, total_paid_amount: 294000, approval_rate: 78, loss_ratio: 68 },
      { year_month: '2024-07', total_claims: 1100, total_claim_amount: 370000, total_paid_amount: 252000, approval_rate: 75, loss_ratio: 68 },
    ])
    setSegments([
      { tier: 'Platinum', count: 750, total_premium: 720000, avg_loss_ratio: 55 },
      { tier: 'Gold', count: 1250, total_premium: 900000, avg_loss_ratio: 62 },
      { tier: 'Silver', count: 1750, total_premium: 735000, avg_loss_ratio: 70 },
      { tier: 'Bronze', count: 1250, total_premium: 375000, avg_loss_ratio: 82 },
    ])
    setSummary({ total_customers: 5000, total_pets: 6500, total_policies: 6000, total_claims: 15000, total_providers: 200 })
  }

  const latestKpi = kpis[0] || {}
  const previousKpi = kpis[1] || {}

  const claimsChange = previousKpi.total_claims
    ? ((latestKpi.total_claims - previousKpi.total_claims) / previousKpi.total_claims * 100).toFixed(1)
    : 0

  return (
    <div className="space-y-6 relative">
      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/70 z-10 flex items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
            <span className="text-sm text-gray-600">Loading dashboard...</span>
          </div>
        </div>
      )}
      {/* Notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {notifications.map(n => (
          <div
            key={n.id}
            className={`px-4 py-2 rounded-lg shadow-lg text-white text-sm animate-slide-in ${
              n.type === 'success' ? 'bg-green-500' :
              n.type === 'warning' ? 'bg-yellow-500' :
              n.type === 'error' ? 'bg-red-500' :
              'bg-blue-500'
            }`}
          >
            {n.message}
          </div>
        ))}
      </div>

      {/* Header with Connection Status */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Executive Dashboard</h1>
          <p className="text-gray-500">Key performance indicators from the Gold layer</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Connection Status */}
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
            wsConnected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
          }`}>
            {wsConnected ? (
              <>
                <Wifi className="h-4 w-4" />
                <span>Live</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4" />
                <span>Offline</span>
              </>
            )}
          </div>
          {/* Refresh Button */}
          <button
            onClick={() => fetchData(true)}
            className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          {/* Last Update */}
          {lastUpdate && (
            <span className="text-sm text-gray-400">
              Updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Claims</p>
              <p className="text-3xl font-bold">{summary.total_claims?.toLocaleString() || '15,000'}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-2 flex items-center text-sm">
            {parseFloat(claimsChange) >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
            )}
            <span className={parseFloat(claimsChange) >= 0 ? 'text-green-600' : 'text-red-600'}>
              {claimsChange}% vs last month
            </span>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Customers</p>
              <p className="text-3xl font-bold">{summary.total_customers?.toLocaleString() || '5,000'}</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
              <Users className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            {summary.total_pets?.toLocaleString() || '6,500'} pets insured
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Approval Rate</p>
              <p className="text-3xl font-bold">{latestKpi.approval_rate || 78}%</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-yellow-100 flex items-center justify-center">
              <CheckCircle className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            Target: 80%
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Loss Ratio</p>
              <p className="text-3xl font-bold">{latestKpi.loss_ratio || 68}%</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
              <DollarSign className="h-6 w-6 text-red-600" />
            </div>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            Target: &lt; 70%
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Claims Trend */}
        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Claims Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={[...kpis].reverse()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year_month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="total_claims" stroke="#3b82f6" name="Total Claims" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Customer Segments */}
        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Customer Segments</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={segments}
                dataKey="count"
                nameKey="tier"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ tier, count }) => `${tier}: ${count}`}
              >
                {segments.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Second Charts Row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Premium by Segment */}
        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Premium by Segment</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={segments}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tier" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="total_premium" fill="#3b82f6" name="Total Premium" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Loss Ratio by Segment */}
        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Loss Ratio by Segment</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={segments}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tier" />
              <YAxis />
              <Tooltip formatter={(value) => `${value}%`} />
              <Legend />
              <Bar dataKey="avg_loss_ratio" name="Loss Ratio %">
                {segments.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.avg_loss_ratio > 70 ? '#ef4444' : entry.avg_loss_ratio > 60 ? '#f59e0b' : '#22c55e'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly KPIs Table */}
      <div className="chart-card">
        <h3 className="text-lg font-semibold mb-4">Monthly KPIs</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Month</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Claims</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Claim Amount</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Paid Amount</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Approval Rate</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Loss Ratio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {kpis.map((kpi, idx) => (
                <tr key={kpi.year_month} className={idx === 0 ? 'bg-blue-50' : ''}>
                  <td className="px-4 py-3 whitespace-nowrap font-medium">{kpi.year_month}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">{kpi.total_claims?.toLocaleString()}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">${kpi.total_claim_amount?.toLocaleString()}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">${kpi.total_paid_amount?.toLocaleString()}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">{kpi.approval_rate}%</td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">
                    <span className={`px-2 py-1 rounded ${
                      kpi.loss_ratio > 70 ? 'bg-red-100 text-red-800' :
                      kpi.loss_ratio > 60 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {kpi.loss_ratio}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
