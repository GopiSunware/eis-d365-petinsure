import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, Mail, Phone, MapPin, Calendar, CheckCircle } from 'lucide-react'
import api from '../services/api'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState(null)

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    address_line1: '',
    city: '',
    state: '',
    zip_code: '',
    date_of_birth: '',
    preferred_contact: 'Email',
    marketing_opt_in: false,
    referral_source: ''
  })

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await api.post('/customers/', formData)
      setSuccess(response.data)
      // Store customer ID for subsequent pages
      localStorage.setItem('customer_id', response.data.customer_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
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
          <h2 className="text-2xl font-bold mb-2">Registration Successful!</h2>
          <p className="text-gray-600 mb-4">
            Welcome to PetInsure360, {success.first_name}!
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Your Customer ID: <span className="font-mono font-bold">{success.customer_id}</span>
          </p>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/add-pet')}
              className="btn-primary w-full"
            >
              Add Your Pet
            </button>
            <button
              onClick={() => {
                setSuccess(null)
                setFormData({
                  first_name: '',
                  last_name: '',
                  email: '',
                  phone: '',
                  address_line1: '',
                  city: '',
                  state: '',
                  zip_code: '',
                  date_of_birth: '',
                  preferred_contact: 'Email',
                  marketing_opt_in: false,
                  referral_source: ''
                })
              }}
              className="btn-secondary w-full"
            >
              Register Another Customer
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
          <div className="h-10 w-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center">
            <User className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Register</h1>
            <p className="text-gray-600">Create your PetInsure360 account</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">First Name *</label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="John"
              />
            </div>
            <div>
              <label className="label">Last Name *</label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="Smith"
              />
            </div>
          </div>

          {/* Contact */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">
                <Mail className="inline h-4 w-4 mr-1" />
                Email *
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="john@example.com"
              />
            </div>
            <div>
              <label className="label">
                <Phone className="inline h-4 w-4 mr-1" />
                Phone * (10 digits)
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                required
                pattern="[0-9]{10}"
                className="input-field"
                placeholder="5551234567"
              />
            </div>
          </div>

          {/* Address */}
          <div>
            <label className="label">
              <MapPin className="inline h-4 w-4 mr-1" />
              Street Address *
            </label>
            <input
              type="text"
              name="address_line1"
              value={formData.address_line1}
              onChange={handleChange}
              required
              className="input-field"
              placeholder="123 Main Street"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">City *</label>
              <input
                type="text"
                name="city"
                value={formData.city}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="Austin"
              />
            </div>
            <div>
              <label className="label">State *</label>
              <select
                name="state"
                value={formData.state}
                onChange={handleChange}
                required
                className="input-field"
              >
                <option value="">Select</option>
                {['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'].map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">ZIP Code *</label>
              <input
                type="text"
                name="zip_code"
                value={formData.zip_code}
                onChange={handleChange}
                required
                pattern="[0-9]{5}"
                className="input-field"
                placeholder="78701"
              />
            </div>
          </div>

          {/* Date of Birth */}
          <div>
            <label className="label">
              <Calendar className="inline h-4 w-4 mr-1" />
              Date of Birth *
            </label>
            <input
              type="date"
              name="date_of_birth"
              value={formData.date_of_birth}
              onChange={handleChange}
              required
              className="input-field"
            />
          </div>

          {/* Preferences */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Preferred Contact</label>
              <select
                name="preferred_contact"
                value={formData.preferred_contact}
                onChange={handleChange}
                className="input-field"
              >
                <option value="Email">Email</option>
                <option value="Phone">Phone</option>
                <option value="SMS">SMS</option>
              </select>
            </div>
            <div>
              <label className="label">How did you hear about us?</label>
              <select
                name="referral_source"
                value={formData.referral_source}
                onChange={handleChange}
                className="input-field"
              >
                <option value="">Select...</option>
                <option value="Google">Google</option>
                <option value="Facebook">Facebook</option>
                <option value="Friend">Friend/Family</option>
                <option value="Vet">Veterinarian</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          {/* Marketing */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              name="marketing_opt_in"
              checked={formData.marketing_opt_in}
              onChange={handleChange}
              className="h-4 w-4 text-primary-600 rounded"
            />
            <label className="text-sm text-gray-700">
              I'd like to receive promotional emails and offers
            </label>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}
