import { useState, useEffect } from 'react'
import { FileText, Search, Filter, Database, Bot, RefreshCw } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import api from '../services/api'

const DOCGEN_URL = import.meta.env.VITE_DOCGEN_URL || 'http://localhost:8007'
// Agent Pipeline URL - VITE_PIPELINE_URL has /api suffix, we need base URL for /api/v1/pipeline/recent
const AGENT_PIPELINE_URL = (import.meta.env.VITE_PIPELINE_URL || 'http://localhost:8006/api').replace(/\/api$/, '')

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6', '#6366f1']

export default function ClaimsPage() {
  const [loading, setLoading] = useState(true)
  const [claims, setClaims] = useState([])
  const [filters, setFilters] = useState({ status: '', category: '', pipeline: '' })
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchClaims()
  }, [filters.status, filters.category])

  const fetchClaims = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.status) params.append('status', filters.status)
      if (filters.category) params.append('category', filters.category)
      params.append('limit', '100')

      // Fetch from main insights API (Gold layer claims)
      const response = await api.get(`/api/insights/claims?${params}`)
      let allClaims = (response.data.claims || []).map(c => ({
        ...c,
        processing_method: 'rule',
        pipeline_source: 'Rule Engine Pipeline'
      }))

      // Fetch from pipeline pending claims (Bronze/Silver)
      // Note: Backend now includes customer_name and pet_name in claim data
      try {
        const pipelineRes = await api.get('/api/pipeline/pending')

        const mapPipelineClaim = (c, layer) => ({
          ...c,
          processing_method: 'rule',
          pipeline_source: 'Rule Engine Pipeline',
          status: layer,
          submission_date: c.ingestion_timestamp || c.service_date
        })

        const bronzeClaims = (pipelineRes.data.bronze || []).map(c => mapPipelineClaim(c, 'Bronze'))
        const silverClaims = (pipelineRes.data.silver || []).map(c => mapPipelineClaim(c, 'Silver'))
        allClaims = [...bronzeClaims, ...silverClaims, ...allClaims]
      } catch (e) {
        console.log('Pipeline data not available')
      }

      // Fetch from DocGen batches (AI document processing)
      try {
        const docgenRes = await fetch(`${DOCGEN_URL}/api/v1/docgen/batches?limit=100`)
        if (docgenRes.ok) {
          const docgenData = await docgenRes.json()
          const docgenClaims = (docgenData.batches || []).map(b => ({
            claim_id: b.batch_id,
            claim_number: b.claim_number || b.claim_data?.claim_number,
            claim_type: b.claim_type || b.claim_data?.claim_type || 'Unknown',
            claim_category: b.claim_category || b.claim_data?.claim_category || '-',
            claim_amount: b.claim_amount || b.claim_data?.claim_amount,
            customer_id: b.claim_data?.customer_id,
            customer_name: b.claim_data?.customer_name || '-',
            pet_id: b.claim_data?.pet_id,
            pet_name: b.claim_data?.pet_name || '-',
            paid_amount: 0,
            status: b.ai_decision || b.status,
            submission_date: b.created_at,
            service_date: b.created_at,
            processing_method: 'agent',
            pipeline_source: 'DocGen Pipeline',
            ai_confidence: b.ai_confidence,
            ai_reasoning: b.ai_reasoning
          }))
          allClaims = [...allClaims, ...docgenClaims]
        }
      } catch (e) {
        console.log('DocGen data not available')
      }

      // Fetch from Agent Pipeline (WS6 - LangGraph medallion pipeline)
      try {
        const agentPipelineRes = await fetch(`${AGENT_PIPELINE_URL}/api/v1/pipeline/recent?limit=100`)
        if (agentPipelineRes.ok) {
          const agentPipelineData = await agentPipelineRes.json()
          const agentPipelineClaims = (agentPipelineData.runs || []).map(run => {
            const claimData = run.claim_data || {}
            const goldOutput = run.gold_output || {}
            const silverOutput = run.silver_output || {}
            return {
              claim_id: run.claim_id,
              claim_number: claimData.claim_number || run.claim_id,
              claim_type: claimData.claim_type || 'Unknown',
              claim_category: claimData.claim_category || claimData.category || '-',
              claim_amount: claimData.claim_amount || 0,
              customer_id: claimData.customer_id,
              customer_name: claimData.customer_name || '-',
              pet_id: claimData.pet_id,
              pet_name: claimData.pet_name || '-',
              paid_amount: silverOutput.estimated_reimbursement || 0,
              status: goldOutput.decision || goldOutput.final_decision || run.status || 'Processing',
              submission_date: run.started_at,
              service_date: claimData.service_date,
              processing_method: 'agent',
              pipeline_source: 'Agent Pipeline (LangGraph)',
              ai_confidence: goldOutput.confidence,
              ai_reasoning: goldOutput.reasoning,
              risk_level: goldOutput.risk_level,
              agent_run_id: run.run_id,
              processing_time_ms: run.total_processing_time_ms
            }
          })
          allClaims = [...allClaims, ...agentPipelineClaims]
        }
      } catch (e) {
        console.log('Agent Pipeline (WS6) data not available:', e.message)
      }

      // Deduplicate by claim_number (prefer rule-based if both exist)
      const claimMap = new Map()
      allClaims.forEach(c => {
        const key = c.claim_number || c.claim_id
        if (!claimMap.has(key)) {
          claimMap.set(key, c)
        } else {
          // If we already have this claim, merge info
          const existing = claimMap.get(key)
          if (c.processing_method === 'agent' && existing.processing_method === 'rule') {
            existing.has_agent = true
            existing.ai_decision = c.status
            existing.ai_confidence = c.ai_confidence
          } else if (c.processing_method === 'rule' && existing.processing_method === 'agent') {
            claimMap.set(key, { ...c, has_agent: true, ai_decision: existing.status, ai_confidence: existing.ai_confidence })
          }
        }
      })

      setClaims(Array.from(claimMap.values()))
    } catch (err) {
      console.error('Error fetching claims:', err)
      setDemoClaims()
    } finally {
      setLoading(false)
    }
  }

  const setDemoClaims = () => {
    setClaims([
      { claim_id: 'CLM-001', claim_number: 'CLM-20241220-ABC', customer_name: 'John Smith', pet_name: 'Buddy', species: 'Dog', claim_type: 'Illness', claim_category: 'Digestive', service_date: '2024-12-15', claim_amount: 450, paid_amount: 360, status: 'Paid', processing_days: 3 },
      { claim_id: 'CLM-002', claim_number: 'CLM-20241219-DEF', customer_name: 'Jane Doe', pet_name: 'Whiskers', species: 'Cat', claim_type: 'Accident', claim_category: 'Laceration', service_date: '2024-12-14', claim_amount: 280, paid_amount: 224, status: 'Paid', processing_days: 2 },
      { claim_id: 'CLM-003', claim_number: 'CLM-20241218-GHI', customer_name: 'Bob Johnson', pet_name: 'Max', species: 'Dog', claim_type: 'Wellness', claim_category: 'Annual Exam', service_date: '2024-12-12', claim_amount: 150, paid_amount: 120, status: 'Approved', processing_days: 4 },
      { claim_id: 'CLM-004', claim_number: 'CLM-20241217-JKL', customer_name: 'Alice Williams', pet_name: 'Luna', species: 'Cat', claim_type: 'Illness', claim_category: 'Respiratory', service_date: '2024-12-10', claim_amount: 580, paid_amount: 0, status: 'Under Review', processing_days: null },
      { claim_id: 'CLM-005', claim_number: 'CLM-20241216-MNO', customer_name: 'Charlie Brown', pet_name: 'Rocky', species: 'Dog', claim_type: 'Dental', claim_category: 'Cleaning', service_date: '2024-12-08', claim_amount: 320, paid_amount: 0, status: 'Denied', processing_days: 5, denial_reason: 'Pre-existing condition' },
    ])
  }

  // Calculate stats - Group by claim_type (not category) and limit to top 8
  const claimsByType = claims.reduce((acc, claim) => {
    const type = claim.claim_type || 'Other'
    acc[type] = (acc[type] || 0) + 1
    return acc
  }, {})

  const claimsByStatus = claims.reduce((acc, claim) => {
    const status = claim.status || 'Unknown'
    acc[status] = (acc[status] || 0) + 1
    return acc
  }, {})

  // Sort by count and take top 8, group rest as "Other"
  const sortedTypes = Object.entries(claimsByType).sort((a, b) => b[1] - a[1])
  const topTypes = sortedTypes.slice(0, 8)
  const otherCount = sortedTypes.slice(8).reduce((sum, [, count]) => sum + count, 0)
  if (otherCount > 0) {
    topTypes.push(['Other', otherCount])
  }

  const typeChartData = topTypes.map(([name, value]) => ({ name, value }))
  const statusChartData = Object.entries(claimsByStatus).map(([name, value]) => ({ name, value }))

  // Filter by search term, pipeline, and sort by submission date (newest first)
  const searchLower = searchTerm.toLowerCase()
  const filteredClaims = claims
    .filter(c => {
      // Search filter
      if (searchTerm) {
        const matches = (
          c.claim_id?.toLowerCase().includes(searchLower) ||
          c.claim_number?.toLowerCase().includes(searchLower) ||
          c.customer_name?.toLowerCase().includes(searchLower) ||
          c.pet_name?.toLowerCase().includes(searchLower) ||
          c.claim_category?.toLowerCase().includes(searchLower)
        )
        if (!matches) return false
      }
      // Pipeline filter
      if (filters.pipeline) {
        if (filters.pipeline === 'both') {
          return c.has_agent === true
        }
        return c.processing_method === filters.pipeline
      }
      return true
    })
    .sort((a, b) => {
      // Sort by full datetime (newest first) - use all available timestamp sources
      const dateA = a.submission_date || a.ingestion_timestamp || a.created_at || a.service_date || '1900-01-01'
      const dateB = b.submission_date || b.ingestion_timestamp || b.created_at || b.service_date || '1900-01-01'
      const dateCompare = new Date(dateB) - new Date(dateA)
      if (dateCompare !== 0) return dateCompare
      // Secondary sort by claim_number descending (to handle same-second submissions)
      return (b.claim_number || '').localeCompare(a.claim_number || '')
    })

  const getStatusColor = (status) => {
    switch (status) {
      case 'Paid': return 'bg-green-100 text-green-800'
      case 'Approved': return 'bg-blue-100 text-blue-800'
      case 'Under Review': return 'bg-yellow-100 text-yellow-800'
      case 'Denied': return 'bg-red-100 text-red-800'
      case 'Submitted': return 'bg-gray-100 text-gray-800'
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
            <span className="text-sm text-gray-600">Loading claims...</span>
          </div>
        </div>
      )}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Claims Analytics</h1>
          <p className="text-gray-500">Detailed claims data from the Gold layer</p>
        </div>
        <button
          onClick={fetchClaims}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Summary Charts */}
      <div className="grid grid-cols-2 gap-6">
        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Claims by Type (Top 8)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={typeChartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="45%"
                outerRadius={90}
                innerRadius={40}
              >
                {typeChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value, name) => [`${value} claims`, name]} />
              <Legend
                layout="horizontal"
                verticalAlign="bottom"
                align="center"
                wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Claims by Status</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={statusChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" name="Count">
                {statusChartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.name === 'Paid' ? '#22c55e' :
                      entry.name === 'Approved' ? '#3b82f6' :
                      entry.name === 'Under Review' ? '#f59e0b' :
                      entry.name === 'Denied' ? '#ef4444' : '#9ca3af'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search claims..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <select
          value={filters.status}
          onChange={(e) => setFilters(f => ({ ...f, status: e.target.value }))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="Submitted">Submitted</option>
          <option value="Under Review">Under Review</option>
          <option value="Approved">Approved</option>
          <option value="Denied">Denied</option>
          <option value="Paid">Paid</option>
        </select>

        <select
          value={filters.category}
          onChange={(e) => setFilters(f => ({ ...f, category: e.target.value }))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Categories</option>
          <option value="Toxicity/Poisoning">Toxicity/Poisoning</option>
          <option value="Orthopedic Surgery">Orthopedic Surgery</option>
          <option value="Gastrointestinal">Gastrointestinal</option>
          <option value="Emergency">Emergency</option>
          <option value="Oncology">Oncology</option>
          <option value="Dermatology">Dermatology</option>
          <option value="Dental">Dental</option>
          <option value="Digestive">Digestive</option>
          <option value="Respiratory">Respiratory</option>
          <option value="Laceration">Laceration</option>
          <option value="Annual Exam">Annual Exam</option>
          <option value="Preventive">Preventive</option>
          <option value="Illness">Illness</option>
        </select>

        <select
          value={filters.pipeline}
          onChange={(e) => setFilters(f => ({ ...f, pipeline: e.target.value }))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Pipelines</option>
          <option value="rule">Rule-Based</option>
          <option value="agent">AI Agent</option>
          <option value="both">Both</option>
        </select>
      </div>

      {/* Claims Table */}
      <div className="chart-card">
        <h3 className="text-lg font-semibold mb-4">Claims ({filteredClaims.length})</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Claim #</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Submitted</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pet</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Paid</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Pipeline</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredClaims.map(claim => (
                <tr key={claim.claim_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="font-mono text-sm">{claim.claim_number}</span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                    {(() => {
                      const dateStr = claim.submission_date || claim.ingestion_timestamp || claim.service_date
                      if (!dateStr) return '-'
                      const d = new Date(dateStr)
                      // Show date and time for better sorting visibility
                      return d.toLocaleString('en-US', {
                        month: 'numeric',
                        day: 'numeric',
                        year: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit'
                      })
                    })()}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">{claim.customer_name}</td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-sm">{claim.pet_name}</span>
                      <span className="ml-1 text-xs text-gray-400">({claim.species})</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">{claim.claim_type}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{claim.claim_category}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium">
                    ${claim.claim_amount?.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium text-green-600">
                    ${claim.paid_amount?.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(claim.status)}`}>
                      {claim.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center gap-1">
                      {claim.processing_method === 'rule' && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800">
                          <Database className="h-3 w-3" /> Rule
                        </span>
                      )}
                      {claim.processing_method === 'agent' && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-purple-100 text-purple-800">
                          <Bot className="h-3 w-3" /> Agent
                        </span>
                      )}
                      {claim.has_agent && claim.processing_method === 'rule' && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-purple-100 text-purple-800">
                          <Bot className="h-3 w-3" /> Agent
                        </span>
                      )}
                    </div>
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
