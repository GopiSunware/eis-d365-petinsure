import { useState, useEffect } from 'react'
import { Database, Server, BarChart3, Cloud, ArrowRight, RefreshCw, CheckCircle, Clock, AlertCircle, Play, Zap, FileText, ListChecks, ToggleLeft, ToggleRight } from 'lucide-react'
import api from '../services/api'
import { connectSocket, subscribeToEvent } from '../services/socket'

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

    // Cleanup: unsubscribe from all events
    return () => {
      if (unsubBronze) unsubBronze()
      if (unsubSilver) unsubSilver()
      if (unsubGold) unsubGold()
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

  const handleBronzeToSilver = async () => {
    setProcessing(prev => ({ ...prev, bronzeToSilver: true }))
    try {
      const res = await api.post('/api/pipeline/process/bronze-to-silver')
      console.log('Bronze to Silver result:', res.data)
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
    try {
      const res = await api.post('/api/pipeline/process/silver-to-gold')
      console.log('Silver to Gold result:', res.data)
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

      {/* Manual Processing Controls */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-blue-900">Manual Pipeline Triggers</h3>
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

          <button
            onClick={handleSilverToGold}
            disabled={processing.silverToGold || pendingClaims.silver.length === 0}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${
              pendingClaims.silver.length > 0
                ? 'bg-gray-600 text-white hover:bg-gray-700'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
            } disabled:opacity-50`}
          >
            {processing.silverToGold ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <Play className="h-5 w-5" />
            )}
            Process Silver → Gold
            {pendingClaims.silver.length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-white/30 rounded text-sm">
                {pendingClaims.silver.length}
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
