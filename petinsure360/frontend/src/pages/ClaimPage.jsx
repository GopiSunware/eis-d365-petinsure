import { useState, useEffect } from 'react'
import { AlertCircle, CheckCircle, Clock, FileText, DollarSign, Zap, ListChecks } from 'lucide-react'
import api from '../services/api'

const CLAIM_TYPES = ['Accident', 'Illness', 'Wellness', 'Dental', 'Behavioral']
const CLAIM_CATEGORIES = {
  Accident: ['Toxicity/Poisoning', 'Orthopedic Surgery', 'Gastrointestinal', 'Allergic/Immunologic', 'Trauma/Emergency', 'Emergency/Critical', 'Ophthalmology', 'Broken Bone', 'Laceration', 'Bite Wound', 'Foreign Body', 'Other'],
  Illness: ['Endocrine/Metabolic', 'Dermatology', 'Orthopedic', 'Oncology', 'Neurology', 'Gastrointestinal', 'Urinary', 'Renal/Urinary', 'Reproductive/Emergency', 'Parasitic/Infectious', 'Digestive', 'Respiratory', 'Skin/Allergy', 'Infection', 'Cancer', 'Chronic', 'Other'],
  Wellness: ['Preventive Care', 'Annual Exam', 'Vaccination', 'Flea/Tick Prevention', 'Heartworm Test', 'Other'],
  Dental: ['Dental', 'Cleaning', 'Extraction', 'Root Canal', 'Other'],
  Behavioral: ['Training', 'Anxiety Treatment', 'Aggression Therapy', 'Other']
}

export default function ClaimPage({ user }) {
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState(null)
  const [simulatingProcessing, setSimulatingProcessing] = useState(false)
  const [userPets, setUserPets] = useState([])
  const [userPolicies, setUserPolicies] = useState([])

  // Scenario selector state
  const [scenarios, setScenarios] = useState([])
  const [selectedScenario, setSelectedScenario] = useState('')
  const [loadingScenarios, setLoadingScenarios] = useState(false)

  const [formData, setFormData] = useState({
    policy_id: '',
    pet_id: '',
    customer_id: '',
    provider_id: '',
    provider_name: '',
    claim_type: 'Illness',
    claim_category: '',
    service_date: '',
    claim_amount: '',
    diagnosis_code: '',
    diagnosis: '',
    treatment_notes: '',
    invoice_number: '',
    is_emergency: false,
    is_in_network: true,
    line_items: []
  })

  // Fetch scenarios on mount
  useEffect(() => {
    const fetchScenarios = async () => {
      setLoadingScenarios(true)
      try {
        const response = await api.get('/scenarios/')
        setScenarios(response.data.scenarios || [])
      } catch (err) {
        console.error('Error fetching scenarios:', err)
      } finally {
        setLoadingScenarios(false)
      }
    }
    fetchScenarios()
  }, [])

  useEffect(() => {
    // Use logged-in user's customer_id if available
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

        // Auto-select first pet that has a policy
        if (pets.length > 0 && policies.length > 0) {
          // Find first pet that has a policy
          const petWithPolicy = pets.find(pet =>
            policies.some(p => p.pet_id === pet.pet_id)
          )
          if (petWithPolicy) {
            const petPolicy = policies.find(p => p.pet_id === petWithPolicy.pet_id)
            setFormData(prev => ({
              ...prev,
              pet_id: petWithPolicy.pet_id,
              policy_id: petPolicy?.policy_id || ''
            }))
          } else {
            // No pet has policy, just select first pet
            setFormData(prev => ({ ...prev, pet_id: pets[0].pet_id, policy_id: '' }))
          }
        } else if (pets.length > 0) {
          setFormData(prev => ({ ...prev, pet_id: pets[0].pet_id }))
        }
      }).catch(err => console.error('Error fetching user data:', err))
    } else {
      const savedCustomerId = localStorage.getItem('customer_id')
      const savedPetId = localStorage.getItem('pet_id')
      const savedPolicyId = localStorage.getItem('policy_id')
      setFormData(prev => ({
        ...prev,
        customer_id: savedCustomerId || '',
        pet_id: savedPetId || '',
        policy_id: savedPolicyId || ''
      }))
    }
  }, [user])

  // Filter policies based on selected pet
  const filteredPolicies = userPolicies.filter(p => p.pet_id === formData.pet_id)

  // Check if selected pet has a policy
  const selectedPetHasPolicy = filteredPolicies.length > 0

  // Handle scenario selection
  const handleScenarioSelect = (scenarioId) => {
    setSelectedScenario(scenarioId)

    if (!scenarioId) {
      // Reset form when "Select scenario..." is chosen
      setFormData(prev => ({
        ...prev,
        claim_type: 'Illness',
        claim_category: '',
        service_date: '',
        claim_amount: '',
        diagnosis_code: '',
        diagnosis: '',
        treatment_notes: '',
        provider_id: '',
        provider_name: '',
        is_emergency: false,
        is_in_network: true,
        line_items: []
      }))
      return
    }

    const scenario = scenarios.find(s => s.id === scenarioId)
    if (scenario) {
      // Calculate total from line items
      const totalAmount = scenario.line_items?.reduce((sum, item) => sum + (item.amount || 0), 0) || scenario.claim_amount

      setFormData(prev => ({
        ...prev,
        claim_type: scenario.claim_type || 'Illness',
        claim_category: scenario.claim_category || '',
        service_date: scenario.service_date || new Date().toISOString().split('T')[0],
        claim_amount: totalAmount.toString(),
        diagnosis_code: scenario.diagnosis_code || '',
        diagnosis: scenario.diagnosis || '',
        treatment_notes: scenario.treatment_notes || '',
        provider_id: scenario.provider_id || '',
        provider_name: scenario.provider_name || '',
        is_emergency: scenario.is_emergency || false,
        is_in_network: scenario.is_in_network !== false,
        line_items: scenario.line_items || []
      }))
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target

    // When pet changes, auto-select first policy for that pet (if any)
    if (name === 'pet_id') {
      const policiesForPet = userPolicies.filter(p => p.pet_id === value)
      setFormData(prev => ({
        ...prev,
        pet_id: value,
        policy_id: policiesForPet.length > 0 ? policiesForPet[0].policy_id : ''
      }))
      return
    }

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Prevent double submission
    if (loading) {
      console.log('Submission already in progress, ignoring duplicate click')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Use the new pipeline submit-claim endpoint for Bronze layer ingestion
      const submitData = {
        scenario_id: selectedScenario || null,
        customer_id: formData.customer_id,
        pet_id: formData.pet_id,
        policy_id: formData.policy_id || null,
        claim_type: formData.claim_type,
        claim_category: formData.claim_category,
        diagnosis_code: formData.diagnosis_code || null,
        diagnosis: formData.diagnosis || formData.treatment_notes.split('.')[0] || 'General treatment',
        service_date: formData.service_date,
        treatment_notes: formData.treatment_notes,
        line_items: formData.line_items.length > 0 ? formData.line_items : [
          { description: formData.claim_category || 'Medical Service', amount: parseFloat(formData.claim_amount) }
        ],
        claim_amount: parseFloat(formData.claim_amount),
        provider_id: formData.provider_id || null,
        provider_name: formData.provider_name || 'PetCare Veterinary Clinic',
        is_in_network: formData.is_in_network,
        is_emergency: formData.is_emergency
      }

      // Submit to Bronze layer via pipeline API
      const response = await api.post('/pipeline/submit-claim', submitData)
      setSuccess(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit claim. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const simulateProcessing = async () => {
    if (!success) return
    setSimulatingProcessing(true)
    try {
      await api.post(`/claims/${success.claim_id}/simulate-processing`)
    } catch (err) {
      console.error('Simulation error:', err)
    } finally {
      setSimulatingProcessing(false)
    }
  }

  if (success) {
    return (
      <div className="max-w-md mx-auto">
        <div className="card text-center">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-green-100 text-green-600 mb-4">
            <CheckCircle className="h-8 w-8" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Claim Submitted!</h2>
          <p className="text-gray-600 mb-4">
            Your claim has been received and is in the <strong>Bronze Layer</strong> (raw ingestion).
          </p>
          <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
            <p className="text-sm"><strong>Claim Number:</strong> {success.claim_number}</p>
            <p className="text-sm"><strong>Claim ID:</strong> {success.claim_id}</p>
            <p className="text-sm"><strong>Layer:</strong> <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">Bronze</span></p>
            <p className="text-sm mt-2 text-gray-600">
              {success.message}
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              <Clock className="inline h-4 w-4 mr-1" />
              Check the <strong>BI Dashboard → Pipeline</strong> to see this claim and trigger processing to Silver and Gold layers.
            </p>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => {
                setSuccess(null)
                setSelectedScenario('')
                setFormData(prev => ({
                  ...prev,
                  claim_type: 'Illness',
                  claim_category: '',
                  service_date: '',
                  claim_amount: '',
                  diagnosis_code: '',
                  diagnosis: '',
                  treatment_notes: '',
                  provider_id: '',
                  provider_name: '',
                  invoice_number: '',
                  is_emergency: false,
                  is_in_network: true,
                  line_items: []
                }))
              }}
              className="btn-primary w-full"
            >
              Submit Another Claim
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <div className="h-10 w-10 rounded-full bg-red-100 text-red-600 flex items-center justify-center">
            <AlertCircle className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Submit a Claim</h1>
            <p className="text-gray-600">File an insurance claim for your pet's care</p>
          </div>
        </div>

        {/* Scenario Selector - Demo Feature */}
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="h-5 w-5 text-purple-600" />
            <h3 className="font-semibold text-purple-900">Quick Fill (Demo)</h3>
          </div>
          <p className="text-sm text-purple-700 mb-3">
            Select a pre-defined scenario to auto-populate the form with realistic claim data.
          </p>
          <select
            value={selectedScenario}
            onChange={(e) => handleScenarioSelect(e.target.value)}
            className="w-full px-3 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white"
            disabled={loadingScenarios}
          >
            <option value="">Select a scenario...</option>
            {/* Fraud Scenarios */}
            {scenarios.filter(s => s.category === 'fraud').length > 0 && (
              <optgroup label="🚨 FRAUD DETECTION SCENARIOS">
                {scenarios.filter(s => s.category === 'fraud').map(scenario => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name} - ${scenario.claim_amount?.toLocaleString() || 'N/A'}
                  </option>
                ))}
              </optgroup>
            )}
            {/* Validation Scenarios */}
            {scenarios.filter(s => s.category === 'validation').length > 0 && (
              <optgroup label="⚠️ VALIDATION SCENARIOS">
                {scenarios.filter(s => s.category === 'validation').map(scenario => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name} - ${scenario.claim_amount?.toLocaleString() || 'N/A'}
                  </option>
                ))}
              </optgroup>
            )}
            {/* Standard Scenarios */}
            <optgroup label="📋 Standard Claim Scenarios">
              {scenarios.filter(s => !s.category).map(scenario => (
                <option key={scenario.id} value={scenario.id}>
                  {scenario.name} - ${scenario.claim_amount?.toLocaleString() || 'N/A'} ({scenario.claim_type})
                </option>
              ))}
            </optgroup>
          </select>
          {selectedScenario && (() => {
            const scenario = scenarios.find(s => s.id === selectedScenario);
            return (
              <div className="mt-3 p-3 bg-white rounded border border-purple-200">
                <p className="text-sm text-gray-700 mb-2">
                  <strong>Scenario:</strong> {scenario?.description}
                </p>
                {(scenario?.category === 'fraud' || scenario?.category === 'validation') && (
                  <div className="flex gap-4 text-xs mt-2 pt-2 border-t">
                    <span className="text-green-700">
                      <strong>Rule-Based:</strong> {scenario?.expected_rule_result || 'APPROVED'}
                    </span>
                    <span className={scenario?.expected_ai_result === 'FLAGGED' || scenario?.expected_ai_result === 'FAIL' || scenario?.expected_ai_result === 'CRITICAL' ? 'text-red-700' : 'text-amber-700'}>
                      <strong>AI Detection:</strong> {scenario?.expected_ai_result || 'N/A'}
                    </span>
                  </div>
                )}
              </div>
            );
          })()}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Pet selection warning */}
          {formData.pet_id && !selectedPetHasPolicy && userPets.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              <span>
                <strong>No policy found for this pet.</strong> Please purchase a policy before submitting a claim,
                or select a different pet.
              </span>
            </div>
          )}

          {/* IDs - Pet first, then Policy (filtered by pet) */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">Pet * <span className="text-xs text-gray-500">(select first)</span></label>
              {userPets.length > 0 ? (
                <select
                  name="pet_id"
                  value={formData.pet_id}
                  onChange={handleChange}
                  required
                  className="input-field"
                >
                  <option value="">Select pet...</option>
                  {userPets.map(pet => {
                    const hasPolicyIcon = userPolicies.some(p => p.pet_id === pet.pet_id) ? ' ✓' : ' (no policy)'
                    return (
                      <option key={pet.pet_id} value={pet.pet_id}>
                        {pet.pet_name} ({pet.species}){hasPolicyIcon}
                      </option>
                    )
                  })}
                </select>
              ) : (
                <input
                  type="text"
                  name="pet_id"
                  value={formData.pet_id}
                  onChange={handleChange}
                  required
                  className="input-field"
                  placeholder="PET-XXXXXXXX"
                />
              )}
            </div>
            <div>
              <label className="label">Policy * <span className="text-xs text-gray-500">(for selected pet)</span></label>
              {filteredPolicies.length > 0 ? (
                <select
                  name="policy_id"
                  value={formData.policy_id}
                  onChange={handleChange}
                  required
                  className="input-field"
                >
                  <option value="">Select policy...</option>
                  {filteredPolicies.map(policy => (
                    <option key={policy.policy_id} value={policy.policy_id}>
                      {policy.policy_number || policy.policy_id} - {policy.plan_type || policy.plan_name}
                    </option>
                  ))}
                </select>
              ) : formData.pet_id && userPets.length > 0 ? (
                <div className="input-field bg-gray-100 text-gray-500 cursor-not-allowed">
                  No policy for this pet
                </div>
              ) : (
                <input
                  type="text"
                  name="policy_id"
                  value={formData.policy_id}
                  onChange={handleChange}
                  required
                  className="input-field"
                  placeholder="POL-XXXXXXXX"
                />
              )}
            </div>
            <div>
              <label className="label">Customer ID *</label>
              <input
                type="text"
                name="customer_id"
                value={formData.customer_id}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="CUST-XXXXXXXX"
                readOnly={!!user}
              />
            </div>
          </div>

          {/* Claim Type and Category */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Claim Type *</label>
              <select
                name="claim_type"
                value={formData.claim_type}
                onChange={handleChange}
                required
                className="input-field"
              >
                {CLAIM_TYPES.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Category *</label>
              <select
                name="claim_category"
                value={formData.claim_category}
                onChange={handleChange}
                required
                className="input-field"
              >
                <option value="">Select category...</option>
                {CLAIM_CATEGORIES[formData.claim_type]?.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Service Date and Amount */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Service Date *</label>
              <input
                type="date"
                name="service_date"
                value={formData.service_date}
                onChange={handleChange}
                required
                className="input-field"
              />
            </div>
            <div>
              <label className="label">
                <DollarSign className="inline h-4 w-4" />
                Claim Amount *
              </label>
              <input
                type="number"
                name="claim_amount"
                value={formData.claim_amount}
                onChange={handleChange}
                required
                min="1"
                step="0.01"
                className="input-field"
                placeholder="450.00"
              />
            </div>
          </div>

          {/* Provider */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Provider Name</label>
              <input
                type="text"
                name="provider_name"
                value={formData.provider_name}
                onChange={handleChange}
                className="input-field"
                placeholder="Veterinary clinic name"
              />
            </div>
            <div>
              <label className="label">Diagnosis Code</label>
              <input
                type="text"
                name="diagnosis_code"
                value={formData.diagnosis_code}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g., GI001, ORTH002"
              />
            </div>
          </div>

          {/* Diagnosis */}
          <div>
            <label className="label">Diagnosis</label>
            <input
              type="text"
              name="diagnosis"
              value={formData.diagnosis}
              onChange={handleChange}
              className="input-field"
              placeholder="e.g., Gastroenteritis, ACL Tear"
            />
          </div>

          {/* Treatment Notes */}
          <div>
            <label className="label">
              <FileText className="inline h-4 w-4 mr-1" />
              Treatment Notes
            </label>
            <textarea
              name="treatment_notes"
              value={formData.treatment_notes}
              onChange={handleChange}
              className="input-field"
              rows="3"
              placeholder="Describe the treatment received..."
            />
          </div>

          {/* Line Items Display (when scenario selected) */}
          {formData.line_items.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <ListChecks className="h-4 w-4 text-gray-600" />
                <label className="font-medium text-gray-700">Line Items</label>
              </div>
              <div className="space-y-2">
                {formData.line_items.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm bg-white p-2 rounded border">
                    <span className="text-gray-700">{item.description}</span>
                    <span className="font-medium">${item.amount?.toLocaleString()}</span>
                  </div>
                ))}
                <div className="flex justify-between text-sm font-bold pt-2 border-t">
                  <span>Total</span>
                  <span>${formData.line_items.reduce((sum, item) => sum + (item.amount || 0), 0).toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}

          {/* Checkboxes */}
          <div className="flex items-center gap-6">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                name="is_emergency"
                checked={formData.is_emergency}
                onChange={handleChange}
                className="h-4 w-4 text-red-600 rounded"
              />
              <label className="text-sm text-gray-700">
                Emergency visit
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                name="is_in_network"
                checked={formData.is_in_network}
                onChange={handleChange}
                className="h-4 w-4 text-green-600 rounded"
              />
              <label className="text-sm text-gray-700">
                In-network provider
              </label>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || (userPets.length > 0 && !selectedPetHasPolicy)}
            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Submitting Claim...' :
              (userPets.length > 0 && !selectedPetHasPolicy) ? 'Select a Pet with Policy' :
              'Submit Claim to Bronze Layer'}
          </button>
        </form>
      </div>
    </div>
  )
}
