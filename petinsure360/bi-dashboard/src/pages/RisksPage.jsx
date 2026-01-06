import { useState, useEffect } from 'react'
import { AlertTriangle, Shield, TrendingUp } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
import api from '../services/api'

const COLORS = ['#22c55e', '#f59e0b', '#ef4444', '#7c3aed']

export default function RisksPage() {
  const [loading, setLoading] = useState(true)
  const [risks, setRisks] = useState([])
  const [crossSell, setCrossSell] = useState([])
  const [distribution, setDistribution] = useState({})
  const [activeTab, setActiveTab] = useState('risks') // 'risks' or 'crosssell'

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [risksRes, crossSellRes] = await Promise.all([
        api.get('/api/insights/risks?limit=100'),
        api.get('/api/insights/cross-sell?limit=50')
      ])
      setRisks(risksRes.data.risk_scores || [])
      setDistribution(risksRes.data.distribution || {})
      setCrossSell(crossSellRes.data.recommendations || [])
    } catch (err) {
      console.error('Error fetching data:', err)
      setDemoData()
    } finally {
      setLoading(false)
    }
  }

  const setDemoData = () => {
    setRisks([
      { customer_id: 'CUST-001', full_name: 'John Smith', total_risk_score: 35, risk_category: 'Low', claims_frequency_risk: 10, loss_ratio_risk: 15, pet_age_risk: 5, breed_risk: 5, recommendation: 'Standard renewal' },
      { customer_id: 'CUST-002', full_name: 'Jane Doe', total_risk_score: 55, risk_category: 'Medium', claims_frequency_risk: 20, loss_ratio_risk: 20, pet_age_risk: 10, breed_risk: 5, recommendation: 'Monitor' },
      { customer_id: 'CUST-003', full_name: 'Bob Johnson', total_risk_score: 78, risk_category: 'High', claims_frequency_risk: 25, loss_ratio_risk: 30, pet_age_risk: 15, breed_risk: 8, recommendation: 'Review policy terms' },
      { customer_id: 'CUST-004', full_name: 'Alice Williams', total_risk_score: 28, risk_category: 'Low', claims_frequency_risk: 8, loss_ratio_risk: 10, pet_age_risk: 5, breed_risk: 5, recommendation: 'Standard renewal' },
      { customer_id: 'CUST-005', full_name: 'Charlie Brown', total_risk_score: 92, risk_category: 'Critical', claims_frequency_risk: 25, loss_ratio_risk: 35, pet_age_risk: 20, breed_risk: 12, recommendation: 'Consider premium adjustment' },
    ])
    setDistribution({ Low: 2500, Medium: 1500, High: 750, Critical: 250 })
    setCrossSell([
      { customer_id: 'CUST-001', full_name: 'John Smith', customer_value_tier: 'Platinum', recommendation: 'Multi-Pet Discount', estimated_revenue_opportunity: 300, priority_score: 100 },
      { customer_id: 'CUST-004', full_name: 'Alice Williams', customer_value_tier: 'Gold', recommendation: 'Wellness Add-on', estimated_revenue_opportunity: 180, priority_score: 85 },
      { customer_id: 'CUST-006', full_name: 'Diana Ross', customer_value_tier: 'Gold', recommendation: 'Dental Coverage', estimated_revenue_opportunity: 150, priority_score: 80 },
    ])
  }

  const distributionData = Object.entries(distribution).map(([name, value]) => ({ name, value }))

  const getRiskColor = (category) => {
    switch (category) {
      case 'Low': return 'bg-green-100 text-green-800'
      case 'Medium': return 'bg-yellow-100 text-yellow-800'
      case 'High': return 'bg-orange-100 text-orange-800'
      case 'Critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const totalOpportunity = crossSell.reduce((sum, r) => sum + (r.estimated_revenue_opportunity || 0), 0)

  return (
    <div className="space-y-6 relative">
      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/70 z-10 flex items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
            <span className="text-sm text-gray-600">Loading risk analysis...</span>
          </div>
        </div>
      )}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Risk Analysis</h1>
        <p className="text-gray-500">Customer risk scores and cross-sell opportunities from the Gold layer</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        {Object.entries(distribution).map(([category, count]) => (
          <div key={category} className="stat-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{category} Risk</p>
                <p className="text-2xl font-bold">{count?.toLocaleString()}</p>
              </div>
              <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                category === 'Low' ? 'bg-green-100' :
                category === 'Medium' ? 'bg-yellow-100' :
                category === 'High' ? 'bg-orange-100' : 'bg-red-100'
              }`}>
                <AlertTriangle className={`h-5 w-5 ${
                  category === 'Low' ? 'text-green-600' :
                  category === 'Medium' ? 'text-yellow-600' :
                  category === 'High' ? 'text-orange-600' : 'text-red-600'
                }`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-6">
        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={distributionData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, value }) => `${name}: ${value.toLocaleString()}`}
              >
                {distributionData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.name === 'Low' ? '#22c55e' :
                      entry.name === 'Medium' ? '#f59e0b' :
                      entry.name === 'High' ? '#f97316' : '#ef4444'
                    }
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Cross-Sell Opportunities</h3>
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-gray-500">Total Revenue Opportunity</p>
              <p className="text-2xl font-bold text-green-600">${totalOpportunity.toLocaleString()}</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500" />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={crossSell.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="full_name" tick={false} />
              <YAxis />
              <Tooltip formatter={(value) => `$${value}`} />
              <Bar dataKey="estimated_revenue_opportunity" fill="#3b82f6" name="Opportunity ($)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tabbed Section: Risk Scores / Cross-Sell */}
      <div className="chart-card">
        {/* Tab Header */}
        <div className="flex border-b border-gray-200 mb-4">
          <button
            onClick={() => setActiveTab('risks')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'risks'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Customer Risk Scores ({risks.length})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('crosssell')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'crosssell'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Cross-Sell Recommendations ({crossSell.length})
            </div>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'risks' && (
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Risk Score</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Category</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Claims Risk</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Loss Ratio Risk</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Pet Age Risk</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recommendation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {risks.map(risk => (
                  <tr key={risk.customer_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div>
                        <p className="font-medium">{risk.full_name}</p>
                        <p className="text-xs text-gray-500">{risk.customer_id}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className={`px-3 py-1 text-sm font-bold rounded-full ${
                        risk.total_risk_score < 40 ? 'bg-green-100 text-green-800' :
                        risk.total_risk_score < 60 ? 'bg-yellow-100 text-yellow-800' :
                        risk.total_risk_score < 80 ? 'bg-orange-100 text-orange-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {risk.total_risk_score?.toFixed(0)}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getRiskColor(risk.risk_category)}`}>
                        {risk.risk_category}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center text-sm">{risk.claims_frequency_risk?.toFixed(0)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-center text-sm">{risk.loss_ratio_risk?.toFixed(0)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-center text-sm">{risk.pet_age_risk?.toFixed(0)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{risk.recommendation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'crosssell' && (
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Tier</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recommendation</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Est. Revenue</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Priority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {crossSell.map(rec => (
                  <tr key={rec.customer_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <p className="font-medium">{rec.full_name}</p>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                        rec.customer_value_tier === 'Platinum' ? 'bg-purple-100 text-purple-800' :
                        rec.customer_value_tier === 'Gold' ? 'bg-yellow-100 text-yellow-800' :
                        rec.customer_value_tier === 'Silver' ? 'bg-gray-200 text-gray-800' : 'bg-orange-100 text-orange-800'
                      }`}>
                        {rec.customer_value_tier}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">{rec.recommendation}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium text-green-600">
                      ${rec.estimated_revenue_opportunity?.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${rec.priority_score}%` }}
                        ></div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
