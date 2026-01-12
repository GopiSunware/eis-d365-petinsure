import { useState, useEffect, useCallback } from 'react'
import { Upload, FileText, CheckCircle, XCircle, Clock, Loader2, X, AlertCircle, RefreshCw, File, Archive } from 'lucide-react'
import api from '../services/api'

export default function UploadDocsPage({ user, addNotification }) {
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [userPets, setUserPets] = useState([])
  const [userPolicies, setUserPolicies] = useState([])
  const [uploads, setUploads] = useState([])
  const [loadingUploads, setLoadingUploads] = useState(true)
  const [dragActive, setDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])
  const [serviceStatus, setServiceStatus] = useState(null)

  const [formData, setFormData] = useState({
    policy_id: '',
    pet_id: '',
    customer_id: ''
  })

  // Check DocGen service health
  const checkServiceHealth = async () => {
    try {
      const response = await api.get('/docgen/health')
      setServiceStatus(response.data.docgen_service === 'connected' ? 'connected' : 'unavailable')
    } catch {
      setServiceStatus('unavailable')
    }
  }

  // Load user's uploads
  const loadUploads = async () => {
    if (!user?.customer_id) return

    try {
      setLoadingUploads(true)
      const response = await api.get(`/docgen/uploads/${user.customer_id}`)
      setUploads(response.data.uploads || [])
    } catch (err) {
      console.error('Error fetching uploads:', err)
    } finally {
      setLoadingUploads(false)
    }
  }

  // Load pets and policies
  useEffect(() => {
    if (user?.customer_id) {
      setFormData(prev => ({ ...prev, customer_id: user.customer_id }))

      // Fetch user's pets and policies
      Promise.all([
        api.get(`/pets/customer/${user.customer_id}`),
        api.get(`/policies/customer/${user.customer_id}`)
      ]).then(([petsRes, policiesRes]) => {
        const pets = petsRes.data.pets || []
        const policies = policiesRes.data.policies || []
        setUserPets(pets)
        setUserPolicies(policies)

        // Auto-select first pet and policy
        if (pets.length > 0) {
          setFormData(prev => ({ ...prev, pet_id: pets[0].pet_id }))
        }
        if (policies.length > 0) {
          setFormData(prev => ({ ...prev, policy_id: policies[0].policy_id }))
        }
      }).catch(err => console.error('Error fetching user data:', err))

      // Load uploads
      loadUploads()
      checkServiceHealth()
    }
  }, [user])

  // Poll for upload status updates
  useEffect(() => {
    const hasProcessing = uploads.some(u => u.status === 'processing' || u.status === 'uploaded')
    if (hasProcessing) {
      const interval = setInterval(loadUploads, 3000)
      return () => clearInterval(interval)
    }
  }, [uploads, user])

  // Handle drag events
  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  // Handle drop
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      setSelectedFiles(prev => [...prev, ...files])
    }
  }, [])

  // Handle file input change
  const handleFileChange = (e) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      setSelectedFiles(prev => [...prev, ...files])
    }
  }

  // Remove file from selection
  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  // Handle form field change
  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  // Get selected pet and policy names
  const getSelectedPetName = () => {
    const pet = userPets.find(p => p.pet_id === formData.pet_id)
    return pet?.pet_name || ''
  }

  const getSelectedPolicyNumber = () => {
    const policy = userPolicies.find(p => p.policy_id === formData.policy_id)
    return policy?.policy_number || policy?.policy_id || ''
  }

  // Upload files
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return
    if (!formData.policy_id || !formData.pet_id) {
      alert('Please select a policy and pet before uploading.')
      return
    }

    setUploading(true)

    try {
      const uploadFormData = new FormData()
      selectedFiles.forEach(file => uploadFormData.append('files', file))
      uploadFormData.append('customer_id', formData.customer_id)
      uploadFormData.append('policy_id', formData.policy_id)
      uploadFormData.append('pet_id', formData.pet_id)
      uploadFormData.append('pet_name', getSelectedPetName())
      uploadFormData.append('policy_number', getSelectedPolicyNumber())

      const response = await api.post('/docgen/upload', uploadFormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      // Clear selection and refresh
      setSelectedFiles([])
      loadUploads()

      // Show notification
      if (addNotification) {
        addNotification('success', 'Documents uploaded! AI processing started.')
      }

    } catch (err) {
      console.error('Upload error:', err)
      if (addNotification) {
        addNotification('error', 'Upload failed. Please try again.')
      }
    } finally {
      setUploading(false)
    }
  }

  // Get file icon
  const getFileIcon = (filename) => {
    if (filename?.endsWith('.zip')) return <Archive className="h-5 w-5 text-purple-500" />
    if (filename?.endsWith('.pdf')) return <FileText className="h-5 w-5 text-red-500" />
    return <File className="h-5 w-5 text-gray-500" />
  }

  // Get status badge
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
          <span className="flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">
            <Clock className="w-3 h-3" />
            In Review
          </span>
        )
      case 'processing':
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
            Uploaded
          </span>
        )
    }
  }

  // Format file size
  const formatFileSize = (bytes) => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (!user) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="card text-center py-12">
          <AlertCircle className="h-12 w-12 mx-auto text-gray-300 mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Sign In Required</h2>
          <p className="text-gray-600">Please sign in to upload documents for your claims.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Submit Claim with Documents</h1>
          <p className="text-gray-600">Upload invoices and receipts for AI-powered claim processing</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Service Status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
            serviceStatus === 'connected' ? 'bg-green-100 text-green-700' :
            serviceStatus === 'unavailable' ? 'bg-amber-100 text-amber-700' :
            'bg-gray-100 text-gray-500'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              serviceStatus === 'connected' ? 'bg-green-500' :
              serviceStatus === 'unavailable' ? 'bg-amber-500' :
              'bg-gray-400'
            }`} />
            {serviceStatus === 'connected' && 'AI Service Ready'}
            {serviceStatus === 'unavailable' && 'AI Queued Mode'}
            {!serviceStatus && 'Checking...'}
          </div>
          <button
            onClick={() => { loadUploads(); checkServiceHealth(); }}
            className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Upload Section */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">New Upload</h2>

        {/* Policy & Pet Selection */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="label">Policy *</label>
            {userPolicies.length > 0 ? (
              <select
                name="policy_id"
                value={formData.policy_id}
                onChange={handleChange}
                required
                className="input-field"
              >
                <option value="">Select policy...</option>
                {userPolicies.map(policy => (
                  <option key={policy.policy_id} value={policy.policy_id}>
                    {policy.policy_number || policy.policy_id} - {policy.plan_type || policy.plan_name}
                  </option>
                ))}
              </select>
            ) : (
              <div className="text-sm text-gray-500 p-2 bg-gray-50 rounded">
                No policies found. Please purchase a policy first.
              </div>
            )}
          </div>
          <div>
            <label className="label">Pet *</label>
            {userPets.length > 0 ? (
              <select
                name="pet_id"
                value={formData.pet_id}
                onChange={handleChange}
                required
                className="input-field"
              >
                <option value="">Select pet...</option>
                {userPets.map(pet => (
                  <option key={pet.pet_id} value={pet.pet_id}>
                    {pet.pet_name} ({pet.species})
                  </option>
                ))}
              </select>
            ) : (
              <div className="text-sm text-gray-500 p-2 bg-gray-50 rounded">
                No pets found. Please add a pet first.
              </div>
            )}
          </div>
        </div>

        {/* Dropzone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-gray-400'
          } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
        >
          <input
            type="file"
            id="file-upload"
            multiple
            accept=".pdf,.jpg,.jpeg,.png,.heic,.doc,.docx,.zip"
            onChange={handleFileChange}
            className="hidden"
            disabled={uploading}
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            {dragActive ? (
              <p className="text-primary-600 font-medium">Drop files here...</p>
            ) : (
              <>
                <p className="text-gray-600 font-medium">
                  Drag & drop documents here
                </p>
                <p className="text-gray-400 text-sm mt-1">
                  or click to browse (PDF, Images, Word, ZIP)
                </p>
                <p className="text-gray-400 text-xs mt-2">
                  Vet invoices, lab results, prescriptions, receipts
                </p>
              </>
            )}
          </label>
        </div>

        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            <h4 className="font-medium text-gray-700">
              Selected Files ({selectedFiles.length})
            </h4>
            <ul className="space-y-2 max-h-48 overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <li
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getFileIcon(file.name)}
                    <span className="text-sm text-gray-700">{file.name}</span>
                    <span className="text-xs text-gray-400">
                      ({formatFileSize(file.size)})
                    </span>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-gray-400 hover:text-red-500"
                    disabled={uploading}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Upload Button */}
        {selectedFiles.length > 0 && (
          <div className="mt-4">
            <button
              onClick={handleUpload}
              disabled={uploading || !formData.policy_id || !formData.pet_id}
              className={`btn-primary w-full md:w-auto flex items-center justify-center gap-2 ${
                (uploading || !formData.policy_id || !formData.pet_id)
                  ? 'opacity-50 cursor-not-allowed'
                  : ''
              }`}
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Upload & Process {selectedFiles.length} File{selectedFiles.length > 1 ? 's' : ''}
                </>
              )}
            </button>
            <p className="text-xs text-gray-500 mt-2">
              {serviceStatus === 'unavailable'
                ? 'Documents will be queued and processed when AI service is available.'
                : 'Your documents will be processed by AI. You\'ll be notified when complete.'}
            </p>
          </div>
        )}
      </div>

      {/* Upload History */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Your Uploads</h2>
          <button
            onClick={loadUploads}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            Refresh
          </button>
        </div>

        {loadingUploads ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : uploads.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No uploads yet</p>
            <p className="text-gray-400 text-sm mt-1">
              Upload documents above to get started
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {uploads.map((upload) => (
              <div
                key={upload.upload_id}
                className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900">
                        {upload.filenames?.join(', ') || 'Document'}
                      </span>
                      {getStatusBadge(upload.status)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {upload.pet_name && <span>Pet: {upload.pet_name} • </span>}
                      {new Date(upload.created_at).toLocaleString()}
                    </div>

                    {/* Status Details */}
                    {upload.status === 'processing' && (
                      <div className="mt-2 text-sm text-blue-600 flex items-center gap-1">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        AI agent is analyzing your documents...
                      </div>
                    )}

                    {upload.status === 'completed' && upload.claim_number && (
                      <div className="mt-2 p-2 bg-green-50 rounded text-sm">
                        <CheckCircle className="inline w-4 h-4 text-green-500 mr-1" />
                        <span className="text-green-700">
                          {upload.user_message || (
                            <>
                              Claim created: <strong>{upload.claim_number}</strong>
                              {upload.ai_decision && (
                                <span className="ml-2 text-green-600">
                                  Decision: {upload.ai_decision}
                                </span>
                              )}
                            </>
                          )}
                        </span>
                      </div>
                    )}

                    {upload.status === 'completed' && !upload.claim_number && upload.ai_decision && (
                      <div className="mt-2 p-2 bg-yellow-50 rounded text-sm">
                        <AlertCircle className="inline w-4 h-4 text-yellow-500 mr-1" />
                        <span className="text-yellow-700">
                          {upload.user_message || `Decision: ${upload.ai_decision}`}
                        </span>
                      </div>
                    )}

                    {upload.status === 'failed' && (
                      <div className="mt-2 p-2 bg-amber-50 rounded text-sm">
                        <Clock className="inline w-4 h-4 text-amber-500 mr-1" />
                        <span className="text-amber-700">
                          {upload.user_message || "Your claim is being reviewed by our team. We'll notify you once processing is complete."}
                        </span>
                      </div>
                    )}

                    {upload.status === 'queued' && (
                      <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
                        <Clock className="inline w-4 h-4 text-blue-500 mr-1" />
                        <span className="text-blue-700">
                          {upload.user_message || "Your documents have been saved and will be processed shortly."}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
