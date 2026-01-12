import { useState, useEffect } from 'react'
import { GitCompare, Database, Bot, CheckCircle, XCircle, AlertTriangle, Clock, RefreshCw, Brain, Zap } from 'lucide-react'
import api from '../services/api'

// Agent Pipeline URL (LangGraph agents) - NOT DocGen
const PIPELINE_URL = (import.meta.env.VITE_PIPELINE_URL || 'http://localhost:8006/api').replace(/\/api$/, '')

export default function ComparisonPage() {
  const [loading, setLoading] = useState(true)
  const [rulesClaims, setRulesClaims] = useState([])
  const [agentRuns, setAgentRuns] = useState([])
  const [comparisons, setComparisons] = useState([])

  useEffect(() => {
    fetchComparisonData()
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchComparisonData, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchComparisonData = async () => {
    try {
      // Fetch rule-based pipeline claims (all layers)
      const pipelineRes = await api.get('/api/pipeline/pending')
      const allRulesClaims = [
        ...(pipelineRes.data.bronze || []),
        ...(pipelineRes.data.silver || []),
        ...(pipelineRes.data.gold || [])
      ]
      setRulesClaims(allRulesClaims)

      // Fetch Agent Pipeline runs from LangGraph service (port 8006)
      let agentRunsList = []
      try {
        const agentRes = await fetch(`${PIPELINE_URL}/api/v1/pipeline/recent?limit=50`)
        if (agentRes.ok) {
          const agentData = await agentRes.json()
          agentRunsList = agentData.runs || []
          setAgentRuns(agentRunsList)
        }
      } catch (err) {
        console.error('Error fetching agent pipeline runs:', err)
      }

      // Build comparison data by matching claim numbers/IDs
      buildComparisons(allRulesClaims, agentRunsList)
    } catch (err) {
      console.error('Error fetching comparison data:', err)
    } finally {
      setLoading(false)
    }
  }

  const buildComparisons = (rules, agents) => {
    const comparisonMap = new Map()

    // Add rule-based claims
    rules.forEach(claim => {
      const key = claim.claim_number || claim.claim_id
      comparisonMap.set(key, {
        claim_number: key,
        claim_id: claim.claim_id,
        claim_amount: claim.claim_amount,
        claim_category: claim.claim_category,
        customer_id: claim.customer_id,
        rules: {
          status: claim.layer === 'gold' ? 'Completed' : claim.layer === 'silver' ? 'Validated' : 'Pending',
          layer: claim.layer,
          quality_score: claim.overall_quality_score,
          reimbursement: claim.estimated_reimbursement,
          decision: claim.layer === 'gold' ? 'Approved' : 'Processing'
        },
        agent: null
      })
    })

    // Add agent pipeline runs - match by claim_number from claim_data
    agents.forEach(run => {
      const claimData = run.claim_data || {}
      const key = claimData.claim_number || run.claim_id

      // Extract decision from gold_output or final_decision
      const goldOutput = run.gold_output || {}
      const finalDecision = run.final_decision || goldOutput.final_decision
      const confidence = goldOutput.confidence
      const approvedAmount = goldOutput.approved_amount

      // Determine status
      let status = run.status
      if (run.status === 'completed') status = 'Completed'
      else if (run.status === 'running') status = 'Processing'
      else if (run.status === 'failed') status = 'Failed'
      else status = 'Pending'

      // Format decision for display
      let displayDecision = finalDecision
      if (finalDecision === 'auto_approve' || finalDecision === 'approve') displayDecision = 'Approved'
      else if (finalDecision === 'deny' || finalDecision === 'reject') displayDecision = 'Denied'
      else if (finalDecision === 'needs_review' || finalDecision === 'manual_review') displayDecision = 'Review'
      else if (finalDecision === 'flag') displayDecision = 'Flagged'

      const agentData = {
        status: status,
        decision: displayDecision,
        confidence: confidence,
        approved_amount: approvedAmount,
        run_id: run.run_id,
        current_stage: run.current_stage,
        reasoning: goldOutput.reasoning,
        fraud_score: run.fraud_score,
        risk_level: run.risk_level
      }

      if (comparisonMap.has(key)) {
        comparisonMap.get(key).agent = agentData
      } else {
        comparisonMap.set(key, {
          claim_number: key,
          claim_id: run.claim_id,
          claim_amount: claimData.claim_amount,
          claim_category: claimData.claim_category || claimData.claim_type,
          customer_id: claimData.customer_id,
          rules: null,
          agent: agentData
        })
      }
    })

    setComparisons(Array.from(comparisonMap.values()))
  }

  const getDecisionIcon = (decision) => {
    if (!decision) return <Clock className="h-5 w-5 text-gray-400" />
    const d = decision.toLowerCase()
    if (d === 'approved' || d === 'approve' || d === 'auto_approve') {
      return <CheckCircle className="h-5 w-5 text-green-500" />
    }
    if (d === 'denied' || d === 'deny' || d === 'reject' || d === 'flagged' || d === 'flag') {
      return <XCircle className="h-5 w-5 text-red-500" />
    }
    if (d === 'review' || d === 'needs_review' || d === 'manual_review') {
      return <AlertTriangle className="h-5 w-5 text-yellow-500" />
    }
    if (d === 'processing') {
      return <Zap className="h-5 w-5 text-blue-500 animate-pulse" />
    }
    return <Clock className="h-5 w-5 text-gray-400" />
  }

  const getStatusBadge = (status) => {
    if (!status) return null
    const colors = {
      'completed': 'bg-green-100 text-green-800',
      'processing': 'bg-blue-100 text-blue-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'validated': 'bg-purple-100 text-purple-800',
      'failed': 'bg-red-100 text-red-800',
    }
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${colors[status.toLowerCase()] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    )
  }

  // Count stats
  const matchedCount = comparisons.filter(c => c.rules && c.agent).length
  const conflictCount = comparisons.filter(c => {
    if (!c.rules || !c.agent || !c.rules.decision || !c.agent.decision) return false
    const rulesD = c.rules.decision.toLowerCase()
    const agentD = c.agent.decision.toLowerCase()
    // Normalize for comparison
    const normalizeDecision = (d) => {
      if (d === 'approved' || d === 'approve' || d === 'auto_approve') return 'approved'
      if (d === 'denied' || d === 'deny' || d === 'reject') return 'denied'
      if (d === 'review' || d === 'needs_review' || d === 'manual_review') return 'review'
      return d
    }
    return normalizeDecision(rulesD) !== normalizeDecision(agentD)
  }).length

  return (
    <div className="space-y-6 relative">
      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/70 z-10 flex items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
            <span className="text-sm text-gray-600">Loading comparison data...</span>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <GitCompare className="h-7 w-7 text-purple-600" />
            Rule vs Agent Comparison
          </h1>
          <p className="text-gray-500">Side-by-side comparison of rule-based vs AI-driven processing</p>
        </div>
        <button
          onClick={fetchComparisonData}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow p-4 border-l-4 border-blue-500">
          <div className="flex items-center gap-2 text-blue-600 mb-1">
            <Database className="h-5 w-5" />
            <span className="text-sm font-medium">Rule-Based</span>
          </div>
          <p className="text-2xl font-bold">{rulesClaims.length}</p>
          <p className="text-xs text-gray-500">Claims in pipeline</p>
        </div>
        <div className="bg-white rounded-xl shadow p-4 border-l-4 border-purple-500">
          <div className="flex items-center gap-2 text-purple-600 mb-1">
            <Bot className="h-5 w-5" />
            <span className="text-sm font-medium">AI Agent</span>
          </div>
          <p className="text-2xl font-bold">{agentRuns.length}</p>
          <p className="text-xs text-gray-500">Pipeline runs</p>
        </div>
        <div className="bg-white rounded-xl shadow p-4 border-l-4 border-green-500">
          <div className="flex items-center gap-2 text-green-600 mb-1">
            <CheckCircle className="h-5 w-5" />
            <span className="text-sm font-medium">Matched</span>
          </div>
          <p className="text-2xl font-bold">{matchedCount}</p>
          <p className="text-xs text-gray-500">Both pipelines</p>
        </div>
        <div className="bg-white rounded-xl shadow p-4 border-l-4 border-yellow-500">
          <div className="flex items-center gap-2 text-yellow-600 mb-1">
            <AlertTriangle className="h-5 w-5" />
            <span className="text-sm font-medium">Differences</span>
          </div>
          <p className="text-2xl font-bold">{conflictCount}</p>
          <p className="text-xs text-gray-500">Decision conflicts</p>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <div className="px-6 py-4 border-b bg-gray-50">
          <h3 className="text-lg font-semibold">Claim Processing Comparison</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Claim #</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase" colSpan="2">
                  <span className="flex items-center justify-center gap-1">
                    <Database className="h-4 w-4" /> Rule-Based
                  </span>
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase" colSpan="2">
                  <span className="flex items-center justify-center gap-1">
                    <Bot className="h-4 w-4" /> AI Agent
                  </span>
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Match</th>
              </tr>
              <tr className="bg-gray-100">
                <th></th>
                <th></th>
                <th className="px-4 py-2 text-xs text-gray-500">Status</th>
                <th className="px-4 py-2 text-xs text-gray-500">Decision</th>
                <th className="px-4 py-2 text-xs text-gray-500">Status</th>
                <th className="px-4 py-2 text-xs text-gray-500">Decision</th>
                <th></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {comparisons.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center text-gray-500">
                    No claims to compare. Submit a claim to see comparison.
                  </td>
                </tr>
              ) : (
                comparisons.map((comp, idx) => {
                  // Check if decisions match (with normalization)
                  const normalizeDecision = (d) => {
                    if (!d) return null
                    d = d.toLowerCase()
                    if (d === 'approved' || d === 'approve' || d === 'auto_approve') return 'approved'
                    if (d === 'denied' || d === 'deny' || d === 'reject') return 'denied'
                    if (d === 'review' || d === 'needs_review' || d === 'manual_review') return 'review'
                    return d
                  }
                  const rulesDecision = comp.rules?.decision ? normalizeDecision(comp.rules.decision) : null
                  const agentDecision = comp.agent?.decision ? normalizeDecision(comp.agent.decision) : null
                  const decisionsMatch = !comp.rules || !comp.agent || rulesDecision === agentDecision

                  return (
                    <tr key={idx} className={`hover:bg-gray-50 ${!decisionsMatch ? 'bg-yellow-50' : ''}`}>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="font-mono text-sm">{comp.claim_number}</span>
                        {comp.claim_category && (
                          <span className="ml-2 text-xs text-gray-500">{comp.claim_category}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right font-medium">
                        ${comp.claim_amount?.toLocaleString() || '-'}
                      </td>

                      {/* Rule-Based Status & Decision */}
                      <td className="px-4 py-3 text-center">
                        {comp.rules ? getStatusBadge(comp.rules.status) : (
                          <span className="text-xs text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {comp.rules ? (
                          <div className="flex items-center justify-center gap-1">
                            {getDecisionIcon(comp.rules.decision)}
                            <span className="text-sm">{comp.rules.decision || 'Pending'}</span>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">Not in pipeline</span>
                        )}
                      </td>

                      {/* Agent Status & Decision */}
                      <td className="px-4 py-3 text-center">
                        {comp.agent ? getStatusBadge(comp.agent.status) : (
                          <span className="text-xs text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {comp.agent ? (
                          <div className="flex flex-col items-center">
                            <div className="flex items-center gap-1">
                              {getDecisionIcon(comp.agent.decision || comp.agent.status)}
                              <span className="text-sm">{comp.agent.decision || comp.agent.current_stage || 'Processing'}</span>
                            </div>
                            {comp.agent.confidence && (
                              <span className="text-xs text-gray-500">{Math.round(comp.agent.confidence * 100)}% conf</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">Not in pipeline</span>
                        )}
                      </td>

                      {/* Match indicator */}
                      <td className="px-4 py-3 text-center">
                        {comp.rules && comp.agent ? (
                          decisionsMatch ? (
                            <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
                          ) : (
                            <AlertTriangle className="h-5 w-5 text-yellow-500 mx-auto" title="Decisions differ" />
                          )
                        ) : (
                          <span className="text-xs text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white rounded-xl shadow p-4">
        <h4 className="font-semibold mb-3">Understanding the Comparison</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="font-medium text-blue-600 mb-1">Rule-Based Pipeline</p>
            <ul className="text-gray-600 space-y-1">
              <li>- Uses predefined business rules</li>
              <li>- Bronze: Raw data ingestion</li>
              <li>- Silver: Validation & quality scoring</li>
              <li>- Gold: Business metrics & aggregation</li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-purple-600 mb-1">AI Agent Pipeline</p>
            <ul className="text-gray-600 space-y-1">
              <li>- Uses Claude AI for decision making</li>
              <li>- Detects fraud patterns rules may miss</li>
              <li>- Provides reasoning for decisions</li>
              <li>- Confidence scores for transparency</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
