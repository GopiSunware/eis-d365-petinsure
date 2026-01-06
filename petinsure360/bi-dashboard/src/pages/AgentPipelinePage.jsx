import { useState, useEffect } from 'react'
import { Bot, FileText, CheckCircle, XCircle, Clock, Loader2, RefreshCw, Play, AlertTriangle, Zap, Activity, Brain } from 'lucide-react'
import api from '../services/api'

// Agent step component
const AgentStep = ({ step }) => {
  const getStatusIcon = () => {
    if (step.status === 'running') return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
    if (step.status === 'completed') {
      if (step.result === 'pass') return <CheckCircle className="h-5 w-5 text-green-500" />
      if (step.result === 'fail') return <XCircle className="h-5 w-5 text-red-500" />
      if (step.result === 'warning') return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      if (step.result === 'skip') return <div className="h-5 w-5 rounded-full border-2 border-gray-300 flex items-center justify-center"><span className="text-xs text-gray-400">—</span></div>
    }
    return <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
  }

  const getStatusBg = () => {
    if (step.status === 'running') return 'bg-blue-50 border-blue-200'
    if (step.status === 'completed') {
      if (step.result === 'pass') return 'bg-green-50'
      if (step.result === 'fail') return 'bg-red-50'
      if (step.result === 'warning') return 'bg-yellow-50'
      if (step.result === 'skip') return 'bg-gray-50'
    }
    return 'bg-gray-50 opacity-50'
  }

  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg ${getStatusBg()}`}>
      {getStatusIcon()}
      <div className="flex-1">
        <span className="text-sm font-medium">{step.message}</span>
        {step.details && (
          <p className="text-xs text-gray-500 mt-0.5">{step.details}</p>
        )}
      </div>
      <span className="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-600">
        {step.step_type?.replace(/_/g, ' ')}
      </span>
    </div>
  )
}

// Batch card component with expandable inline details
const BatchCard = ({ batch, onProcess, onView, isProcessing }) => {
  const [expanded, setExpanded] = useState(false)

  const getStatusBadge = () => {
    switch (batch.status) {
      case 'completed':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
            <CheckCircle className="w-3 h-3" />
            Completed
          </span>
        )
      case 'failed':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
            <XCircle className="w-3 h-3" />
            Failed
          </span>
        )
      case 'processing':
      case 'extracting':
      case 'validating':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
            <Loader2 className="w-3 h-3 animate-spin" />
            Processing
          </span>
        )
      default:
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
            <Clock className="w-3 h-3" />
            Pending
          </span>
        )
    }
  }

  const getDecisionBadge = () => {
    if (!batch.ai_decision) return null
    const colors = {
      auto_approve: 'bg-green-100 text-green-700',
      proceed: 'bg-green-100 text-green-700',
      needs_review: 'bg-yellow-100 text-yellow-700',
      deny: 'bg-red-100 text-red-700',
      duplicate_rejected: 'bg-red-100 text-red-700',
    }
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[batch.ai_decision] || 'bg-gray-100 text-gray-700'}`}>
        {batch.ai_decision.replace(/_/g, ' ')}
      </span>
    )
  }

  return (
    <div className={`bg-white rounded-lg border p-4 transition-shadow ${batch.status === 'failed' ? 'border-red-200' : ''}`}>
      {/* Header Row - Always Visible */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-gray-900">
              {batch.claim_number || `Batch ${batch.batch_id?.slice(0, 8)}`}
            </span>
            {getStatusBadge()}
            {getDecisionBadge()}
          </div>
          <p className="text-sm text-gray-500">
            {batch.documents_count || 0} document(s) • {new Date(batch.created_at).toLocaleString()}
            {batch.claim_amount && <span> • ${batch.claim_amount.toLocaleString()}</span>}
            {batch.claim_type && <span> • {batch.claim_type}</span>}
          </p>
          {/* Error shown prominently when failed */}
          {batch.error && (
            <div className="mt-2 flex items-start gap-2 p-2 bg-red-50 rounded-lg border border-red-200">
              <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-red-700">Error: {batch.error_stage || 'processing'}</p>
                <p className="text-sm text-red-600">{batch.error}</p>
              </div>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          {batch.status === 'pending' && (
            <button
              onClick={() => onProcess(batch.batch_id)}
              disabled={isProcessing}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Process
                </>
              )}
            </button>
          )}
          {batch.status === 'failed' && (
            <button
              onClick={() => onProcess(batch.batch_id)}
              disabled={isProcessing}
              className="flex items-center gap-1 px-3 py-1.5 bg-orange-600 text-white text-sm rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Retrying...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Retry
                </>
              )}
            </button>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className={`px-3 py-1.5 border text-sm rounded-lg transition-colors ${
              expanded ? 'bg-gray-100 border-gray-400' : 'border-gray-300 hover:bg-gray-50'
            }`}
          >
            {expanded ? '▲ Collapse' : '▼ Expand'}
          </button>
        </div>
      </div>

      {/* Expandable Section - Inline Details */}
      {expanded && (
        <div className="mt-4 pt-4 border-t space-y-4">
          {/* Agent Steps */}
          {batch.agent_steps?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Processing Steps</h4>
              <div className="space-y-2">
                {batch.agent_steps.map((step, idx) => (
                  <AgentStep key={step.step_id || idx} step={step} />
                ))}
              </div>
            </div>
          )}

          {/* AI Reasoning */}
          {batch.ai_reasoning && (
            <div className="p-3 bg-purple-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-900">AI Reasoning</span>
              </div>
              <div className="text-sm text-purple-800 space-y-1">
                {batch.ai_reasoning.split(/\n/).map((line, idx) => (
                  <p key={idx}>{line}</p>
                ))}
              </div>
            </div>
          )}

          {/* View Full Details Button */}
          <div className="flex justify-end">
            <button
              onClick={() => onView(batch)}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              View Full Details →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AgentPipelinePage() {
  const [batches, setBatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState({})
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [serviceStatus, setServiceStatus] = useState(null)

  // DocGen service URL (EIS Dynamics DocGen Service)
  const DOCGEN_URL = import.meta.env.VITE_DOCGEN_URL || 'http://localhost:8007'

  useEffect(() => {
    checkServiceHealth()
    loadBatches()

    // Poll for updates
    const interval = setInterval(loadBatches, 5000)
    return () => clearInterval(interval)
  }, [])

  const checkServiceHealth = async () => {
    try {
      const response = await fetch(`${DOCGEN_URL}/health`)
      if (response.ok) {
        setServiceStatus('connected')
      } else {
        setServiceStatus('unavailable')
      }
    } catch {
      setServiceStatus('unavailable')
    }
  }

  const loadBatches = async () => {
    try {
      const response = await fetch(`${DOCGEN_URL}/api/v1/docgen/batches?limit=50`)
      if (response.ok) {
        const data = await response.json()
        setBatches(data.batches || [])
      }
    } catch (err) {
      console.error('Error loading batches:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleProcess = async (batchId) => {
    // Immediately show processing state - don't clear until batch status changes
    setProcessing(prev => ({ ...prev, [batchId]: true }))

    try {
      await fetch(`${DOCGEN_URL}/api/v1/docgen/process/${batchId}`, { method: 'POST' })

      // Poll frequently until batch status changes from pending
      const pollForCompletion = async () => {
        let attempts = 0
        const maxAttempts = 120 // 2 minutes max

        while (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 1000)) // Poll every second
          try {
            const response = await fetch(`${DOCGEN_URL}/api/v1/docgen/batches?limit=50`)
            if (response.ok) {
              const data = await response.json()
              setBatches(data.batches || [])

              // Check if this batch is no longer pending
              const batch = (data.batches || []).find(b => b.batch_id === batchId)
              if (batch && batch.status !== 'pending' && !['extracting', 'validating', 'processing'].includes(batch.status)) {
                // Processing finished (completed or failed)
                setProcessing(prev => ({ ...prev, [batchId]: false }))
                return
              }
            }
          } catch (e) {
            console.error('Poll error:', e)
          }
          attempts++
        }
        // Timeout - clear processing state
        setProcessing(prev => ({ ...prev, [batchId]: false }))
      }

      pollForCompletion()
    } catch (err) {
      console.error('Error processing batch:', err)
      setProcessing(prev => ({ ...prev, [batchId]: false }))
    }
  }

  const handleViewBatch = async (batch) => {
    try {
      const response = await fetch(`${DOCGEN_URL}/api/v1/docgen/batch/${batch.batch_id}`)
      if (response.ok) {
        const fullBatch = await response.json()
        setSelectedBatch(fullBatch)
      }
    } catch (err) {
      console.error('Error loading batch details:', err)
    }
  }

  // Stats
  const pendingCount = batches.filter(b => b.status === 'pending').length
  const processingCount = batches.filter(b => ['processing', 'extracting', 'validating'].includes(b.status)).length
  const completedCount = batches.filter(b => b.status === 'completed').length
  const failedCount = batches.filter(b => b.status === 'failed').length

  // Check if any batch is being processed (local button click)
  const isAnyProcessing = Object.values(processing).some(v => v)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Pipeline (AI-Driven)</h1>
          <p className="text-gray-500">Claims processed by AI agents - parallel to Legacy Pipeline</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => { loadBatches(); checkServiceHealth(); }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Processing Progress Bar */}
      {(isAnyProcessing || processingCount > 0) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-2">
            <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
            <span className="text-sm font-medium text-blue-800">
              AI Agent Processing in Progress...
            </span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full animate-pulse"
              style={{ width: '100%', animation: 'pulse 2s ease-in-out infinite, progress 3s ease-in-out infinite' }}
            />
          </div>
          <p className="text-xs text-blue-600 mt-2">
            {processingCount > 0 ? `${processingCount} batch(es) being processed by AI agents` : 'Starting AI processing...'}
          </p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center">
              <Clock className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Pending</p>
              <p className="text-2xl font-bold text-gray-900">{pendingCount}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Processing</p>
              <p className="text-2xl font-bold text-blue-600">{processingCount}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Completed</p>
              <p className="text-2xl font-bold text-green-600">{completedCount}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
              <XCircle className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Failed</p>
              <p className="text-2xl font-bold text-red-600">{failedCount}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Flow Diagram */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="h-5 w-5 text-purple-600" />
          <h3 className="text-lg font-semibold text-purple-900">AI Agent Processing Flow</h3>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm">
            <FileText className="h-8 w-8 text-gray-600 mb-2" />
            <span className="text-sm font-medium">Document Upload</span>
          </div>
          <div className="h-0.5 w-12 bg-purple-300" />
          <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm">
            <CheckCircle className="h-8 w-8 text-blue-600 mb-2" />
            <span className="text-sm font-medium">Policy Check</span>
          </div>
          <div className="h-0.5 w-12 bg-purple-300" />
          <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm">
            <Activity className="h-8 w-8 text-purple-600 mb-2" />
            <span className="text-sm font-medium">Duplicate Check</span>
          </div>
          <div className="h-0.5 w-12 bg-purple-300" />
          <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm">
            <Zap className="h-8 w-8 text-yellow-600 mb-2" />
            <span className="text-sm font-medium">AI Extraction</span>
          </div>
          <div className="h-0.5 w-12 bg-purple-300" />
          <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm">
            <AlertTriangle className="h-8 w-8 text-orange-600 mb-2" />
            <span className="text-sm font-medium">Validation</span>
          </div>
          <div className="h-0.5 w-12 bg-purple-300" />
          <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm">
            <Brain className="h-8 w-8 text-green-600 mb-2" />
            <span className="text-sm font-medium">AI Decision</span>
          </div>
        </div>
      </div>

      {/* Batches List */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Document Batches</h3>
          <span className="text-sm text-gray-500">{batches.length} total</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        ) : batches.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No document batches yet</p>
            <p className="text-gray-400 text-sm">Documents uploaded from Customer Portal will appear here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {batches.map(batch => (
              <BatchCard
                key={batch.batch_id}
                batch={batch}
                onProcess={handleProcess}
                onView={handleViewBatch}
                isProcessing={processing[batch.batch_id]}
              />
            ))}
          </div>
        )}
      </div>

      {/* Batch Detail Modal */}
      {selectedBatch && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b sticky top-0 bg-white">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  Batch Details: {selectedBatch.claim_number || selectedBatch.batch_id?.slice(0, 8)}
                </h3>
                <button
                  onClick={() => setSelectedBatch(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6 space-y-6">
              {/* Documents */}
              <div>
                <h4 className="font-medium mb-3">Documents</h4>
                <div className="space-y-2">
                  {selectedBatch.documents?.map((doc, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      <FileText className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="font-medium">{doc.original_filename}</p>
                        <p className="text-xs text-gray-500">
                          {doc.content_type} • {(doc.file_size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Agent Steps */}
              {selectedBatch.agent_steps?.length > 0 && (
                <div>
                  <h4 className="font-medium mb-3">Processing Steps</h4>
                  <div className="space-y-2">
                    {selectedBatch.agent_steps.map((step, idx) => (
                      <AgentStep key={idx} step={step} />
                    ))}
                  </div>
                </div>
              )}

              {/* Extracted Data */}
              {selectedBatch.mapped_claim && (
                <div>
                  <h4 className="font-medium mb-3">Extracted Data</h4>
                  <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
                    {JSON.stringify(selectedBatch.mapped_claim, null, 2)}
                  </pre>
                </div>
              )}

              {/* Billing */}
              {selectedBatch.billing && (
                <div>
                  <h4 className="font-medium mb-3">Billing Calculation</h4>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Claim Amount</p>
                        <p className="font-semibold">${selectedBatch.billing.claim_amount}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Deductible</p>
                        <p className="font-semibold">${selectedBatch.billing.deductible_applied}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Final Payout</p>
                        <p className="font-semibold text-green-600">${selectedBatch.billing.final_payout}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* AI Reasoning */}
              {selectedBatch.ai_reasoning && (
                <div>
                  <h4 className="font-medium mb-3">AI Reasoning</h4>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="text-sm space-y-1">
                      {selectedBatch.ai_reasoning.split(/\n/).map((line, idx) => (
                        <p key={idx}>{line}</p>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
