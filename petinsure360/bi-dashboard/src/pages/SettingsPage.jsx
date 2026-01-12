import { useState, useEffect } from 'react'
import { Settings, Cpu, Zap, CheckCircle, XCircle, Loader2, Sparkles, Bot, Brain, Trash2, RefreshCw, AlertTriangle } from 'lucide-react'
import api from '../services/api'

// AI Claims API base URL (WS2) - Uses Claims Data API which has AI config endpoints
const AI_API_BASE = import.meta.env.VITE_AI_API_URL || import.meta.env.VITE_CLAIMS_API_URL || 'http://localhost:8002'
// Agent Pipeline URL - for testing the actual agent service
const AGENT_PIPELINE_URL = (import.meta.env.VITE_PIPELINE_URL || 'http://localhost:8006').replace(/\/api$/, '')

export default function SettingsPage() {
  const [selectedProvider, setSelectedProvider] = useState('')
  const [selectedModel, setSelectedModel] = useState('')
  const [temperature, setTemperature] = useState(0.7)
  const [maxTokens, setMaxTokens] = useState(2000)
  const [testResult, setTestResult] = useState(null)
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [config, setConfig] = useState(null)
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(true)

  // Fetch current config and models
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [configRes, modelsRes] = await Promise.all([
          fetch(`${AI_API_BASE}/api/v1/claims/ai/config`),
          fetch(`${AI_API_BASE}/api/v1/claims/ai/models`)
        ])

        if (configRes.ok) {
          const configData = await configRes.json()
          setConfig(configData)
          setSelectedProvider(configData.provider || '')
          setSelectedModel(configData.model_id || '')
          setTemperature(configData.temperature || 0.7)
          setMaxTokens(configData.max_tokens || 2000)
        }

        if (modelsRes.ok) {
          const modelsData = await modelsRes.json()
          setModels(modelsData.models || [])
        }
      } catch (error) {
        console.error('Failed to fetch AI config:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  // Filter models by provider
  const filteredModels = models.filter(m => m.provider === selectedProvider)

  const handleProviderChange = (provider) => {
    setSelectedProvider(provider)
    const providerModels = models.filter(m => m.provider === provider)
    if (providerModels.length > 0) {
      setSelectedModel(providerModels[0].model_id)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const response = await fetch(`${AI_API_BASE}/api/v1/claims/ai/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: selectedProvider,
          model_id: selectedModel,
          temperature,
          max_tokens: maxTokens
        })
      })
      if (response.ok) {
        const updated = await response.json()
        setConfig(updated)
        setTestResult({ status: 'success', response: 'Configuration saved successfully!' })
      }
    } catch (error) {
      setTestResult({ status: 'error', error: error.message })
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    
    // Test the SELECTED provider (what user chose in UI), not what backend has
    const testProvider = selectedProvider
    const testModel = selectedModel
    
    // Test Agent Pipeline with the selected provider/model
    let pipelineResult = null
    try {
      const pipelineRes = await fetch(`${AGENT_PIPELINE_URL}/ai/test?provider=${testProvider}&model=${testModel}`, {
        method: 'POST'
      })
      pipelineResult = await pipelineRes.json()
    } catch (error) {
      pipelineResult = { status: 'error', message: `Agent Pipeline unreachable: ${error.message}` }
    }
    
    // Set result based on the test
    const status = pipelineResult?.status || 'error'
    
    setTestResult({
      status: status,
      message: pipelineResult?.message || 'Connection test failed',
      provider: testProvider,
      model: testModel,
      details: {
        agent_pipeline: pipelineResult
      }
    })
    
    setTesting(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading AI configuration...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Settings</h1>
          <p className="text-gray-600">Configure AI provider and model for claims processing</p>
        </div>
        <div className="flex items-center space-x-2">
          <Sparkles className="h-6 w-6 text-blue-600" />
          <span className="text-sm text-gray-500">AI-Powered Insurance</span>
        </div>
      </div>

      {/* AI Configuration Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
          <div className="flex items-center space-x-3">
            <Brain className="h-6 w-6 text-white" />
            <h2 className="text-lg font-semibold text-white">AI Configuration</h2>
          </div>
          <p className="text-blue-100 text-sm mt-1">
            Select the AI provider and model for claims processing and fraud detection
          </p>
        </div>

        <div className="p-6 space-y-6">
          {/* Provider Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              AI Provider
            </label>
            <div className="grid grid-cols-2 gap-4">
              {/* Claude Option */}
              <button
                onClick={() => handleProviderChange('claude')}
                className={`relative flex items-center p-4 rounded-lg border-2 transition-all cursor-pointer ${
                  selectedProvider === 'claude'
                    ? 'border-orange-500 bg-orange-50'
                    : 'border-gray-200 hover:border-orange-300'
                }`}
              >
                <div className="flex-shrink-0">
                  <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                    <Bot className="h-6 w-6 text-orange-600" />
                  </div>
                </div>
                <div className="ml-4 text-left">
                  <h3 className="text-sm font-semibold text-gray-900">Anthropic Claude</h3>
                  <p className="text-xs text-gray-500">Advanced reasoning & analysis</p>
                </div>
                {selectedProvider === 'claude' && (
                  <CheckCircle className="absolute top-2 right-2 h-5 w-5 text-orange-500" />
                )}
              </button>

              {/* OpenAI Option */}
              <button
                onClick={() => handleProviderChange('openai')}
                className={`relative flex items-center p-4 rounded-lg border-2 transition-all cursor-pointer ${
                  selectedProvider === 'openai'
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 hover:border-green-300'
                }`}
              >
                <div className="flex-shrink-0">
                  <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                    <Cpu className="h-6 w-6 text-green-600" />
                  </div>
                </div>
                <div className="ml-4 text-left">
                  <h3 className="text-sm font-semibold text-gray-900">Azure OpenAI</h3>
                  <p className="text-xs text-gray-500">GPT-4 powered analysis</p>
                </div>
                {selectedProvider === 'openai' && (
                  <CheckCircle className="absolute top-2 right-2 h-5 w-5 text-green-500" />
                )}
              </button>
            </div>
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {filteredModels.length > 0 ? (
                filteredModels.map((model) => (
                  <option key={model.model_id} value={model.model_id}>
                    {model.display_name} - {model.description}
                  </option>
                ))
              ) : (
                <option value="">Select a provider first</option>
              )}
            </select>
          </div>

          {/* Advanced Settings */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature: {temperature}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Precise (0)</span>
                <span>Creative (1)</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Tokens
              </label>
              <select
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={1000}>1,000 (Fast)</option>
                <option value={2000}>2,000 (Balanced)</option>
                <option value={4000}>4,000 (Detailed)</option>
                <option value={8000}>8,000 (Maximum)</option>
              </select>
            </div>
          </div>

          {/* Current Configuration Display */}
          {config && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Current Active Configuration</h4>
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Provider:</span>
                  <span className="ml-2 font-medium capitalize">{config.provider}</span>
                </div>
                <div>
                  <span className="text-gray-500">Model:</span>
                  <span className="ml-2 font-medium">{config.model_id}</span>
                </div>
                <div>
                  <span className="text-gray-500">Temperature:</span>
                  <span className="ml-2 font-medium">{config.temperature}</span>
                </div>
                <div>
                  <span className="text-gray-500">Max Tokens:</span>
                  <span className="ml-2 font-medium">{config.max_tokens}</span>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <button
              onClick={handleTest}
              disabled={testing}
              className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              {testing ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Zap className="h-4 w-4 mr-2" />
              )}
              Test Connection
            </button>

            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="h-4 w-4 mr-2" />
              )}
              Save Configuration
            </button>
          </div>

          {/* Test Result */}
          {testResult && (
            <div
              className={`mt-4 p-4 rounded-lg ${
                testResult.status === 'success'
                  ? 'bg-green-50 border border-green-200'
                  : testResult.status === 'warning'
                  ? 'bg-yellow-50 border border-yellow-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className="flex items-center">
                {testResult.status === 'success' ? (
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                ) : testResult.status === 'warning' ? (
                  <Zap className="h-5 w-5 text-yellow-500 mr-2" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500 mr-2" />
                )}
                <span
                  className={`font-medium ${
                    testResult.status === 'success' ? 'text-green-700' 
                    : testResult.status === 'warning' ? 'text-yellow-700'
                    : 'text-red-700'
                  }`}
                >
                  {testResult.status === 'success' ? 'Connection Successful!' 
                   : testResult.status === 'warning' ? 'Connection Warning'
                   : 'Connection Failed'}
                </span>
              </div>
              
              {/* Provider/Model being tested */}
              <p className="mt-2 text-xs text-gray-600">
                Testing: <span className="font-medium capitalize">{testResult.provider}</span> ({testResult.model})
              </p>
              
              {/* Main message */}
              {testResult.message && (
                <p className={`mt-2 text-sm ${
                  testResult.status === 'success' ? 'text-green-600'
                  : testResult.status === 'warning' ? 'text-yellow-600'
                  : 'text-red-600'
                }`}>
                  {testResult.message}
                </p>
              )}
              
              {/* Legacy support */}
              {testResult.response && !testResult.message && (
                <p className="mt-2 text-sm text-green-600">{testResult.response}</p>
              )}
              {testResult.error && (
                <p className="mt-2 text-sm text-red-600">{testResult.error}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Demo Data Management */}
      <DemoDataManagement />

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <Settings className="h-5 w-5 text-blue-600" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">AI Configuration</h3>
            <p className="mt-1 text-sm text-blue-700">
              Configure AI providers (Claude or OpenAI) and select models for claims processing.
              Changes take effect immediately for new submissions and fraud detection analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Demo Data Management Component
function DemoDataManagement() {
  const [clearing, setClearing] = useState(false)
  const [clearResult, setClearResult] = useState(null)
  const [showConfirm, setShowConfirm] = useState(false)

  const handleClearClick = () => {
    setClearResult(null)
    setShowConfirm(true)
  }

  const handleCancel = () => {
    setShowConfirm(false)
  }

  const handleConfirmClear = async () => {
    setShowConfirm(false)
    setClearing(true)
    setClearResult(null)

    try {
      const response = await api.delete('/api/pipeline/clear?include_demo_data=true')
      setClearResult({
        success: true,
        message: 'All pipelines cleared successfully!',
        details: response.data
      })
    } catch (error) {
      setClearResult({
        success: false,
        message: 'Failed to clear pipelines',
        error: error.message
      })
    } finally {
      setClearing(false)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="bg-gradient-to-r from-gray-700 to-gray-800 px-6 py-4">
        <div className="flex items-center space-x-3">
          <RefreshCw className="h-6 w-6 text-white" />
          <h2 className="text-lg font-semibold text-white">Pipeline Management</h2>
        </div>
        <p className="text-gray-300 text-sm mt-1">
          Reset pipeline data for fresh testing
        </p>
      </div>

      <div className="p-6 space-y-4">
        {/* Inline Confirmation */}
        {showConfirm ? (
          <div className="bg-amber-50 border border-amber-300 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-800">
                  Are you sure you want to clear all pipelines?
                </p>
                <p className="text-sm text-amber-700 mt-1">
                  This will remove all claims from Rule Engine, Agent Pipeline, and DocGen batches.
                  Demo users, pets, and policies will be preserved.
                </p>
                <div className="flex gap-3 mt-4">
                  <button
                    onClick={handleConfirmClear}
                    className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700"
                  >
                    Yes, Clear All
                  </button>
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Normal State */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">
                  Clear all pipeline data including claims, runs, and document batches.
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Demo users and policies will be preserved.
                </p>
              </div>
              <button
                onClick={handleClearClick}
                disabled={clearing}
                className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                {clearing ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4 mr-2" />
                )}
                Clear All Pipelines
              </button>
            </div>

            {/* Results */}
            {clearResult && (
              <div className={`rounded-lg p-4 text-sm ${
                clearResult.success 
                  ? 'bg-green-50 border border-green-200' 
                  : 'bg-red-50 border border-red-200'
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  {clearResult.success ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-600" />
                  )}
                  <span className={`font-medium ${clearResult.success ? 'text-green-800' : 'text-red-800'}`}>
                    {clearResult.message}
                  </span>
                </div>
                {clearResult.success && clearResult.details && (
                  <div className="grid grid-cols-3 gap-4 text-green-700 mt-2 pt-2 border-t border-green-200">
                    <div>
                      <span className="text-green-600">Rule Engine:</span>
                      <span className="ml-1 font-medium">{clearResult.details.rule_engine?.claims_cleared || 0} claims</span>
                    </div>
                    <div>
                      <span className="text-green-600">Agent Pipeline:</span>
                      <span className="ml-1 font-medium">{clearResult.details.agent_pipeline?.runs_cleared || 0} runs</span>
                    </div>
                    <div>
                      <span className="text-green-600">DocGen:</span>
                      <span className="ml-1 font-medium">{clearResult.details.docgen?.batches_cleared || 0} batches</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
