import { useState, useEffect } from 'react'
import { Upload, FileText, CheckCircle, XCircle, Clock, Loader2, RefreshCw, Trash2, Download, Eye, AlertCircle, Archive, File } from 'lucide-react'

export default function DocGenAdminPage() {
  const [batches, setBatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [serviceStatus, setServiceStatus] = useState(null)
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [exporting, setExporting] = useState({})

  // DocGen service URL (EIS Dynamics DocGen Service)
  const DOCGEN_URL = import.meta.env.VITE_DOCGEN_URL || 'http://localhost:8007'

  useEffect(() => {
    checkServiceHealth()
    loadBatches()
  }, [])

  const checkServiceHealth = async () => {
    try {
      const response = await fetch(`${DOCGEN_URL}/health`)
      if (response.ok) {
        const data = await response.json()
        setServiceStatus(data)
      } else {
        setServiceStatus({ status: 'unavailable' })
      }
    } catch {
      setServiceStatus({ status: 'unavailable' })
    }
  }

  const loadBatches = async () => {
    try {
      setLoading(true)
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

  const handleDeleteBatch = async (batchId) => {
    if (!confirm('Delete this batch? This cannot be undone.')) return

    try {
      await fetch(`${DOCGEN_URL}/api/v1/docgen/batch/${batchId}`, { method: 'DELETE' })
      loadBatches()
    } catch (err) {
      console.error('Error deleting batch:', err)
    }
  }

  const handleProcessBatch = async (batchId) => {
    try {
      await fetch(`${DOCGEN_URL}/api/v1/docgen/process/${batchId}`, { method: 'POST' })
      setTimeout(loadBatches, 1000)
    } catch (err) {
      console.error('Error processing batch:', err)
    }
  }

  const handleExport = async (batchId, format) => {
    setExporting(prev => ({ ...prev, [`${batchId}-${format}`]: true }))
    try {
      const response = await fetch(`${DOCGEN_URL}/api/v1/docgen/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch_id: batchId, formats: [format] })
      })

      if (response.ok) {
        const data = await response.json()
        const downloadUrl = data.download_urls?.[format]
        if (downloadUrl) {
          window.open(downloadUrl, '_blank')
        }
      }
    } catch (err) {
      console.error('Error exporting:', err)
    } finally {
      setExporting(prev => ({ ...prev, [`${batchId}-${format}`]: false }))
    }
  }

  const handleViewBatch = async (batchId) => {
    try {
      const response = await fetch(`${DOCGEN_URL}/api/v1/docgen/batch/${batchId}`)
      if (response.ok) {
        const data = await response.json()
        setSelectedBatch(data)
      }
    } catch (err) {
      console.error('Error loading batch:', err)
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
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

  const getFileIcon = (filename) => {
    if (filename?.endsWith('.zip')) return <Archive className="w-5 h-5 text-purple-500" />
    if (filename?.endsWith('.pdf')) return <FileText className="w-5 h-5 text-red-500" />
    return <File className="w-5 h-5 text-gray-500" />
  }

  // Stats
  const totalBatches = batches.length
  const pendingBatches = batches.filter(b => b.status === 'pending').length
  const completedBatches = batches.filter(b => b.status === 'completed').length
  const failedBatches = batches.filter(b => b.status === 'failed').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">DocGen Admin</h1>
          <p className="text-gray-500">Manage document uploads and AI processing</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Service Status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
            serviceStatus?.status === 'healthy' ? 'bg-green-100 text-green-700' :
            'bg-red-100 text-red-700'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              serviceStatus?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
            }`} />
            {serviceStatus?.status === 'healthy' ? 'Service Online' : 'Service Offline'}
          </div>
          <button
            onClick={() => { loadBatches(); checkServiceHealth(); }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-500">Total Batches</p>
          <p className="text-2xl font-bold text-gray-900">{totalBatches}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-500">Pending</p>
          <p className="text-2xl font-bold text-yellow-600">{pendingBatches}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-500">Completed</p>
          <p className="text-2xl font-bold text-green-600">{completedBatches}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-500">Failed</p>
          <p className="text-2xl font-bold text-red-600">{failedBatches}</p>
        </div>
      </div>

      {/* Batches Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold">Document Batches</h3>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        ) : batches.length === 0 ? (
          <div className="text-center py-12">
            <Upload className="h-12 w-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No batches yet</p>
            <p className="text-gray-400 text-sm">Documents uploaded by users will appear here</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Documents</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">AI Decision</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {batches.map(batch => (
                  <tr key={batch.batch_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <code className="text-sm text-gray-600">{batch.batch_id?.slice(0, 8)}</code>
                      {batch.claim_number && (
                        <span className="ml-2 text-xs text-gray-400">{batch.claim_number}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm">{batch.documents_count || 0} file(s)</span>
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(batch.status)}
                    </td>
                    <td className="px-4 py-3">
                      {batch.ai_decision ? (
                        <span className={`px-2 py-1 text-xs font-medium rounded ${
                          batch.ai_decision === 'auto_approve' || batch.ai_decision === 'proceed'
                            ? 'bg-green-100 text-green-700'
                            : batch.ai_decision === 'needs_review'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {batch.ai_decision.replace(/_/g, ' ')}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(batch.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleViewBatch(batch.batch_id)}
                          className="p-1.5 text-gray-400 hover:text-blue-600"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        {batch.status === 'pending' && (
                          <button
                            onClick={() => handleProcessBatch(batch.batch_id)}
                            className="p-1.5 text-gray-400 hover:text-green-600"
                            title="Process"
                          >
                            <Loader2 className="w-4 h-4" />
                          </button>
                        )}

                        {batch.status === 'completed' && (
                          <>
                            <button
                              onClick={() => handleExport(batch.batch_id, 'pdf')}
                              disabled={exporting[`${batch.batch_id}-pdf`]}
                              className="p-1.5 text-gray-400 hover:text-red-600"
                              title="Export PDF"
                            >
                              {exporting[`${batch.batch_id}-pdf`] ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <Download className="w-4 h-4" />
                              )}
                            </button>
                          </>
                        )}

                        <button
                          onClick={() => handleDeleteBatch(batch.batch_id)}
                          className="p-1.5 text-gray-400 hover:text-red-600"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Batch Detail Modal */}
      {selectedBatch && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b sticky top-0 bg-white flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                Batch: {selectedBatch.batch_id?.slice(0, 8)}
              </h3>
              <button
                onClick={() => setSelectedBatch(null)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ×
              </button>
            </div>
            <div className="p-6 space-y-6">
              {/* Status */}
              <div className="flex items-center gap-4">
                {getStatusBadge(selectedBatch.status)}
                {selectedBatch.ai_decision && (
                  <span className="px-2 py-1 text-sm font-medium rounded bg-purple-100 text-purple-700">
                    Decision: {selectedBatch.ai_decision}
                  </span>
                )}
                {selectedBatch.processing_time_ms && (
                  <span className="text-sm text-gray-500">
                    Processed in {(selectedBatch.processing_time_ms / 1000).toFixed(1)}s
                  </span>
                )}
              </div>

              {/* Documents */}
              <div>
                <h4 className="font-medium mb-3">Documents ({selectedBatch.documents?.length || 0})</h4>
                <div className="space-y-2">
                  {selectedBatch.documents?.map((doc, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      {getFileIcon(doc.original_filename)}
                      <div className="flex-1">
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
                      <div key={idx} className={`flex items-center gap-3 p-3 rounded-lg ${
                        step.result === 'pass' ? 'bg-green-50' :
                        step.result === 'fail' ? 'bg-red-50' :
                        step.result === 'warning' ? 'bg-yellow-50' :
                        'bg-gray-50'
                      }`}>
                        {step.result === 'pass' && <CheckCircle className="w-5 h-5 text-green-500" />}
                        {step.result === 'fail' && <XCircle className="w-5 h-5 text-red-500" />}
                        {step.result === 'warning' && <AlertCircle className="w-5 h-5 text-yellow-500" />}
                        {!step.result && <Clock className="w-5 h-5 text-gray-400" />}
                        <div className="flex-1">
                          <p className="font-medium">{step.message}</p>
                          {step.details && <p className="text-xs text-gray-500">{step.details}</p>}
                        </div>
                        <span className="text-xs bg-gray-200 px-2 py-0.5 rounded">
                          {step.step_type?.replace(/_/g, ' ')}
                        </span>
                      </div>
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
                  <h4 className="font-medium mb-3">Billing</h4>
                  <div className="grid grid-cols-4 gap-4">
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-500">Claim Amount</p>
                      <p className="font-semibold">${selectedBatch.billing.claim_amount}</p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-500">Deductible</p>
                      <p className="font-semibold">${selectedBatch.billing.deductible_applied}</p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-500">Covered Amount</p>
                      <p className="font-semibold">${selectedBatch.billing.covered_amount}</p>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-500">Final Payout</p>
                      <p className="font-semibold text-green-600">${selectedBatch.billing.final_payout}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* AI Reasoning */}
              {selectedBatch.ai_reasoning && (
                <div>
                  <h4 className="font-medium mb-3">AI Reasoning</h4>
                  <div className="bg-purple-50 p-4 rounded-lg text-sm whitespace-pre-wrap">
                    {selectedBatch.ai_reasoning}
                  </div>
                </div>
              )}

              {/* Error */}
              {selectedBatch.error && (
                <div>
                  <h4 className="font-medium mb-3 text-red-600">Error</h4>
                  <div className="bg-red-50 p-4 rounded-lg text-sm text-red-700">
                    {selectedBatch.error}
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
