import { useState, useEffect, useCallback } from 'react'
import { Bot, FileText, CheckCircle, XCircle, Clock, Loader2, RefreshCw, Play, AlertTriangle, Zap, Activity, Brain, Database } from 'lucide-react'
import api from '../services/api'

// localStorage keys for progress persistence
const STORAGE_KEYS = {
  ACTIVE_RUN_ID: 'petinsure360_activeAgentRunId',
  ACTIVE_RUN_DATA: 'petinsure360_activeAgentRunData'
}

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

// AI-Driven Layer Card Component - Renders from card_display
const LayerCard = ({ layer, icon: Icon, state, output, fallbackTitle, fallbackSubtitle, accentColor }) => {
  const isCompleted = state?.status === 'completed'
  const isFailed = state?.status === 'failed'
  const isRunning = state?.status === 'running'
  const cardDisplay = output?.card_display

  // Color mappings for each layer
  const colorMap = {
    amber: {
      border: 'border-amber-400',
      bg: 'bg-amber-50',
      iconBg: 'bg-amber-500',
      title: 'text-amber-900',
      subtitle: 'text-amber-700',
      accent: 'text-amber-700',
      progressBg: 'bg-amber-200',
      progressFill: 'bg-amber-500',
    },
    slate: {
      border: 'border-gray-400',
      bg: 'bg-slate-50',
      iconBg: 'bg-slate-500',
      title: 'text-slate-900',
      subtitle: 'text-slate-600',
      accent: 'text-slate-700',
      progressBg: 'bg-slate-200',
      progressFill: 'bg-slate-500',
    },
    green: {
      border: 'border-green-400',
      bg: 'bg-green-50',
      iconBg: 'bg-green-500',
      title: 'text-green-900',
      subtitle: 'text-green-700',
      accent: 'text-green-700',
      progressBg: 'bg-green-200',
      progressFill: 'bg-green-500',
    },
  }

  const colors = colorMap[accentColor] || colorMap.slate

  // Get status color from card_display or fallback
  const getStatusColor = (statusColor) => {
    const statusColorMap = {
      green: 'bg-green-100 text-green-700',
      red: 'bg-red-100 text-red-700',
      yellow: 'bg-yellow-100 text-yellow-700',
      orange: 'bg-orange-100 text-orange-700',
      blue: 'bg-blue-100 text-blue-700',
    }
    return statusColorMap[statusColor] || 'bg-gray-100 text-gray-700'
  }

  // Title and subtitle from AI or fallback
  const title = cardDisplay?.title || fallbackTitle
  const subtitle = cardDisplay?.subtitle || fallbackSubtitle

  return (
    <div className={`p-4 rounded-xl border-2 ${isCompleted ? `${colors.border} ${colors.bg}` : 'border-gray-200 bg-gray-50'}`}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-8 h-8 rounded-full ${colors.iconBg} flex items-center justify-center`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
        <div>
          <h4 className={`font-semibold ${colors.title}`}>{title}</h4>
          <p className={`text-xs ${colors.subtitle}`}>{subtitle}</p>
        </div>
      </div>

      {/* Content - AI Generated or Fallback */}
      {isCompleted && cardDisplay ? (
        <div className="space-y-2">
          {/* Primary Metric */}
          {cardDisplay.primary_metric && (
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600">{cardDisplay.primary_metric.label}</span>
              <span className={`text-sm font-bold ${colors.accent}`}>{cardDisplay.primary_metric.value}</span>
            </div>
          )}

          {/* Amount Display (for Silver/Gold) */}
          {cardDisplay.amount !== undefined && cardDisplay.amount !== null && (
            <div className="bg-green-100 rounded-lg p-2 text-center">
              <p className="text-xs text-green-600">{cardDisplay.amount_label || 'Amount'}</p>
              <p className="text-lg font-bold text-green-700">${Number(cardDisplay.amount).toLocaleString()}</p>
            </div>
          )}

          {/* Status/Decision Badge */}
          {(cardDisplay.status || cardDisplay.decision) && (
            <div className={`text-center py-2 rounded-lg ${getStatusColor(cardDisplay.status_color || cardDisplay.decision_color)}`}>
              <p className="text-sm font-bold">{cardDisplay.decision || cardDisplay.status}</p>
            </div>
          )}

          {/* Secondary Metrics */}
          {cardDisplay.secondary_metrics?.length > 0 && (
            <div className={`grid grid-cols-${Math.min(cardDisplay.secondary_metrics.length, 2)} gap-2 text-xs`}>
              {cardDisplay.secondary_metrics.slice(0, 2).map((metric, idx) => (
                <div key={idx} className="bg-white rounded p-1.5 text-center">
                  <p className="text-gray-500">{metric.label}</p>
                  <p className="font-bold">{metric.value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Summary */}
          {cardDisplay.summary && (
            <p className="text-xs text-gray-600 italic line-clamp-2">{cardDisplay.summary}</p>
          )}
        </div>
      ) : isCompleted ? (
        // Fallback for completed without card_display (legacy data)
        <div className="space-y-2">
          {layer === 'bronze' && output.quality_score !== undefined && (
            <>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-600">Data Quality</span>
                <span className={`text-sm font-bold ${colors.accent}`}>{Math.round((output.quality_score || 0) * 100)}%</span>
              </div>
              <div className={`w-full ${colors.progressBg} rounded-full h-2`}>
                <div className={`${colors.progressFill} h-2 rounded-full`} style={{width: `${Math.round((output.quality_score || 0) * 100)}%`}}></div>
              </div>
            </>
          )}
          {layer === 'silver' && (
            <>
              <div className="flex items-center gap-2">
                {output.is_covered ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-500" />
                )}
                <span className="text-sm font-medium">{output.is_covered ? 'Coverage Verified' : 'Not Covered'}</span>
              </div>
              {output.expected_reimbursement && (
                <div className="bg-green-100 rounded-lg p-2 text-center">
                  <p className="text-xs text-green-600">Expected Reimbursement</p>
                  <p className="text-lg font-bold text-green-700">${output.expected_reimbursement?.toLocaleString()}</p>
                </div>
              )}
            </>
          )}
          {layer === 'gold' && output.final_decision && (
            <>
              <div className={`text-center py-2 rounded-lg ${
                output.final_decision === 'approve' || output.final_decision === 'auto_approve'
                  ? 'bg-green-100'
                  : output.final_decision === 'deny'
                    ? 'bg-red-100'
                    : 'bg-yellow-100'
              }`}>
                <p className="text-lg font-bold capitalize">
                  {output.final_decision === 'auto_approve' ? 'Approved' : output.final_decision}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-white rounded p-1.5 text-center">
                  <p className="text-gray-500">Amount</p>
                  <p className="font-bold">${(output.approved_amount || output.silver_reference?.expected_reimbursement || 0).toLocaleString()}</p>
                </div>
                <div className="bg-white rounded p-1.5 text-center">
                  <p className="text-gray-500">Confidence</p>
                  <p className="font-bold">{Math.round((output.confidence || 0) * 100)}%</p>
                </div>
              </div>
            </>
          )}
        </div>
      ) : isFailed ? (
        // Show error state
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-red-600">
            <XCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Processing Failed</span>
          </div>
          {state?.error && (
            <p className="text-xs text-red-500 bg-red-50 p-2 rounded">{state.error.substring(0, 150)}{state.error.length > 150 ? '...' : ''}</p>
          )}
        </div>
      ) : isRunning ? (
        // Show running state
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          <span className="text-sm text-blue-600">Processing...</span>
        </div>
      ) : (
        <p className="text-xs text-gray-500 italic">Awaiting processing</p>
      )}
    </div>
  )
}

// Pipeline Run Card component for LangGraph Agent Pipeline
const PipelineRunCard = ({ run, onProcessBronze, onProcessSilver, onProcessGold, isProcessing, isFirst = false }) => {
  const [expanded, setExpanded] = useState(isFirst) // First card expands by default

  // Determine which process button to show
  const getNextAction = () => {
    const status = run.status?.toLowerCase()
    const currentStage = run.current_stage?.toLowerCase()

    // If running, no action available
    if (status === 'running') return null
    // If completed or failed, no action available
    if (status === 'completed' || status === 'failed') return null

    // Check stage completion
    const bronzeComplete = run.bronze_state?.status === 'completed' || run.bronze_output
    const silverComplete = run.silver_state?.status === 'completed' || run.silver_output
    const goldComplete = run.gold_state?.status === 'completed' || run.gold_output

    if (!bronzeComplete) return 'bronze'
    if (!silverComplete) return 'silver'
    if (!goldComplete) return 'gold'
    return null
  }

  const nextAction = getNextAction()

  const getStatusBadge = () => {
    const status = run.status?.toLowerCase()
    if (status === 'completed') {
      return (
        <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
          <CheckCircle className="w-3 h-3" />
          Completed
        </span>
      )
    }
    if (status === 'failed' || run.has_errors) {
      return (
        <span className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
          <XCircle className="w-3 h-3" />
          Failed
        </span>
      )
    }
    if (status === 'running') {
      return (
        <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
          <Loader2 className="w-3 h-3 animate-spin" />
          {run.current_stage ? `Processing ${run.current_stage}` : 'Running'}
        </span>
      )
    }
    // Pending - show what's waiting
    if (nextAction) {
      return (
        <span className="flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded-full">
          <Clock className="w-3 h-3" />
          Waiting for {nextAction}
        </span>
      )
    }
    return (
      <span className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
        <Clock className="w-3 h-3" />
        {status || 'Pending'}
      </span>
    )
  }

  const getStageBadge = (stageName, stageData) => {
    if (!stageData) return <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded">Pending</span>
    const status = stageData.status?.toLowerCase()
    if (status === 'completed') {
      return <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">✓ {stageName}</span>
    }
    if (status === 'running') {
      return <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded animate-pulse">⟳ {stageName}</span>
    }
    if (status === 'failed' || stageData.error) {
      return <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">✗ {stageName}</span>
    }
    return <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded">{stageName}</span>
  }

  const claimData = run.claim_data || {}
  const bronzeOutput = run.bronze_output || {}
  const silverOutput = run.silver_output || {}
  const goldOutput = run.gold_output || {}

  return (
    <div className={`bg-white rounded-lg border p-4 transition-shadow ${run.has_errors ? 'border-red-200' : 'border-purple-200'}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Bot className="w-4 h-4 text-purple-600" />
            <span className="font-medium text-gray-900">
              {claimData.claim_number || run.claim_id}
            </span>
            {getStatusBadge()}
          </div>
          <p className="text-sm text-gray-500">
            {claimData.claim_type && <span>{claimData.claim_type} • </span>}
            {claimData.claim_amount && <span>${claimData.claim_amount.toLocaleString()} • </span>}
            {run.started_at && <span>{new Date(run.started_at).toLocaleString()}</span>}
          </p>
          {/* Stage Progress */}
          <div className="flex items-center gap-2 mt-2">
            {getStageBadge('Router', run.router_state)}
            <span className="text-gray-300">→</span>
            {getStageBadge('Bronze', run.bronze_state)}
            <span className="text-gray-300">→</span>
            {getStageBadge('Silver', run.silver_state)}
            <span className="text-gray-300">→</span>
            {getStageBadge('Gold', run.gold_state)}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Process Button - shows next action */}
          {nextAction && (
            <button
              onClick={() => {
                if (nextAction === 'bronze') onProcessBronze?.(run.run_id)
                else if (nextAction === 'silver') onProcessSilver?.(run.run_id)
                else if (nextAction === 'gold') onProcessGold?.(run.run_id)
              }}
              disabled={isProcessing}
              className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg text-white transition-colors ${
                nextAction === 'bronze' ? 'bg-amber-600 hover:bg-amber-700' :
                nextAction === 'silver' ? 'bg-gray-600 hover:bg-gray-700' :
                'bg-green-600 hover:bg-green-700'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Process {nextAction.charAt(0).toUpperCase() + nextAction.slice(1)}
                </>
              )}
            </button>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className={`px-3 py-1.5 border text-sm rounded-lg transition-colors ${
              expanded ? 'bg-purple-100 border-purple-400' : 'border-gray-300 hover:bg-gray-50'
            }`}
          >
            {expanded ? '▲ Collapse' : '▼ Expand'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t">
          {/* Executive Summary Header - AI-Driven Cards */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            {/* Bronze Layer Card - AI Generated */}
            <LayerCard
              layer="bronze"
              icon={Database}
              state={run.bronze_state}
              output={bronzeOutput}
              fallbackTitle="Bronze Layer"
              fallbackSubtitle="AI Data Validation Agent"
              accentColor="amber"
            />

            {/* Silver Layer Card - AI Generated */}
            <LayerCard
              layer="silver"
              icon={Activity}
              state={run.silver_state}
              output={silverOutput}
              fallbackTitle="Silver Layer"
              fallbackSubtitle="AI Enrichment Agent"
              accentColor="slate"
            />

            {/* Gold Layer Card - AI Generated */}
            <LayerCard
              layer="gold"
              icon={Brain}
              state={run.gold_state}
              output={goldOutput}
              fallbackTitle="Gold Layer"
              fallbackSubtitle="AI Decision Agent"
              accentColor="green"
            />
          </div>

          {/* Detailed Analysis (Expanded by default) */}
          {(bronzeOutput.reasoning || silverOutput.enrichment_notes || goldOutput.reasoning) && (
            <details open className="bg-gray-50 rounded-lg p-3">
              <summary className="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900">
                View Detailed Analysis
              </summary>
              <div className="mt-3 space-y-3 text-xs text-gray-600">
                {/* Bronze Analysis */}
                {bronzeOutput.reasoning && (
                  <details open className="p-2 bg-amber-50 rounded border-l-2 border-amber-400">
                    <summary className="font-medium text-amber-800 cursor-pointer hover:text-amber-900">
                      Bronze Analysis
                    </summary>
                    <div className="mt-2 space-y-2">
                      <p className="whitespace-pre-wrap text-amber-900">{bronzeOutput.reasoning}</p>
                      {/* Bronze Output Data */}
                      {bronzeOutput.cleaned_data && (
                        <details className="mt-2 p-2 bg-amber-100/50 rounded">
                          <summary className="text-xs font-medium text-amber-700 cursor-pointer">
                            View Output Data
                          </summary>
                          <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                            <div><span className="text-amber-600">Claim ID:</span> {bronzeOutput.cleaned_data.claim_id}</div>
                            <div><span className="text-amber-600">Amount:</span> ${bronzeOutput.cleaned_data.claim_amount?.toLocaleString()}</div>
                            <div><span className="text-amber-600">Customer:</span> {bronzeOutput.cleaned_data.customer_name}</div>
                            <div><span className="text-amber-600">Pet:</span> {bronzeOutput.cleaned_data.pet_name}</div>
                            <div><span className="text-amber-600">Type:</span> {bronzeOutput.cleaned_data.claim_type}</div>
                            <div><span className="text-amber-600">Category:</span> {bronzeOutput.cleaned_data.claim_category}</div>
                            <div className="col-span-2"><span className="text-amber-600">Diagnosis:</span> {bronzeOutput.cleaned_data.diagnosis}</div>
                            <div><span className="text-amber-600">Quality Score:</span> {(bronzeOutput.quality_score * 100).toFixed(0)}%</div>
                            <div><span className="text-amber-600">Decision:</span> {bronzeOutput.decision}</div>
                          </div>
                        </details>
                      )}
                    </div>
                  </details>
                )}
                {/* Silver Enrichment */}
                {silverOutput.enrichment_notes && (
                  <details open className="p-2 bg-slate-50 rounded border-l-2 border-slate-400">
                    <summary className="font-medium text-slate-800 cursor-pointer hover:text-slate-900">
                      Silver Enrichment
                    </summary>
                    <div className="mt-2 space-y-2">
                      <p className="whitespace-pre-wrap text-slate-900">{silverOutput.enrichment_notes}</p>
                      {/* Silver Output Data */}
                      <details className="mt-2 p-2 bg-slate-100/50 rounded">
                        <summary className="text-xs font-medium text-slate-700 cursor-pointer">
                          View Output Data
                        </summary>
                        <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                          <div><span className="text-slate-600">Coverage:</span> {silverOutput.is_covered ? 'Yes' : 'No'}</div>
                          <div><span className="text-slate-600">Coverage %:</span> {silverOutput.coverage_percentage}%</div>
                          <div><span className="text-slate-600">Expected Reimbursement:</span> ${silverOutput.expected_reimbursement?.toLocaleString()}</div>
                          <div><span className="text-slate-600">Quality Score:</span> {(silverOutput.quality_score * 100).toFixed(0)}%</div>
                        </div>
                      </details>
                    </div>
                  </details>
                )}
                {/* Gold Decision */}
                {goldOutput.reasoning && (
                  <details open className="p-2 bg-green-50 rounded border-l-2 border-green-400">
                    <summary className="font-medium text-green-800 cursor-pointer hover:text-green-900">
                      Gold Decision Rationale
                    </summary>
                    <div className="mt-2 space-y-2">
                      <p className="whitespace-pre-wrap text-green-900">{goldOutput.reasoning}</p>
                      {/* Gold Output Data */}
                      <details className="mt-2 p-2 bg-green-100/50 rounded">
                        <summary className="text-xs font-medium text-green-700 cursor-pointer">
                          View Output Data
                        </summary>
                        <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                          <div><span className="text-green-600">Final Decision:</span> <span className="font-semibold">{goldOutput.final_decision?.replace('_', ' ').toUpperCase()}</span></div>
                          <div><span className="text-green-600">Approved Amount:</span> ${goldOutput.approved_amount?.toLocaleString()}</div>
                          <div><span className="text-green-600">Fraud Score:</span> {(goldOutput.fraud_score * 100).toFixed(1)}%</div>
                          <div><span className="text-green-600">Risk Level:</span> {goldOutput.risk_level?.toUpperCase()}</div>
                          <div><span className="text-green-600">Confidence:</span> {(goldOutput.confidence * 100).toFixed(0)}%</div>
                          <div><span className="text-green-600">Processing Time:</span> {(goldOutput.total_pipeline_time_ms / 1000).toFixed(1)}s</div>
                        </div>
                      </details>
                    </div>
                  </details>
                )}
              </div>
            </details>
          )}

          {/* Errors */}
          {run.errors?.length > 0 && (
            <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <XCircle className="w-4 h-4 text-red-600" />
                <span className="text-sm font-medium text-red-900">Processing Errors</span>
              </div>
              {run.errors.map((err, idx) => (
                <p key={idx} className="text-xs text-red-700">• {err}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function AgentPipelinePage() {
  const [pipelineRuns, setPipelineRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState({})
  const [serviceStatus, setServiceStatus] = useState(null)
  const [pipelineStatus, setPipelineStatus] = useState(null)
  const [expandedRunId, setExpandedRunId] = useState(null) // Track which run is expanded

  // DocGen service URL (EIS Dynamics DocGen Service)
  const DOCGEN_URL = import.meta.env.VITE_DOCGEN_URL || 'http://localhost:8007'
  // Agent Pipeline URL (EIS Dynamics LangGraph Pipeline)
  const PIPELINE_URL = (import.meta.env.VITE_PIPELINE_URL || 'http://localhost:8006/api').replace(/\/api$/, '')

  // Restore active run from localStorage on mount
  useEffect(() => {
    const savedRunId = localStorage.getItem(STORAGE_KEYS.ACTIVE_RUN_ID)
    const savedRunData = localStorage.getItem(STORAGE_KEYS.ACTIVE_RUN_DATA)
    
    if (savedRunId) {
      console.log('Restoring active run from localStorage:', savedRunId)
      // Restore processing state
      setProcessing(prev => ({ ...prev, [savedRunId]: true }))
      setExpandedRunId(savedRunId)
      
      // If we have saved run data, use it immediately for UI
      if (savedRunData) {
        try {
          const runData = JSON.parse(savedRunData)
          setPipelineRuns(prev => {
            const exists = prev.some(r => r.run_id === savedRunId)
            if (!exists) return [runData, ...prev]
            return prev
          })
        } catch (e) {
          console.error('Error parsing saved run data:', e)
        }
      }
      
      // Resume polling for this run
      pollPipelineRunWithStorage(savedRunId)
    }
  }, [])

  useEffect(() => {
    checkServiceHealth()
    loadPipelineRuns()

    // Poll for updates
    const interval = setInterval(() => {
      loadPipelineRuns()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const checkServiceHealth = async () => {
    // Check DocGen service
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
    // Check Agent Pipeline service
    try {
      const response = await fetch(`${PIPELINE_URL}/health`)
      if (response.ok) {
        setPipelineStatus('connected')
      } else {
        setPipelineStatus('unavailable')
      }
    } catch {
      setPipelineStatus('unavailable')
    }
  }

  const loadPipelineRuns = async () => {
    setLoading(false) // Set loading false once we start loading runs
    try {
      const response = await fetch(`${PIPELINE_URL}/api/v1/pipeline/recent?limit=50`)
      if (response.ok) {
        const data = await response.json()
        setPipelineRuns(data.runs || [])
      }
    } catch (err) {
      console.error('Error loading pipeline runs:', err)
    }
  }

  // =========================================================================
  // MANUAL PIPELINE PROCESSING HANDLERS
  // =========================================================================

  const handleProcessBronze = async (runId) => {
    setProcessing(prev => ({ ...prev, [runId]: true }))
    try {
      const response = await fetch(`${PIPELINE_URL}/api/v1/pipeline/run/${runId}/process/bronze`, {
        method: 'POST'
      })
      if (!response.ok) {
        const error = await response.json()
        console.error('Bronze processing error:', error)
      }
      // Poll for completion
      pollPipelineRun(runId)
    } catch (err) {
      console.error('Error processing Bronze:', err)
      setProcessing(prev => ({ ...prev, [runId]: false }))
    }
  }

  const handleProcessSilver = async (runId) => {
    setProcessing(prev => ({ ...prev, [runId]: true }))
    try {
      const response = await fetch(`${PIPELINE_URL}/api/v1/pipeline/run/${runId}/process/silver`, {
        method: 'POST'
      })
      if (!response.ok) {
        const error = await response.json()
        console.error('Silver processing error:', error)
      }
      // Poll for completion
      pollPipelineRun(runId)
    } catch (err) {
      console.error('Error processing Silver:', err)
      setProcessing(prev => ({ ...prev, [runId]: false }))
    }
  }

  const handleProcessGold = async (runId) => {
    setProcessing(prev => ({ ...prev, [runId]: true }))
    try {
      const response = await fetch(`${PIPELINE_URL}/api/v1/pipeline/run/${runId}/process/gold`, {
        method: 'POST'
      })
      if (!response.ok) {
        const error = await response.json()
        console.error('Gold processing error:', error)
      }
      // Poll for completion
      pollPipelineRun(runId)
    } catch (err) {
      console.error('Error processing Gold:', err)
      setProcessing(prev => ({ ...prev, [runId]: false }))
    }
  }

  // Poll pipeline run WITH localStorage persistence
  const pollPipelineRunWithStorage = async (runId) => {
    // Save to localStorage when polling starts
    localStorage.setItem(STORAGE_KEYS.ACTIVE_RUN_ID, runId)
    
    let attempts = 0
    const maxAttempts = 180 // 3 minutes max

    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      try {
        const response = await fetch(`${PIPELINE_URL}/api/v1/pipeline/recent?limit=50`)
        if (response.ok) {
          const data = await response.json()
          setPipelineRuns(data.runs || [])

          const run = (data.runs || []).find(r => r.run_id === runId)
          if (run) {
            // Save current run data to localStorage for restoration
            localStorage.setItem(STORAGE_KEYS.ACTIVE_RUN_DATA, JSON.stringify(run))
            
            // Check if run is complete
            if (run.status !== 'running' && run.status !== 'in_progress') {
              // Clear localStorage on completion
              localStorage.removeItem(STORAGE_KEYS.ACTIVE_RUN_ID)
              localStorage.removeItem(STORAGE_KEYS.ACTIVE_RUN_DATA)
              setProcessing(prev => ({ ...prev, [runId]: false }))
              return
            }
          }
        }
      } catch (e) {
        console.error('Poll error:', e)
      }
      attempts++
    }
    // Timeout - clear localStorage
    localStorage.removeItem(STORAGE_KEYS.ACTIVE_RUN_ID)
    localStorage.removeItem(STORAGE_KEYS.ACTIVE_RUN_DATA)
    setProcessing(prev => ({ ...prev, [runId]: false }))
  }

  // Legacy poll function (without localStorage) - kept for compatibility
  const pollPipelineRun = async (runId) => {
    return pollPipelineRunWithStorage(runId)
  }

  // Stats - Pipeline runs (LangGraph)
  const pendingCount = pipelineRuns.filter(r => r.status === 'pending').length
  const processingCount = pipelineRuns.filter(r => r.status === 'running' || r.status === 'started').length
  const completedCount = pipelineRuns.filter(r => r.status === 'completed').length
  const failedCount = pipelineRuns.filter(r => r.status === 'failed' || r.has_errors).length

  // Check if any run is being processed
  const isAnyProcessing = Object.values(processing).some(v => v) || processingCount > 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Pipeline (AI-Driven)</h1>
          <p className="text-gray-500">Claims processed by AI agents through LangGraph medallion architecture</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Service Status Indicators */}
          <div className="flex items-center gap-2 text-xs">
            <span className={`px-2 py-1 rounded ${pipelineStatus === 'connected' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              Pipeline: {pipelineStatus || 'checking...'}
            </span>
            <span className={`px-2 py-1 rounded ${serviceStatus === 'connected' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
              Doc Processing: {serviceStatus || 'checking...'}
            </span>
          </div>
          <button
            onClick={() => { loadPipelineRuns(); checkServiceHealth(); }}
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
            {processingCount > 0 ? `${processingCount} claim(s) being processed by AI agents` : 'Starting AI processing...'}
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

      {/* LangGraph Pipeline Runs - PRIMARY SECTION */}
      <div className="bg-white rounded-xl border-2 border-purple-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Bot className="h-6 w-6 text-purple-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">LangGraph Pipeline Runs</h3>
              <p className="text-xs text-gray-500">Claims processed through Bronze → Silver → Gold medallion layers</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded">{pipelinePending} pending</span>
            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">{pipelineRunning} running</span>
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">{pipelineCompleted} completed</span>
            <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">{pipelineFailed} failed</span>
            <span className="text-sm text-gray-500">{pipelineRuns.length} total</span>
          </div>
        </div>

        {pipelineRuns.length === 0 ? (
          <div className="text-center py-12 bg-purple-50 rounded-lg">
            <Bot className="h-12 w-12 mx-auto text-purple-300 mb-4" />
            <p className="text-purple-600 font-medium">No pipeline runs yet</p>
            <p className="text-purple-400 text-sm">Claims submitted from Customer Portal will be processed here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {pipelineRuns.map((run, index) => (
              <PipelineRunCard
                key={run.run_id}
                run={run}
                onProcessBronze={handleProcessBronze}
                onProcessSilver={handleProcessSilver}
                onProcessGold={handleProcessGold}
                isProcessing={processing[run.run_id]}
                isFirst={index === 0}
              />
            ))}
          </div>
        )}
      </div>

      {/* Document Processing is available at /doc-processing page */}
    </div>
  )
}
