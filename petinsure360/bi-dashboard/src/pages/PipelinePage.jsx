import { useState, useEffect } from 'react'
import { Database, Server, BarChart3, Cloud, ArrowRight, RefreshCw, CheckCircle, Clock, AlertCircle, Play, Zap, FileText, ListChecks, ToggleLeft, ToggleRight, Info, Cpu, Sparkles, ExternalLink, Loader2 } from 'lucide-react'
import api from '../services/api'
import { connectSocket, subscribeToEvent } from '../services/socket'

// localStorage keys for Databricks job persistence
const STORAGE_KEYS = {
  ACTIVE_DATABRICKS_JOB: 'petinsure360_activeDatabricksJob'
}

// Pipeline node component
const PipelineNode = ({ label, icon: Icon, status, count, pendingCount, description, isActive, onClick, actionLabel }) => {
  const statusColors = {
    active: 'border-green-500 bg-green-50',
    processing: 'border-yellow-500 bg-yellow-50 animate-pulse',
    error: 'border-red-500 bg-red-50',
    idle: 'border-gray-300 bg-gray-50',
    pending: 'border-amber-500 bg-amber-50'
  }

  const effectiveStatus = pendingCount > 0 ? 'pending' : status

  return (
    <div className={`flex flex-col items-center p-4 rounded-xl border-2 ${statusColors[effectiveStatus]} transition-all duration-300 ${isActive ? 'scale-105 shadow-lg' : ''}`}>
      <div className={`h-16 w-16 rounded-full flex items-center justify-center mb-3 ${
        effectiveStatus === 'active' ? 'bg-green-100' :
        effectiveStatus === 'processing' ? 'bg-yellow-100' :
        effectiveStatus === 'pending' ? 'bg-amber-100' :
        effectiveStatus === 'error' ? 'bg-red-100' :
        'bg-gray-100'
      }`}>
        <Icon className={`h-8 w-8 ${
          effectiveStatus === 'active' ? 'text-green-600' :
          effectiveStatus === 'processing' ? 'text-yellow-600' :
          effectiveStatus === 'pending' ? 'text-amber-600' :
          effectiveStatus === 'error' ? 'text-red-600' :
          'text-gray-400'
        }`} />
      </div>
      <h3 className="font-semibold text-gray-900">{label}</h3>
      {count !== undefined && (
        <p className="text-2xl font-bold text-blue-600">{count.toLocaleString()}</p>
      )}
      {pendingCount > 0 && (
        <p className="text-sm font-semibold text-amber-600">{pendingCount} pending</p>
      )}
      <p className="text-xs text-gray-500 text-center mt-1">{description}</p>
      {onClick && actionLabel && (
        <button
          onClick={onClick}
          className="mt-2 px-3 py-1 text-xs bg-blue-600 text-white rounded-full hover:bg-blue-700 flex items-center gap-1"
        >
          <Play className="h-3 w-3" />
          {actionLabel}
        </button>
      )}
    </div>
  )
}

// Animated arrow between nodes
const FlowArrow = ({ isActive, hasData }) => (
  <div className="flex items-center justify-center px-2">
    <div className={`flex items-center ${isActive ? 'animate-flow' : ''}`}>
      <div className={`h-0.5 w-8 ${hasData ? 'bg-amber-500' : isActive ? 'bg-blue-500' : 'bg-gray-300'}`}></div>
      <ArrowRight className={`h-5 w-5 ${hasData ? 'text-amber-500' : isActive ? 'text-blue-500' : 'text-gray-300'}`} />
    </div>
  </div>
)

// Pending Claims Card
const PendingClaimsCard = ({ title, claims, layer, colorClass }) => (
  <div className={`rounded-lg border-2 ${colorClass} p-4`}>
    <div className="flex items-center justify-between mb-3">
      <h4 className="font-semibold flex items-center gap-2">
        <ListChecks className="h-4 w-4" />
        {title}
      </h4>
      <span className="px-2 py-1 text-xs font-bold rounded-full bg-white/50">
        {claims.length} claims
      </span>
    </div>
    {claims.length === 0 ? (
      <p className="text-sm text-gray-500 italic">No pending claims</p>
    ) : (
      <div className="space-y-2 max-h-40 overflow-y-auto">
        {[...claims].sort((a, b) => new Date(b.ingestion_timestamp || 0) - new Date(a.ingestion_timestamp || 0)).slice(0, 5).map((claim, idx) => (
          <div key={idx} className="bg-white/70 rounded p-2 text-sm">
            <div className="flex justify-between">
              <span className="font-medium">{claim.claim_number || claim.claim_id}</span>
              <span className="font-semibold">${claim.claim_amount?.toLocaleString()}</span>
            </div>
            <div className="text-xs text-gray-600">
              {claim.claim_category} | {claim.diagnosis || 'N/A'}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {claim.ingestion_timestamp ? new Date(claim.ingestion_timestamp).toLocaleString() : ''}
            </div>
          </div>
        ))}
        {claims.length > 5 && (
          <p className="text-xs text-gray-500 text-center">+{claims.length - 5} more</p>
        )}
      </div>
    )}
  </div>
)

export default function PipelinePage() {
  const [loading, setLoading] = useState(true)
  const [pipelineStatus, setPipelineStatus] = useState(null)
  const [pipelineFlow, setPipelineFlow] = useState(null)
  const [pendingClaims, setPendingClaims] = useState({ bronze: [], silver: [], gold: [] })
  const [processingLog, setProcessingLog] = useState([])
  const [refreshing, setRefreshing] = useState(false)
  const [processing, setProcessing] = useState({ bronzeToSilver: false, silverToGold: false })
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [resetError, setResetError] = useState(null)
  const [dataMode, setDataMode] = useState('demo') // 'demo' or 'azure'
  const [togglingMode, setTogglingMode] = useState(false)
  const [lastProcessingResult, setLastProcessingResult] = useState(null) // Store last processing proof
  const [executionInfo, setExecutionInfo] = useState(null) // Store execution mode info
  const [databricksJob, setDatabricksJob] = useState(null) // Track active Databricks job

  // Restore active Databricks job from localStorage on mount
  useEffect(() => {
    const savedJobStr = localStorage.getItem(STORAGE_KEYS.ACTIVE_DATABRICKS_JOB)
    if (savedJobStr) {
      try {
        const savedJob = JSON.parse(savedJobStr)
        console.log('Restoring active Databricks job from localStorage:', savedJob)
        
        // Restore UI state
        setDatabricksJob({
          run_id: savedJob.run_id,
          job_url: savedJob.job_url,
          layer: savedJob.layer,
          status: 'running',
          started_at: savedJob.started_at
        })
        
        setLastProcessingResult({
          type: savedJob.layer === 'bronze_silver' ? 'Bronze → Silver' : 'Silver → Gold',
          success: true,
          databricks: {
            triggered: true,
            run_id: savedJob.run_id,
            job_url: savedJob.job_url,
            completed: false
          }
        })
        
        // Resume polling
        pollDatabricksJobStatusWithStorage(savedJob.run_id, savedJob.layer)
      } catch (e) {
        console.error('Error restoring Databricks job:', e)
        localStorage.removeItem(STORAGE_KEYS.ACTIVE_DATABRICKS_JOB)
      }
    }
  }, [])

  useEffect(() => {
    // Connect WebSocket for real-time updates
    connectSocket()

    fetchPipelineData()

    // WebSocket listeners for real-time updates using subscribeToEvent
    // subscribeToEvent returns an unsubscribe function
    const unsubBronze = subscribeToEvent('claim_to_bronze', (data) => {
      console.log('New claim in Bronze:', data)
      fetchPendingClaims()
    })

    const unsubSilver = subscribeToEvent('silver_processed', (data) => {
      console.log('Silver processing complete:', data)
      fetchPendingClaims()
    })

    const unsubGold = subscribeToEvent('gold_processed', (data) => {
      console.log('Gold processing complete:', data)
      fetchPendingClaims()
      fetchPipelineData()
    })

    // Databricks job events
    const unsubDatabricksStarted = subscribeToEvent('databricks_job_started', (data) => {
      console.log('Databricks job started:', data)
      setDatabricksJob({
        run_id: data.run_id,
        job_url: data.job_url,
        layer: data.layer,
        tasks: data.tasks,
        status: 'running',
        started_at: data.timestamp
      })
    })

    const unsubDatabricksCompleted = subscribeToEvent('databricks_job_completed', (data) => {
      console.log('Databricks job completed:', data)
      setDatabricksJob(prev => prev ? { ...prev, status: 'completed' } : null)
      // Update lastProcessingResult to show completed
      setLastProcessingResult(prev => prev && prev.databricks ? {
        ...prev,
        databricks: { ...prev.databricks, completed: true }
      } : prev)
      // Clear localStorage
      localStorage.removeItem(STORAGE_KEYS.ACTIVE_DATABRICKS_JOB)
    })

    // Cleanup: unsubscribe from all events
    return () => {
      if (unsubBronze) unsubBronze()
      if (unsubSilver) unsubSilver()
      if (unsubGold) unsubGold()
      if (unsubDatabricksStarted) unsubDatabricksStarted()
      if (unsubDatabricksCompleted) unsubDatabricksCompleted()
    }
  }, [])

  const fetchPipelineData = async () => {
    try {
      const [statusRes, flowRes] = await Promise.all([
        api.get('/api/pipeline/status'),
        api.get('/api/pipeline/flow')
      ])
      setPipelineStatus(statusRes.data)
      setPipelineFlow(flowRes.data)
      setProcessingLog(statusRes.data.processing_log || [])

      // Extract execution info from status response
      if (statusRes.data.execution_info) {
        setExecutionInfo(statusRes.data.execution_info)
      }

      // Update data mode from backend response
      const source = statusRes.data.data_source
      setDataMode(source === 'azure' || source === 'synapse' ? 'azure' : 'demo')

      // Also fetch pending claims
      await fetchPendingClaims()
    } catch (err) {
      console.error('Error fetching pipeline data:', err)
      // Set demo data
      setDemoData()
    } finally {
      setLoading(false)
    }
  }

  const handleToggleMode = async () => {
    setTogglingMode(true)
    try {
      // Toggle between demo and azure modes
      const newMode = dataMode === 'demo' ? 'azure' : 'demo'
      // Note: Backend toggle API would be at /api/data-source/toggle
      // For now, we just refresh to get current state
      await api.post('/api/pipeline/refresh')
      await fetchPipelineData()
    } catch (err) {
      console.error('Error toggling mode:', err)
    } finally {
      setTogglingMode(false)
    }
  }

  const fetchPendingClaims = async () => {
    try {
      const res = await api.get('/api/pipeline/pending')
      setPendingClaims({
        bronze: res.data.bronze || [],
        silver: res.data.silver || [],
        gold: res.data.gold || []
      })
    } catch (err) {
      console.error('Error fetching pending claims:', err)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await api.post('/api/pipeline/refresh')
      await fetchPipelineData()
    } catch (err) {
      console.error('Error refreshing pipeline:', err)
    } finally {
      setRefreshing(false)
    }
  }

  // Poll Databricks job status WITH localStorage persistence
  const pollDatabricksJobStatusWithStorage = async (runId, layer) => {
    const maxAttempts = 60 // Poll for up to 10 minutes (60 * 10 seconds)
    let attempts = 0
    
    const poll = async () => {
      try {
        const res = await api.get(`/api/pipeline/databricks/run/${runId}`)
        const status = res.data
        
        console.log('Databricks job status:', status)
        
        if (status.is_complete) {
          // Clear localStorage on completion
          localStorage.removeItem(STORAGE_KEYS.ACTIVE_DATABRICKS_JOB)
          
          // Update UI
          setLastProcessingResult(prev => prev ? {
            ...prev,
            databricks: { ...prev.databricks, completed: true, success: status.is_success, status }
          } : prev)
          fetchPipelineData()
          return
        }
        
        // Continue polling
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 10000) // Poll every 10 seconds
        } else {
          console.warn('Databricks job polling timeout')
          localStorage.removeItem(STORAGE_KEYS.ACTIVE_DATABRICKS_JOB)
        }
      } catch (err) {
        console.error('Error polling Databricks status:', err)
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 10000)
        }
      }
    }
    
    // Start polling after initial delay
    setTimeout(poll, 5000)
  }

  // Poll Databricks job status (legacy callback version)
  const pollDatabricksJobStatus = async (runId, onComplete) => {
    const maxAttempts = 60 // Poll for up to 10 minutes (60 * 10 seconds)
    let attempts = 0
    
    const poll = async () => {
      try {
        const res = await api.get(`/api/pipeline/databricks/run/${runId}`)
        const status = res.data
        
        console.log('Databricks job status:', status)
        
        if (status.is_complete) {
          // Clear localStorage on completion
          localStorage.removeItem(STORAGE_KEYS.ACTIVE_DATABRICKS_JOB)
          
          if (status.is_success) {
            onComplete(true, status)
          } else {
            onComplete(false, status)
          }
          return
        }
        
        // Continue polling
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 10000) // Poll every 10 seconds
        } else {
          console.warn('Databricks job polling timeout')
          localStorage.removeItem(STORAGE_KEYS.ACTIVE_DATABRICKS_JOB)
          onComplete(false, { error: 'Polling timeout' })
        }
      } catch (err) {
        console.error('Error polling Databricks status:', err)
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 10000)
        }
      }
    }
    
    // Start polling after initial delay
    setTimeout(poll, 5000)
  }

  const handleBronzeToSilver = async () => {
    setProcessing(prev => ({ ...prev, bronzeToSilver: true }))
    setLastProcessingResult(null) // Clear previous result
    try {
      const res = await api.post('/api/pipeline/process/bronze-to-silver')
      console.log('Bronze to Silver result:', res.data)
      // Store processing result with proof
      setLastProcessingResult({
        type: 'Bronze → Silver',
        ...res.data
      })
      
      // If Databricks job was triggered, save to localStorage and start polling
      if (res.data.databricks?.triggered && res.data.databricks?.run_id) {
        // Save to localStorage for restoration on page return
        localStorage.setItem(STORAGE_KEYS.ACTIVE_DATABRICKS_JOB, JSON.stringify({
          run_id: res.data.databricks.run_id,
          job_url: res.data.databricks.job_url,
          layer: 'bronze_silver',
          started_at: new Date().toISOString()
        }))
        
        pollDatabricksJobStatus(res.data.databricks.run_id, (success, status) => {
          console.log('Databricks job finished:', success, status)
          setLastProcessingResult(prev => prev ? {
            ...prev,
            databricks: { ...prev.databricks, completed: true, success, status }
          } : prev)
          fetchPipelineData()
        })
      }
      
      // Small delay to ensure backend state is updated before fetching
      await new Promise(resolve => setTimeout(resolve, 500))
      await fetchPendingClaims()
      await fetchPipelineData()
    } catch (err) {
      console.error('Error processing Bronze to Silver:', err)
    } finally {
      setProcessing(prev => ({ ...prev, bronzeToSilver: false }))
    }
  }

  const handleSilverToGold = async () => {
    setProcessing(prev => ({ ...prev, silverToGold: true }))
    setLastProcessingResult(null) // Clear previous result
    try {
      const res = await api.post('/api/pipeline/process/silver-to-gold')
      console.log('Silver to Gold result:', res.data)
      // Store processing result with proof
      setLastProcessingResult({
        type: 'Silver → Gold',
        ...res.data
      })
      
      // If Databricks job was triggered, start polling for completion
      if (res.data.databricks?.triggered && res.data.databricks?.run_id) {
        pollDatabricksJobStatus(res.data.databricks.run_id, (success, status) => {
          console.log('Databricks job finished:', success, status)
          setLastProcessingResult(prev => prev ? {
            ...prev,
            databricks: { ...prev.databricks, completed: true, success, status }
          } : prev)
          fetchPipelineData()
        })
      }
      
      await fetchPendingClaims()
      await fetchPipelineData()
    } catch (err) {
      console.error('Error processing Silver to Gold:', err)
    } finally {
      setProcessing(prev => ({ ...prev, silverToGold: false }))
    }
  }

  const handleClearPipeline = async () => {
    setResetting(true)
    setResetError(null)
    try {
      await api.delete('/api/pipeline/clear')
      await fetchPendingClaims()
      await fetchPipelineData()
      setShowResetConfirm(false)
    } catch (err) {
      console.error('Error clearing pipeline:', err)
      setResetError('Failed to clear pipeline. Please try again.')
    } finally {
      setResetting(false)
    }
  }

  const setDemoData = () => {
    setPipelineStatus({
      data_source: 'demo',
      layers: {
        bronze: { status: 'active', record_count: 15000, description: 'Raw data ingestion', last_update: new Date().toISOString() },
        silver: { status: 'active', record_count: 14500, description: 'Cleaned & validated', last_update: new Date().toISOString() },
        gold: { status: 'active', record_count: 5000, description: 'Business aggregations', last_update: new Date().toISOString() }
      },
      metrics: {
        total_customers: 5000,
        total_pets: 6500,
        total_policies: 6000,
        total_claims: 15000,
        total_providers: 200
      },
      data_quality: {
        completeness: 95.5,
        accuracy: 98.2,
        freshness: 'Cached'
      }
    })
    setPipelineFlow({
      nodes: [],
      edges: [],
      active_flow: false
    })
    setDataMode('demo')
  }

  const layers = pipelineStatus?.layers || {}
  const metrics = pipelineStatus?.metrics || {}
  const quality = pipelineStatus?.data_quality || {}
  // Check if connected to Azure (either ADLS or Synapse)
  const isLive = pipelineStatus?.data_source === 'synapse' || pipelineStatus?.data_source === 'azure'
  const pendingCounts = pipelineStatus?.pending_claims || { bronze: 0, silver: 0, gold: 0 }

  const hasBronzePending = pendingClaims.bronze.length > 0
  const hasSilverPending = pendingClaims.silver.length > 0

  return (
    <div className="space-y-6 relative">
      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/70 z-10 flex items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
            <span className="text-sm text-gray-600">Loading pipeline...</span>
          </div>
        </div>
      )}

      {/* Databricks Job Running Indicator */}
      {databricksJob && databricksJob.status === 'running' && (
        <div className="fixed bottom-4 right-4 z-50 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-lg shadow-lg p-4 animate-pulse">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin" />
            <div>
              <p className="font-semibold">Databricks Job Running</p>
              <p className="text-xs opacity-90">
                {databricksJob.layer === 'bronze_silver' ? 'Bronze + Silver' : 'Gold'} notebooks executing
              </p>
            </div>
            <a
              href={databricksJob.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 px-3 py-1 bg-white/20 rounded-full text-xs hover:bg-white/30 flex items-center gap-1"
            >
              <ExternalLink className="h-3 w-3" />
              View
            </a>
            <button
              onClick={() => setDatabricksJob(null)}
              className="ml-1 text-white/70 hover:text-white"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Rule Engine Pipeline</h1>
          <p className="text-gray-500">Traditional Medallion Lakehouse Architecture (Bronze → Silver → Gold)</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Data Mode Toggle Switch */}
          <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
            <span className={`text-sm font-medium ${dataMode === 'demo' ? 'text-yellow-700' : 'text-gray-400'}`}>
              Demo
            </span>
            <button
              onClick={handleToggleMode}
              disabled={togglingMode}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                isLive ? 'bg-green-500' : 'bg-gray-300'
              } ${togglingMode ? 'opacity-50 cursor-not-allowed' : ''}`}
              title={isLive ? 'Connected to Azure - Click to refresh' : 'Demo Mode - Azure not configured'}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isLive ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm font-medium ${isLive ? 'text-green-700' : 'text-gray-400'}`}>
              Azure
            </span>
          </div>
          {/* Status Badge */}
          <div className={`px-3 py-1 rounded-full text-sm ${
            isLive ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
          }`}>
            {isLive ? (pipelineStatus?.data_source === 'synapse' ? 'Connected to Synapse' : 'Connected to Azure ADLS') : 'Demo Mode (In-Memory)'}
          </div>
          {showResetConfirm ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
              {resetError ? (
                <>
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <span className="text-sm text-red-700">{resetError}</span>
                  <button
                    onClick={() => { setResetError(null); setShowResetConfirm(false); }}
                    className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                  >
                    Dismiss
                  </button>
                </>
              ) : (
                <>
                  <span className="text-sm text-red-700">Clear all pending claims?</span>
                  <button
                    onClick={handleClearPipeline}
                    disabled={resetting}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    {resetting ? (
                      <>
                        <RefreshCw className="h-3 w-3 animate-spin" />
                        Clearing...
                      </>
                    ) : (
                      'Yes, Clear'
                    )}
                  </button>
                  <button
                    onClick={() => setShowResetConfirm(false)}
                    disabled={resetting}
                    className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                </>
              )}
            </div>
          ) : (
            <button
              onClick={() => setShowResetConfirm(true)}
              className="px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg border border-red-200"
            >
              Reset Pipeline
            </button>
          )}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Execution Mode Info Banner */}
      {executionInfo && (
        <div className={`rounded-xl p-4 border-2 ${
          executionInfo.databricks_connected
            ? 'bg-green-50 border-green-300'
            : 'bg-amber-50 border-amber-300'
        }`}>
          <div className="flex items-start gap-3">
            <div className={`p-2 rounded-lg ${
              executionInfo.databricks_connected ? 'bg-green-100' : 'bg-amber-100'
            }`}>
              {executionInfo.databricks_connected ? (
                <Sparkles className="h-5 w-5 text-green-600" />
              ) : (
                <Cpu className="h-5 w-5 text-amber-600" />
              )}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className={`font-semibold ${
                  executionInfo.databricks_connected ? 'text-green-800' : 'text-amber-800'
                }`}>
                  Execution Mode: {executionInfo.databricks_connected ? 'Databricks Notebooks' : 'Python Local Processing'}
                </h4>
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                  executionInfo.databricks_connected
                    ? 'bg-green-200 text-green-800'
                    : 'bg-amber-200 text-amber-800'
                }`}>
                  {executionInfo.mode}
                </span>
              </div>
              <p className="text-sm text-gray-600">{executionInfo.description}</p>
              {executionInfo.note && (
                <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                  <Info className="h-3 w-3" />
                  {executionInfo.note}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Manual Pipeline Triggers */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-blue-900">Manual Pipeline Triggers</h3>
          </div>
          {/* Databricks Job Link */}
          {executionInfo?.databricks_connected && (
            <a
              href="https://adb-7405619408519767.7.azuredatabricks.net/#job/591500457291311"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
            >
              <Sparkles className="h-4 w-4" />
              View Databricks ETL Job
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
        <p className="text-sm text-blue-700 mb-4">
          Manually trigger data processing between layers. Claims submitted from Customer Portal appear in Bronze layer first.
        </p>
        <div className="flex items-center gap-4">
          <button
            onClick={handleBronzeToSilver}
            disabled={processing.bronzeToSilver || pendingClaims.bronze.length === 0}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${
              pendingClaims.bronze.length > 0
                ? 'bg-amber-500 text-white hover:bg-amber-600'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
            } disabled:opacity-50`}
          >
            {processing.bronzeToSilver ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <Play className="h-5 w-5" />
            )}
            Process Bronze → Silver
            {pendingClaims.bronze.length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-white/30 rounded text-sm">
                {pendingClaims.bronze.length}
              </span>
            )}
          </button>

          <ArrowRight className="h-6 w-6 text-gray-400" />

          <div className="flex items-center gap-2 px-6 py-3 bg-yellow-100 text-yellow-800 rounded-lg font-semibold">
            <BarChart3 className="h-5 w-5" />
            Dashboard Ready
            {pendingClaims.gold.length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-yellow-200 rounded text-sm">
                {pendingClaims.gold.length}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Processing Proof - Show after processing */}
      {lastProcessingResult && lastProcessingResult.success && (
        <div className={`rounded-xl p-6 border ${
          lastProcessingResult.databricks?.triggered && !lastProcessingResult.databricks?.completed
            ? 'bg-gradient-to-r from-orange-50 to-amber-50 border-orange-300'
            : 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              {lastProcessingResult.databricks?.triggered && !lastProcessingResult.databricks?.completed ? (
                <RefreshCw className="h-5 w-5 text-orange-600 animate-spin" />
              ) : (
                <CheckCircle className="h-5 w-5 text-green-600" />
              )}
              <h3 className={`text-lg font-semibold ${
                lastProcessingResult.databricks?.triggered && !lastProcessingResult.databricks?.completed
                  ? 'text-orange-800'
                  : 'text-green-800'
              }`}>
                Processing: {lastProcessingResult.type}
              </h3>
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                lastProcessingResult.databricks?.triggered && !lastProcessingResult.databricks?.completed
                  ? 'bg-orange-200 text-orange-800'
                  : lastProcessingResult.notebook_executed
                    ? 'bg-green-200 text-green-800'
                    : 'bg-amber-200 text-amber-800'
              }`}>
                {lastProcessingResult.databricks?.triggered && !lastProcessingResult.databricks?.completed
                  ? 'Databricks Running'
                  : lastProcessingResult.execution_mode === 'python_local' 
                    ? 'Python Local' 
                    : 'Databricks'}
              </span>
            </div>
            <button
              onClick={() => setLastProcessingResult(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* Execution Engine */}
          <div className="mb-4 p-3 bg-white/50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Engine:</strong> {lastProcessingResult.execution_engine || 'PetInsure360 Backend'}
            </p>
            <p className="text-sm text-gray-600">
              <strong>Claims Processed:</strong> {lastProcessingResult.processed}
            </p>
            {/* Databricks Job Link */}
            {lastProcessingResult.databricks && lastProcessingResult.databricks.triggered && (
              <div className={`mt-2 pt-2 border-t ${
                lastProcessingResult.databricks?.completed 
                  ? 'border-green-200' 
                  : 'border-orange-200'
              }`}>
                <div className="flex items-center gap-2">
                  <Sparkles className={`h-4 w-4 ${
                    lastProcessingResult.databricks?.completed 
                      ? 'text-green-500' 
                      : 'text-orange-500'
                  }`} />
                  <span className={`text-sm font-medium ${
                    lastProcessingResult.databricks?.completed 
                      ? 'text-green-700' 
                      : 'text-orange-700'
                  }`}>
                    {lastProcessingResult.databricks?.completed 
                      ? 'Databricks Job Completed' 
                      : 'Databricks Job Running...'}
                  </span>
                  <a
                    href={lastProcessingResult.databricks.job_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full transition-colors ${
                      lastProcessingResult.databricks?.completed
                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                        : 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                    }`}
                  >
                    <ExternalLink className="h-3 w-3" />
                    View in Databricks
                  </a>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Run ID: {lastProcessingResult.databricks.run_id} | Tasks: {lastProcessingResult.databricks.tasks?.join(', ')}
                </p>
                {!lastProcessingResult.databricks?.completed && (
                  <p className="text-xs text-orange-600 mt-1 italic">
                    Note: Local processing complete. Databricks job running in background - check Databricks UI for status.
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Transformations Applied */}
          {lastProcessingResult.transformations_applied && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-green-700 mb-2">Transformations Applied:</h4>
              <div className="flex flex-wrap gap-2">
                {lastProcessingResult.transformations_applied.map((t, idx) => (
                  <span key={idx} className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Processing Proof Details */}
          {lastProcessingResult.processing_proof && lastProcessingResult.processing_proof.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-green-700 mb-2">Claim Processing Details:</h4>
              <div className="max-h-48 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-green-100">
                    <tr>
                      <th className="text-left p-2">Claim ID</th>
                      {lastProcessingResult.type.includes('Silver') && lastProcessingResult.processing_proof[0]?.completeness_score !== undefined && (
                        <>
                          <th className="text-right p-2">Completeness</th>
                          <th className="text-right p-2">Validity</th>
                          <th className="text-right p-2">Quality</th>
                        </>
                      )}
                      {lastProcessingResult.type.includes('Gold') && lastProcessingResult.processing_proof[0]?.estimated_reimbursement !== undefined && (
                        <>
                          <th className="text-left p-2">Customer</th>
                          <th className="text-right p-2">Amount</th>
                          <th className="text-right p-2">Reimbursement</th>
                          <th className="text-left p-2">Priority</th>
                        </>
                      )}
                      <th className="text-right p-2">Processed At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lastProcessingResult.processing_proof.map((proof, idx) => (
                      <tr key={idx} className="border-t border-green-100">
                        <td className="p-2 font-mono text-xs">{proof.claim_id}</td>
                        {lastProcessingResult.type.includes('Silver') && proof.completeness_score !== undefined && (
                          <>
                            <td className="text-right p-2">{proof.completeness_score}%</td>
                            <td className="text-right p-2">{proof.validity_score}%</td>
                            <td className="text-right p-2 font-semibold">{proof.overall_quality_score}%</td>
                          </>
                        )}
                        {lastProcessingResult.type.includes('Gold') && proof.estimated_reimbursement !== undefined && (
                          <>
                            <td className="p-2">{proof.customer_name}</td>
                            <td className="text-right p-2">${proof.claim_amount?.toLocaleString()}</td>
                            <td className="text-right p-2 font-semibold text-green-700">${proof.estimated_reimbursement?.toLocaleString()}</td>
                            <td className="p-2">
                              <span className={`px-2 py-0.5 text-xs rounded ${
                                proof.processing_priority === 'High' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                              }`}>
                                {proof.processing_priority}
                              </span>
                            </td>
                          </>
                        )}
                        <td className="text-right p-2 text-xs text-gray-500">
                          {proof.processed_at ? new Date(proof.processed_at).toLocaleTimeString() : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pending Claims by Layer */}
      <div className="grid grid-cols-3 gap-4">
        <PendingClaimsCard
          title="Bronze Layer (Raw)"
          claims={pendingClaims.bronze}
          layer="bronze"
          colorClass="border-amber-300 bg-amber-50"
        />
        <PendingClaimsCard
          title="Silver Layer (Validated)"
          claims={pendingClaims.silver}
          layer="silver"
          colorClass="border-gray-300 bg-gray-50"
        />
        <PendingClaimsCard
          title="Gold Layer (Aggregated)"
          claims={pendingClaims.gold}
          layer="gold"
          colorClass="border-yellow-300 bg-yellow-50"
        />
      </div>

      {/* Pipeline Flow Visualization */}
      <div className="chart-card">
        <h3 className="text-lg font-semibold mb-6">Data Flow Architecture</h3>
        <div className="flex items-center justify-between px-4 py-8 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl">
          <PipelineNode
            label="API Ingestion"
            icon={Cloud}
            status="active"
            description="FastAPI endpoints"
            isActive={true}
          />
          <FlowArrow isActive={true} hasData={hasBronzePending} />
          <PipelineNode
            label="Bronze Layer"
            icon={Database}
            status={layers.bronze?.status || 'active'}
            count={layers.bronze?.record_count}
            pendingCount={pendingClaims.bronze.length}
            description="Raw JSON/CSV data"
            isActive={true}
          />
          <FlowArrow isActive={true} hasData={hasBronzePending} />
          <PipelineNode
            label="Databricks"
            icon={Server}
            status={processing.bronzeToSilver ? 'processing' : 'active'}
            description="Spark processing"
            isActive={true}
          />
          <FlowArrow isActive={true} hasData={hasSilverPending} />
          <PipelineNode
            label="Silver Layer"
            icon={Database}
            status={layers.silver?.status || 'active'}
            count={layers.silver?.record_count}
            pendingCount={pendingClaims.silver.length}
            description="Clean & validated"
            isActive={true}
          />
          <FlowArrow isActive={true} hasData={hasSilverPending} />
          <PipelineNode
            label="Gold Layer"
            icon={Database}
            status={layers.gold?.status || 'active'}
            count={layers.gold?.record_count}
            pendingCount={pendingClaims.gold.length}
            description="Business metrics"
            isActive={true}
          />
          <FlowArrow isActive={true} />
          <PipelineNode
            label="Dashboard"
            icon={BarChart3}
            status="active"
            description="Analytics views"
            isActive={true}
          />
        </div>
      </div>

      {/* Processing Log */}
      {processingLog.length > 0 && (
        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Processing Log
          </h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {processingLog.slice().reverse().map((log, idx) => (
              <div key={idx} className={`flex items-center gap-3 p-2 rounded ${
                log.action === 'BRONZE_INGEST' ? 'bg-amber-50' :
                log.action === 'SILVER_PROCESS' ? 'bg-gray-50' :
                log.action === 'GOLD_PROCESS' ? 'bg-yellow-50' :
                'bg-gray-50'
              }`}>
                <span className="text-xs text-gray-400 font-mono">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className={`px-2 py-0.5 text-xs font-semibold rounded ${
                  log.action === 'BRONZE_INGEST' ? 'bg-amber-200 text-amber-800' :
                  log.action === 'SILVER_PROCESS' ? 'bg-gray-200 text-gray-800' :
                  log.action === 'GOLD_PROCESS' ? 'bg-yellow-200 text-yellow-800' :
                  'bg-gray-200 text-gray-800'
                }`}>
                  {log.action}
                </span>
                <span className="text-sm text-gray-700">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-5 gap-4">
        <div className="stat-card">
          <p className="text-sm text-gray-500">Customers</p>
          <p className="text-2xl font-bold">{metrics.total_customers?.toLocaleString() || 0}</p>
        </div>
        <div className="stat-card">
          <p className="text-sm text-gray-500">Pets</p>
          <p className="text-2xl font-bold">{metrics.total_pets?.toLocaleString() || 0}</p>
        </div>
        <div className="stat-card">
          <p className="text-sm text-gray-500">Policies</p>
          <p className="text-2xl font-bold">{metrics.total_policies?.toLocaleString() || 0}</p>
        </div>
        <div className="stat-card">
          <p className="text-sm text-gray-500">Claims</p>
          <p className="text-2xl font-bold">{metrics.total_claims?.toLocaleString() || 0}</p>
        </div>
        <div className="stat-card">
          <p className="text-sm text-gray-500">Providers</p>
          <p className="text-2xl font-bold">{metrics.total_providers?.toLocaleString() || 0}</p>
        </div>
      </div>

      {/* Data Quality Section */}
      <div className="grid grid-cols-2 gap-6">
        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Data Quality Metrics</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600">Completeness</span>
                <span className="text-sm font-semibold">{quality.completeness || 95.5}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${quality.completeness || 95.5}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600">Accuracy</span>
                <span className="text-sm font-semibold">{quality.accuracy || 98.2}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${quality.accuracy || 98.2}%` }}
                ></div>
              </div>
            </div>
            <div className="flex items-center justify-between pt-2">
              <span className="text-sm text-gray-600">Data Freshness</span>
              <span className={`px-2 py-1 rounded text-sm ${
                quality.freshness === 'Real-time' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {quality.freshness || 'Cached'}
              </span>
            </div>
          </div>
        </div>

        <div className="chart-card">
          <h3 className="text-lg font-semibold mb-4">Layer Details</h3>
          <div className="space-y-3">
            {Object.entries(layers).map(([name, layer]) => (
              <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {layer.status === 'active' ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : layer.status === 'processing' ? (
                    <Clock className="h-5 w-5 text-yellow-500 animate-spin" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  <div>
                    <p className="font-medium capitalize">{name} Layer</p>
                    <p className="text-xs text-gray-500">{layer.description}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold">{layer.record_count?.toLocaleString()} records</p>
                  <p className="text-xs text-gray-400">
                    {layer.last_update ? new Date(layer.last_update).toLocaleTimeString() : 'N/A'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Technology Stack */}
      <div className="chart-card">
        <h3 className="text-lg font-semibold mb-4">Technology Stack</h3>
        <div className="grid grid-cols-6 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="font-semibold text-blue-700">Azure Databricks</p>
            <p className="text-xs text-gray-500">Data Processing</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="font-semibold text-purple-700">Azure Synapse</p>
            <p className="text-xs text-gray-500">Analytics</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="font-semibold text-green-700">ADLS Gen2</p>
            <p className="text-xs text-gray-500">Data Lake Storage</p>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="font-semibold text-yellow-700">Delta Lake</p>
            <p className="text-xs text-gray-500">Table Format</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="font-semibold text-red-700">FastAPI</p>
            <p className="text-xs text-gray-500">Backend API</p>
          </div>
          <div className="text-center p-4 bg-cyan-50 rounded-lg">
            <p className="font-semibold text-cyan-700">React</p>
            <p className="text-xs text-gray-500">Frontend</p>
          </div>
        </div>
      </div>
    </div>
  )
}
