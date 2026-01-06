import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, CheckCircle, Shield, Star } from 'lucide-react'
import api from '../services/api'

const PLANS = [
  {
    name: 'Basic',
    monthly: 29.99,
    deductible: 500,
    coverage: 5000,
    reimbursement: 70,
    waiting: 14,
    features: ['Accident coverage', 'Illness coverage', '70% reimbursement']
  },
  {
    name: 'Standard',
    monthly: 49.99,
    deductible: 250,
    coverage: 10000,
    reimbursement: 80,
    waiting: 14,
    features: ['Accident coverage', 'Illness coverage', '80% reimbursement', 'Lower deductible']
  },
  {
    name: 'Premium',
    monthly: 79.99,
    deductible: 100,
    coverage: 20000,
    reimbursement: 90,
    waiting: 7,
    popular: true,
    features: ['Accident coverage', 'Illness coverage', '90% reimbursement', 'Minimal deductible', 'Faster waiting period']
  },
  {
    name: 'Unlimited',
    monthly: 99.99,
    deductible: 0,
    coverage: 999999,
    reimbursement: 100,
    waiting: 0,
    features: ['Accident coverage', 'Illness coverage', '100% reimbursement', 'No deductible', 'No waiting period', 'Unlimited coverage']
  }
]

export default function PolicyPage({ user }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState(null)
  const [selectedPlan, setSelectedPlan] = useState('Premium')
  const [userPets, setUserPets] = useState([])

  const [formData, setFormData] = useState({
    customer_id: '',
    pet_id: '',
    plan_name: 'Premium',
    payment_method: 'Credit Card',
    payment_frequency: 'Monthly',
    includes_wellness: false,
    includes_dental: false,
    includes_behavioral: false
  })

  useEffect(() => {
    // Use logged-in user's customer_id if available
    if (user?.customer_id) {
      setFormData(prev => ({ ...prev, customer_id: user.customer_id }))
      // Fetch user's pets for dropdown
      api.get(`/pets/customer/${user.customer_id}`)
        .then(res => {
          setUserPets(res.data.pets || [])
          // Auto-select first pet if available
          if (res.data.pets?.length > 0) {
            setFormData(prev => ({ ...prev, pet_id: res.data.pets[0].pet_id }))
          }
        })
        .catch(err => console.error('Error fetching pets:', err))
    } else {
      const savedCustomerId = localStorage.getItem('customer_id')
      const savedPetId = localStorage.getItem('pet_id')
      if (savedCustomerId) {
        setFormData(prev => ({ ...prev, customer_id: savedCustomerId }))
      }
      if (savedPetId) {
        setFormData(prev => ({ ...prev, pet_id: savedPetId }))
      }
    }
  }, [user])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handlePlanSelect = (planName) => {
    setSelectedPlan(planName)
    setFormData(prev => ({ ...prev, plan_name: planName }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await api.post('/policies/', formData)
      setSuccess(response.data)
      localStorage.setItem('policy_id', response.data.policy_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create policy. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="max-w-md mx-auto">
        <div className="card text-center">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-green-100 text-green-600 mb-4">
            <CheckCircle className="h-8 w-8" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Policy Created!</h2>
          <p className="text-gray-600 mb-2">
            Your {success.plan_name} plan is now active!
          </p>
          <p className="text-sm text-gray-500 mb-4">
            Policy Number: <span className="font-mono font-bold">{success.policy_number}</span>
          </p>
          <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
            <p className="text-sm"><strong>Monthly Premium:</strong> ${success.monthly_premium}</p>
            <p className="text-sm"><strong>Coverage Limit:</strong> ${success.coverage_limit.toLocaleString()}</p>
            <p className="text-sm"><strong>Effective Date:</strong> {success.effective_date}</p>
            <p className="text-sm"><strong>Expiration Date:</strong> {success.expiration_date}</p>
          </div>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/claim')}
              className="btn-primary w-full"
            >
              Submit a Claim
            </button>
            <button
              onClick={() => navigate('/')}
              className="btn-secondary w-full"
            >
              Return Home
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Choose Your Plan</h1>
        <p className="text-gray-600">Select the coverage that's right for your pet</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 max-w-2xl mx-auto">
          {error}
        </div>
      )}

      {/* Plan Cards */}
      <div className="grid md:grid-cols-4 gap-4 mb-8">
        {PLANS.map(plan => (
          <div
            key={plan.name}
            onClick={() => handlePlanSelect(plan.name)}
            className={`card cursor-pointer transition-all ${
              selectedPlan === plan.name
                ? 'ring-2 ring-primary-500 border-primary-500'
                : 'hover:shadow-lg'
            } ${plan.popular ? 'border-pet-orange' : ''}`}
          >
            {plan.popular && (
              <div className="flex items-center space-x-1 text-pet-orange text-sm font-semibold mb-2">
                <Star className="h-4 w-4 fill-current" />
                <span>Most Popular</span>
              </div>
            )}
            <h3 className="text-xl font-bold">{plan.name}</h3>
            <div className="my-4">
              <span className="text-3xl font-bold text-primary-600">${plan.monthly}</span>
              <span className="text-gray-500">/mo</span>
            </div>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>Up to ${plan.coverage === 999999 ? 'Unlimited' : plan.coverage.toLocaleString()} coverage</li>
              <li>{plan.reimbursement}% reimbursement</li>
              <li>${plan.deductible} deductible</li>
              <li>{plan.waiting} day waiting period</li>
            </ul>
            <div className="mt-4 pt-4 border-t">
              <ul className="space-y-1 text-xs text-gray-500">
                {plan.features.map(f => (
                  <li key={f} className="flex items-center space-x-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      {/* Purchase Form */}
      <div className="max-w-2xl mx-auto">
        <div className="card">
          <div className="flex items-center space-x-3 mb-6">
            <div className="h-10 w-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Complete Your Purchase</h2>
              <p className="text-gray-600">Selected: {selectedPlan} Plan</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* IDs */}
            <div className="grid grid-cols-2 gap-4">
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
                />
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
                    <option value="">Select a pet...</option>
                    {userPets.map(pet => (
                      <option key={pet.pet_id} value={pet.pet_id}>
                        {pet.pet_name} ({pet.species} - {pet.breed})
                      </option>
                    ))}
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
            </div>

            {/* Payment */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Payment Method</label>
                <select
                  name="payment_method"
                  value={formData.payment_method}
                  onChange={handleChange}
                  className="input-field"
                >
                  <option value="Credit Card">Credit Card</option>
                  <option value="Debit Card">Debit Card</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                </select>
              </div>
              <div>
                <label className="label">Payment Frequency</label>
                <select
                  name="payment_frequency"
                  value={formData.payment_frequency}
                  onChange={handleChange}
                  className="input-field"
                >
                  <option value="Monthly">Monthly</option>
                  <option value="Quarterly">Quarterly</option>
                  <option value="Annual">Annual (10% discount)</option>
                </select>
              </div>
            </div>

            {/* Add-ons */}
            <div>
              <label className="label mb-3">Optional Add-ons</label>
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    name="includes_wellness"
                    checked={formData.includes_wellness}
                    onChange={handleChange}
                    className="h-4 w-4 text-primary-600 rounded"
                  />
                  <span className="text-sm">Wellness Coverage (+$10/mo) - Routine checkups, vaccinations</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    name="includes_dental"
                    checked={formData.includes_dental}
                    onChange={handleChange}
                    className="h-4 w-4 text-primary-600 rounded"
                  />
                  <span className="text-sm">Dental Coverage (+$8/mo) - Cleanings, extractions</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    name="includes_behavioral"
                    checked={formData.includes_behavioral}
                    onChange={handleChange}
                    className="h-4 w-4 text-primary-600 rounded"
                  />
                  <span className="text-sm">Behavioral Coverage (+$5/mo) - Training, therapy</span>
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full disabled:opacity-50"
            >
              {loading ? 'Processing...' : `Purchase ${selectedPlan} Plan`}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
