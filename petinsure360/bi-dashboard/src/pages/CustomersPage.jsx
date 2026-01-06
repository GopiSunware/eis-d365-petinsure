import { useState, useEffect } from 'react'
import { Users, Search, ChevronDown, Star, AlertTriangle, DollarSign } from 'lucide-react'
import api from '../services/api'

export default function CustomersPage() {
  const [loading, setLoading] = useState(true)
  const [customers, setCustomers] = useState([])
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [filters, setFilters] = useState({ tier: '', risk: '' })
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchCustomers()
  }, [filters])

  const fetchCustomers = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.tier) params.append('tier', filters.tier)
      if (filters.risk) params.append('risk', filters.risk)
      params.append('limit', '100')

      const response = await api.get(`/api/insights/customers?${params}`)
      setCustomers(response.data.customers || [])
    } catch (err) {
      console.error('Error fetching customers:', err)
      setDemoCustomers()
    } finally {
      setLoading(false)
    }
  }

  const setDemoCustomers = () => {
    setCustomers([
      { customer_id: 'CUST-001', full_name: 'John Smith', email: 'john@example.com', city: 'Austin', state: 'TX', customer_value_tier: 'Platinum', customer_risk_score: 'Low', total_annual_premium: 1440, total_claims: 3, loss_ratio: 45, total_pets: 2, active_policies: 2 },
      { customer_id: 'CUST-002', full_name: 'Jane Doe', email: 'jane@example.com', city: 'Seattle', state: 'WA', customer_value_tier: 'Gold', customer_risk_score: 'Medium', total_annual_premium: 960, total_claims: 5, loss_ratio: 68, total_pets: 1, active_policies: 1 },
      { customer_id: 'CUST-003', full_name: 'Bob Johnson', email: 'bob@example.com', city: 'Denver', state: 'CO', customer_value_tier: 'Silver', customer_risk_score: 'High', total_annual_premium: 600, total_claims: 8, loss_ratio: 92, total_pets: 3, active_policies: 2 },
      { customer_id: 'CUST-004', full_name: 'Alice Williams', email: 'alice@example.com', city: 'Miami', state: 'FL', customer_value_tier: 'Gold', customer_risk_score: 'Low', total_annual_premium: 1200, total_claims: 2, loss_ratio: 35, total_pets: 1, active_policies: 1 },
      { customer_id: 'CUST-005', full_name: 'Charlie Brown', email: 'charlie@example.com', city: 'Portland', state: 'OR', customer_value_tier: 'Bronze', customer_risk_score: 'Critical', total_annual_premium: 360, total_claims: 12, loss_ratio: 145, total_pets: 2, active_policies: 1 },
    ])
  }

  // Filter by search term and sort by customer_since (newest first)
  const searchLower = searchTerm.toLowerCase()
  const filteredCustomers = customers
    .filter(c => {
      if (!searchTerm) return true
      return (
        c.full_name?.toLowerCase().includes(searchLower) ||
        c.email?.toLowerCase().includes(searchLower) ||
        c.customer_id?.toLowerCase().includes(searchLower) ||
        c.city?.toLowerCase().includes(searchLower) ||
        c.state?.toLowerCase().includes(searchLower)
      )
    })
    .sort((a, b) => {
      // Sort by customer_since descending (newest first)
      const dateA = a.customer_since || '1900-01-01'
      const dateB = b.customer_since || '1900-01-01'
      return new Date(dateB) - new Date(dateA)
    })

  const getTierColor = (tier) => {
    switch (tier) {
      case 'Platinum': return 'bg-purple-100 text-purple-800'
      case 'Gold': return 'bg-yellow-100 text-yellow-800'
      case 'Silver': return 'bg-gray-200 text-gray-800'
      case 'Bronze': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'Low': return 'bg-green-100 text-green-800'
      case 'Medium': return 'bg-yellow-100 text-yellow-800'
      case 'High': return 'bg-orange-100 text-orange-800'
      case 'Critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  return (
    <div className="space-y-6 relative">
      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/70 z-10 flex items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
            <span className="text-sm text-gray-600">Loading customers...</span>
          </div>
        </div>
      )}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Customer 360</h1>
        <p className="text-gray-500">Unified customer profiles from the Gold layer</p>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search customers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <select
          value={filters.tier}
          onChange={(e) => setFilters(f => ({ ...f, tier: e.target.value }))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Tiers</option>
          <option value="Platinum">Platinum</option>
          <option value="Gold">Gold</option>
          <option value="Silver">Silver</option>
          <option value="Bronze">Bronze</option>
        </select>

        <select
          value={filters.risk}
          onChange={(e) => setFilters(f => ({ ...f, risk: e.target.value }))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Risk Levels</option>
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
          <option value="Critical">Critical</option>
        </select>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Customer List */}
        <div className="col-span-2">
          <div className="chart-card">
            <h3 className="text-lg font-semibold mb-4">Customers ({filteredCustomers.length})</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Member Since</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Tier</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Risk</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Premium</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Loss Ratio</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredCustomers.map(customer => (
                    <tr
                      key={customer.customer_id}
                      onClick={() => setSelectedCustomer(customer)}
                      className={`cursor-pointer hover:bg-gray-50 ${
                        selectedCustomer?.customer_id === customer.customer_id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium">{customer.full_name}</p>
                          <p className="text-xs text-gray-500">{customer.email}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {customer.customer_since ? new Date(customer.customer_since).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {customer.city}, {customer.state}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 text-xs font-medium rounded ${getTierColor(customer.customer_value_tier)}`}>
                          {customer.customer_value_tier}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 text-xs font-medium rounded ${getRiskColor(customer.customer_risk_score)}`}>
                          {customer.customer_risk_score}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-sm font-medium">
                        ${customer.total_annual_premium?.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={`px-2 py-1 text-xs rounded ${
                          customer.loss_ratio > 100 ? 'bg-red-100 text-red-800' :
                          customer.loss_ratio > 70 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {customer.loss_ratio?.toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Customer Detail */}
        <div className="col-span-1">
          <div className="chart-card sticky top-4">
            <h3 className="text-lg font-semibold mb-4">Customer Detail</h3>
            {selectedCustomer ? (
              <div className="space-y-4">
                <div className="text-center pb-4 border-b">
                  <div className="h-16 w-16 mx-auto rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-2xl font-bold">
                    {selectedCustomer.full_name?.charAt(0)}
                  </div>
                  <h4 className="mt-2 font-semibold text-lg">{selectedCustomer.full_name}</h4>
                  <p className="text-sm text-gray-500">{selectedCustomer.customer_id}</p>
                  <div className="mt-2 flex justify-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded ${getTierColor(selectedCustomer.customer_value_tier)}`}>
                      {selectedCustomer.customer_value_tier}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded ${getRiskColor(selectedCustomer.customer_risk_score)}`}>
                      {selectedCustomer.customer_risk_score} Risk
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Total Pets</p>
                    <p className="font-semibold">{selectedCustomer.total_pets}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Active Policies</p>
                    <p className="font-semibold">{selectedCustomer.active_policies}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Annual Premium</p>
                    <p className="font-semibold text-green-600">${selectedCustomer.total_annual_premium?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Total Claims</p>
                    <p className="font-semibold">{selectedCustomer.total_claims}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Loss Ratio</p>
                    <p className={`font-semibold ${selectedCustomer.loss_ratio > 70 ? 'text-red-600' : 'text-green-600'}`}>
                      {selectedCustomer.loss_ratio?.toFixed(0)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Location</p>
                    <p className="font-semibold">{selectedCustomer.city}, {selectedCustomer.state}</p>
                  </div>
                </div>

                {selectedCustomer.loss_ratio > 70 && (
                  <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
                    <div className="flex items-center text-yellow-800">
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      <span className="text-sm font-medium">High Loss Ratio Alert</span>
                    </div>
                    <p className="text-xs text-yellow-700 mt-1">
                      Consider reviewing policy terms or premium adjustments.
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Users className="h-12 w-12 mx-auto text-gray-300 mb-2" />
                <p>Select a customer to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
