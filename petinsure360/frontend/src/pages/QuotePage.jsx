import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronLeft, ChevronRight, Calculator, CheckCircle,
  PawPrint, Shield, DollarSign, Sparkles, AlertCircle,
  Loader2, ArrowRight
} from 'lucide-react'

// Rating Engine API (WS5) - Uses Claims Data API which has rating endpoints
const RATING_API_BASE = import.meta.env.VITE_RATING_URL || import.meta.env.VITE_API_URL || 'http://localhost:8005'

const STEPS = [
  { id: 'pet', title: 'Pet Information', icon: PawPrint },
  { id: 'coverage', title: 'Coverage Selection', icon: Shield },
  { id: 'quote', title: 'Your Quote', icon: DollarSign },
]

const SPECIES_OPTIONS = [
  { value: 'dog', label: 'Dog', icon: '🐕' },
  { value: 'cat', label: 'Cat', icon: '🐈' },
  { value: 'bird', label: 'Bird', icon: '🦜' },
  { value: 'rabbit', label: 'Rabbit', icon: '🐰' },
  { value: 'reptile', label: 'Reptile', icon: '🦎' },
]

export default function QuotePage({ user }) {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [coverageOptions, setCoverageOptions] = useState(null)
  const [breeds, setBreeds] = useState([])
  const [quote, setQuote] = useState(null)

  // Pet Information
  const [petData, setPetData] = useState({
    name: '',
    species: 'dog',
    breed: '',
    date_of_birth: '',
    gender: 'male',
    spayed_neutered: false,
    microchipped: false,
    weight_lbs: '',
    pre_existing_conditions: [],
  })

  // Coverage Selection
  const [coverage, setCoverage] = useState({
    plan_type: 'accident_illness',
    annual_limit: 10000,
    deductible: 250,
    reimbursement_pct: 80,
  })

  // Add-ons
  const [addOns, setAddOns] = useState({
    wellness: false,
    dental: false,
    behavioral: false,
  })

  // Discounts
  const [discounts, setDiscounts] = useState({
    multi_pet: false,
    annual_pay: false,
    shelter_rescue: false,
    military_veteran: false,
  })

  // Location
  const [location, setLocation] = useState({
    state: 'CA',
    zip_code: '90210',
  })

  // Fetch coverage options and breeds on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [coveragesRes, breedsRes] = await Promise.all([
          fetch(`${RATING_API_BASE}/api/v1/rating/coverages`),
          fetch(`${RATING_API_BASE}/api/v1/rating/breeds?species=${petData.species}`),
        ])

        if (coveragesRes.ok) {
          setCoverageOptions(await coveragesRes.json())
        }
        if (breedsRes.ok) {
          const data = await breedsRes.json()
          setBreeds(data.breeds || [])
        }
      } catch (err) {
        console.error('Failed to fetch options:', err)
      }
    }
    fetchData()
  }, [])

  // Fetch breeds when species changes
  useEffect(() => {
    const fetchBreeds = async () => {
      try {
        const res = await fetch(`${RATING_API_BASE}/api/v1/rating/breeds?species=${petData.species}`)
        if (res.ok) {
          const data = await res.json()
          setBreeds(data.breeds || [])
          // Reset breed when species changes
          setPetData(prev => ({ ...prev, breed: '' }))
        }
      } catch (err) {
        console.error('Failed to fetch breeds:', err)
      }
    }
    fetchBreeds()
  }, [petData.species])

  const handlePetChange = (e) => {
    const { name, value, type, checked } = e.target
    setPetData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleCoverageChange = (name, value) => {
    setCoverage(prev => ({ ...prev, [name]: value }))
  }

  const handleAddOnChange = (name) => {
    setAddOns(prev => ({ ...prev, [name]: !prev[name] }))
  }

  const handleDiscountChange = (name) => {
    setDiscounts(prev => ({ ...prev, [name]: !prev[name] }))
  }

  const calculateQuote = async () => {
    setLoading(true)
    setError(null)

    try {
      // Get today's date for effective date
      const today = new Date()
      const effectiveDate = today.toISOString().split('T')[0]

      const quoteRequest = {
        state: location.state,
        zip_code: location.zip_code,
        effective_date: effectiveDate,
        pet: {
          name: petData.name,
          species: petData.species,
          breed: petData.breed,
          date_of_birth: petData.date_of_birth,
          gender: petData.gender,
          spayed_neutered: petData.spayed_neutered,
          microchipped: petData.microchipped,
          weight_lbs: petData.weight_lbs ? parseFloat(petData.weight_lbs) : null,
          pre_existing_conditions: petData.pre_existing_conditions,
        },
        coverage: {
          plan_type: coverage.plan_type,
          annual_limit: coverage.annual_limit,
          deductible: coverage.deductible,
          reimbursement_pct: coverage.reimbursement_pct,
        },
        add_ons: addOns,
        discounts: discounts,
      }

      const response = await fetch(`${RATING_API_BASE}/api/v1/rating/quote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(quoteRequest),
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Failed to calculate quote')
      }

      const quoteResult = await response.json()
      setQuote(quoteResult)
      setCurrentStep(2) // Move to quote step
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const nextStep = () => {
    if (currentStep === 1) {
      // Calculate quote when moving from coverage to quote
      calculateQuote()
    } else if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const canProceed = () => {
    if (currentStep === 0) {
      return petData.name && petData.breed && petData.date_of_birth
    }
    if (currentStep === 1) {
      return coverage.plan_type && coverage.deductible
    }
    return true
  }

  const proceedToPurchase = () => {
    // Store quote info and navigate to policy page
    localStorage.setItem('pending_quote', JSON.stringify(quote))
    navigate('/policy')
  }

  // Step 1: Pet Information
  const renderPetStep = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold mb-4">Tell us about your pet</h2>
        <p className="text-gray-600 mb-6">We'll use this information to calculate a personalized quote.</p>
      </div>

      {/* Species Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">What type of pet?</label>
        <div className="grid grid-cols-5 gap-3">
          {SPECIES_OPTIONS.map(species => (
            <button
              key={species.value}
              type="button"
              onClick={() => setPetData(prev => ({ ...prev, species: species.value }))}
              className={`flex flex-col items-center p-4 rounded-lg border-2 transition-all ${
                petData.species === species.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              <span className="text-2xl mb-1">{species.icon}</span>
              <span className="text-sm font-medium">{species.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Pet Name and Breed */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Pet Name *</label>
          <input
            type="text"
            name="name"
            value={petData.name}
            onChange={handlePetChange}
            placeholder="e.g., Max"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Breed *</label>
          <select
            name="breed"
            value={petData.breed}
            onChange={handlePetChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select breed...</option>
            {breeds.length > 0 ? (
              breeds.map(breed => (
                <option key={breed.breed_code} value={breed.breed_name}>
                  {breed.breed_name}
                </option>
              ))
            ) : (
              // Fallback breeds if API fails
              <>
                {petData.species === 'dog' && (
                  <>
                    <option value="Labrador Retriever">Labrador Retriever</option>
                    <option value="German Shepherd">German Shepherd</option>
                    <option value="Golden Retriever">Golden Retriever</option>
                    <option value="French Bulldog">French Bulldog</option>
                    <option value="Mixed Breed">Mixed Breed</option>
                  </>
                )}
                {petData.species === 'cat' && (
                  <>
                    <option value="Domestic Shorthair">Domestic Shorthair</option>
                    <option value="Siamese">Siamese</option>
                    <option value="Persian">Persian</option>
                    <option value="Maine Coon">Maine Coon</option>
                    <option value="Mixed Breed">Mixed Breed</option>
                  </>
                )}
              </>
            )}
          </select>
        </div>
      </div>

      {/* Date of Birth and Gender */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth *</label>
          <input
            type="date"
            name="date_of_birth"
            value={petData.date_of_birth}
            onChange={handlePetChange}
            max={new Date().toISOString().split('T')[0]}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
          <select
            name="gender"
            value={petData.gender}
            onChange={handlePetChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </div>
      </div>

      {/* Weight */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Weight (lbs)</label>
        <input
          type="number"
          name="weight_lbs"
          value={petData.weight_lbs}
          onChange={handlePetChange}
          placeholder="e.g., 45"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Checkboxes for discounts */}
      <div className="space-y-3">
        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            name="spayed_neutered"
            checked={petData.spayed_neutered}
            onChange={handlePetChange}
            className="h-4 w-4 text-blue-600 rounded"
          />
          <span className="text-sm">Spayed/Neutered <span className="text-green-600">(5% discount)</span></span>
        </label>
        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            name="microchipped"
            checked={petData.microchipped}
            onChange={handlePetChange}
            className="h-4 w-4 text-blue-600 rounded"
          />
          <span className="text-sm">Microchipped <span className="text-green-600">(3% discount)</span></span>
        </label>
      </div>

      {/* Location */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
          <select
            value={location.state}
            onChange={(e) => setLocation(prev => ({ ...prev, state: e.target.value }))}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="CA">California</option>
            <option value="NY">New York</option>
            <option value="TX">Texas</option>
            <option value="FL">Florida</option>
            <option value="WA">Washington</option>
            <option value="CO">Colorado</option>
            <option value="IL">Illinois</option>
            <option value="PA">Pennsylvania</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">ZIP Code</label>
          <input
            type="text"
            value={location.zip_code}
            onChange={(e) => setLocation(prev => ({ ...prev, zip_code: e.target.value }))}
            placeholder="e.g., 90210"
            maxLength={5}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
    </div>
  )

  // Step 2: Coverage Selection
  const renderCoverageStep = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold mb-4">Customize your coverage</h2>
        <p className="text-gray-600 mb-6">Choose the protection level that works for you.</p>
      </div>

      {/* Plan Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">Coverage Type</label>
        <div className="grid grid-cols-3 gap-4">
          {coverageOptions?.plan_types?.map(plan => (
            <button
              key={plan.type}
              type="button"
              onClick={() => handleCoverageChange('plan_type', plan.type)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                coverage.plan_type === plan.type
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              <div className="font-semibold">{plan.name}</div>
              <div className="text-xs text-gray-500 mt-1">{plan.description}</div>
              <div className="text-sm font-medium text-blue-600 mt-2">{plan.price_range}</div>
            </button>
          )) || (
            <>
              <button
                type="button"
                onClick={() => handleCoverageChange('plan_type', 'accident_only')}
                className={`p-4 rounded-lg border-2 text-left ${
                  coverage.plan_type === 'accident_only' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="font-semibold">Accident Only</div>
                <div className="text-xs text-gray-500 mt-1">Covers injuries from accidents</div>
              </button>
              <button
                type="button"
                onClick={() => handleCoverageChange('plan_type', 'accident_illness')}
                className={`p-4 rounded-lg border-2 text-left ${
                  coverage.plan_type === 'accident_illness' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="font-semibold">Accident + Illness</div>
                <div className="text-xs text-gray-500 mt-1">Most popular option</div>
              </button>
              <button
                type="button"
                onClick={() => handleCoverageChange('plan_type', 'comprehensive')}
                className={`p-4 rounded-lg border-2 text-left ${
                  coverage.plan_type === 'comprehensive' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="font-semibold">Comprehensive</div>
                <div className="text-xs text-gray-500 mt-1">Full coverage + wellness</div>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Annual Limit */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">Annual Limit</label>
        <div className="grid grid-cols-4 gap-3">
          {(coverageOptions?.annual_limits || [
            { value: 5000, label: '$5,000/year' },
            { value: 10000, label: '$10,000/year' },
            { value: 15000, label: '$15,000/year' },
            { value: 0, label: 'Unlimited' },
          ]).map(opt => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleCoverageChange('annual_limit', opt.value)}
              className={`p-3 rounded-lg border-2 text-sm font-medium transition-all ${
                coverage.annual_limit === opt.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Deductible */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">Annual Deductible</label>
        <div className="grid grid-cols-4 gap-3">
          {(coverageOptions?.deductibles || [
            { value: 100, label: '$100' },
            { value: 250, label: '$250' },
            { value: 500, label: '$500' },
            { value: 750, label: '$750' },
          ]).map(opt => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleCoverageChange('deductible', opt.value)}
              className={`p-3 rounded-lg border-2 text-sm font-medium transition-all ${
                coverage.deductible === opt.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Reimbursement Rate */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">Reimbursement Rate</label>
        <div className="grid grid-cols-3 gap-3">
          {(coverageOptions?.reimbursement_rates || [
            { value: 70, label: '70%' },
            { value: 80, label: '80%' },
            { value: 90, label: '90%' },
          ]).map(opt => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleCoverageChange('reimbursement_pct', opt.value)}
              className={`p-3 rounded-lg border-2 text-sm font-medium transition-all ${
                coverage.reimbursement_pct === opt.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Add-ons */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">Optional Add-ons</label>
        <div className="space-y-3">
          {(coverageOptions?.add_ons || [
            { type: 'wellness', name: 'Wellness Add-On', description: 'Vaccines, checkups, dental cleaning', monthly_cost: 15 },
            { type: 'dental', name: 'Dental Add-On', description: 'Dental illness, extractions', monthly_cost: 8 },
            { type: 'behavioral', name: 'Behavioral Add-On', description: 'Behavioral therapy, anxiety training', monthly_cost: 5 },
          ]).map(addon => (
            <label
              key={addon.type}
              className={`flex items-center justify-between p-4 rounded-lg border-2 cursor-pointer transition-all ${
                addOns[addon.type]
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={addOns[addon.type]}
                  onChange={() => handleAddOnChange(addon.type)}
                  className="h-4 w-4 text-blue-600 rounded"
                />
                <div>
                  <div className="font-medium">{addon.name}</div>
                  <div className="text-xs text-gray-500">{addon.description}</div>
                </div>
              </div>
              <span className="text-sm font-medium text-gray-700">+${addon.monthly_cost}/mo</span>
            </label>
          ))}
        </div>
      </div>

      {/* Discounts */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">Available Discounts</label>
        <div className="grid grid-cols-2 gap-3">
          <label className="flex items-center space-x-3 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={discounts.multi_pet}
              onChange={() => handleDiscountChange('multi_pet')}
              className="h-4 w-4 text-blue-600 rounded"
            />
            <span className="text-sm">Multi-pet discount (5%)</span>
          </label>
          <label className="flex items-center space-x-3 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={discounts.annual_pay}
              onChange={() => handleDiscountChange('annual_pay')}
              className="h-4 w-4 text-blue-600 rounded"
            />
            <span className="text-sm">Annual payment (10%)</span>
          </label>
          <label className="flex items-center space-x-3 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={discounts.shelter_rescue}
              onChange={() => handleDiscountChange('shelter_rescue')}
              className="h-4 w-4 text-blue-600 rounded"
            />
            <span className="text-sm">Shelter/Rescue pet (5%)</span>
          </label>
          <label className="flex items-center space-x-3 p-3 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={discounts.military_veteran}
              onChange={() => handleDiscountChange('military_veteran')}
              className="h-4 w-4 text-blue-600 rounded"
            />
            <span className="text-sm">Military/Veteran (5%)</span>
          </label>
        </div>
      </div>
    </div>
  )

  // Step 3: Quote Result
  const renderQuoteStep = () => {
    if (!quote) return null

    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-green-100 text-green-600 mb-4">
            <Sparkles className="h-8 w-8" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Your Personalized Quote</h2>
          <p className="text-gray-600">Coverage for {quote.pet?.name || petData.name}</p>
        </div>

        {/* Main Quote Card */}
        <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">Monthly Premium</p>
              <p className="text-4xl font-bold">${parseFloat(quote.monthly_premium).toFixed(2)}</p>
            </div>
            <div className="text-right">
              <p className="text-blue-100 text-sm">Annual Premium</p>
              <p className="text-xl font-semibold">
                ${parseFloat(quote.premium_breakdown?.total_annual_premium || 0).toFixed(2)}/year
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-blue-500 text-sm">
            <p>Quote ID: {quote.quote_id}</p>
            <p>Valid until: {quote.valid_until}</p>
          </div>
        </div>

        {/* Coverage Details */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h3 className="font-semibold">Coverage Details</h3>
          </div>
          <div className="p-6 space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-600">Plan Type</span>
              <span className="font-medium capitalize">{coverage.plan_type.replace('_', ' + ')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Annual Limit</span>
              <span className="font-medium">
                {coverage.annual_limit === 0 ? 'Unlimited' : `$${coverage.annual_limit.toLocaleString()}`}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Deductible</span>
              <span className="font-medium">${coverage.deductible}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Reimbursement</span>
              <span className="font-medium">{coverage.reimbursement_pct}%</span>
            </div>
          </div>
        </div>

        {/* Premium Breakdown */}
        {quote.premium_breakdown && (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b">
              <h3 className="font-semibold">Premium Breakdown</h3>
            </div>
            <div className="p-6 space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Base Rate</span>
                <span>${parseFloat(quote.premium_breakdown.base_rate).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Breed Factor</span>
                <span>x{parseFloat(quote.premium_breakdown.combined_breed_factor).toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Age Factor</span>
                <span>x{parseFloat(quote.premium_breakdown.age_factor).toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Location Factor</span>
                <span>x{parseFloat(quote.premium_breakdown.location_factor).toFixed(3)}</span>
              </div>
              {quote.premium_breakdown.add_on_charges?.length > 0 && (
                <div className="pt-2 border-t">
                  {quote.premium_breakdown.add_on_charges.map((addon, i) => (
                    <div key={i} className="flex justify-between text-blue-600">
                      <span>{addon.type} add-on</span>
                      <span>+${parseFloat(addon.annual_cost || addon.premium).toFixed(2)}/yr</span>
                    </div>
                  ))}
                </div>
              )}
              {quote.premium_breakdown.total_discounts > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Total Discounts</span>
                  <span>-${parseFloat(quote.premium_breakdown.total_discounts).toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between pt-2 border-t font-semibold">
                <span>Total Annual Premium</span>
                <span>${parseFloat(quote.premium_breakdown.total_annual_premium).toFixed(2)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-4">
          <button
            onClick={() => setCurrentStep(1)}
            className="flex-1 px-6 py-3 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            Modify Coverage
          </button>
          <button
            onClick={proceedToPurchase}
            className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            <span>Proceed to Purchase</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => {
            const Icon = step.icon
            const isActive = index === currentStep
            const isComplete = index < currentStep

            return (
              <div key={step.id} className="flex items-center">
                <div
                  className={`flex items-center justify-center h-10 w-10 rounded-full border-2 transition-all ${
                    isActive
                      ? 'border-blue-600 bg-blue-600 text-white'
                      : isComplete
                      ? 'border-green-500 bg-green-500 text-white'
                      : 'border-gray-300 text-gray-400'
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                <span
                  className={`ml-2 text-sm font-medium ${
                    isActive ? 'text-blue-600' : isComplete ? 'text-green-600' : 'text-gray-400'
                  }`}
                >
                  {step.title}
                </span>
                {index < STEPS.length - 1 && (
                  <div className={`h-0.5 w-16 mx-4 ${isComplete ? 'bg-green-500' : 'bg-gray-200'}`} />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* Step Content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        {currentStep === 0 && renderPetStep()}
        {currentStep === 1 && renderCoverageStep()}
        {currentStep === 2 && renderQuoteStep()}

        {/* Navigation Buttons */}
        {currentStep < 2 && (
          <div className="flex justify-between mt-8 pt-6 border-t">
            <button
              onClick={prevStep}
              disabled={currentStep === 0}
              className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
              <span>Back</span>
            </button>
            <button
              onClick={nextStep}
              disabled={!canProceed() || loading}
              className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Calculating...</span>
                </>
              ) : currentStep === 1 ? (
                <>
                  <Calculator className="h-4 w-4" />
                  <span>Get Quote</span>
                </>
              ) : (
                <>
                  <span>Continue</span>
                  <ChevronRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
